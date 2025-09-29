from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
import redis
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
import random
from database import Database
from models import UsersDB
from dependencies import get_database, get_logger, get_redis_client

logger = get_logger

# JWT settings
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

async def generate_and_store_otp(email: str, expire_minutes: int, redis_client: redis.Redis) -> str:
    otp = f"{random.randint(100000, 999999)}"
    if not redis_client:
        logger().warning("Redis client not available, falling back to temp storage")
        temp_otp_storage[email] = otp
    else:
         redis_client.set(f"otp:{email}", otp, ex=expire_minutes * 60)
    return otp

async def verify_otp(email: str, otp: str, redis_client: redis.Redis) -> bool:
    if not redis_client:
        stored_otp = temp_otp_storage.get(email)
        if stored_otp and stored_otp == otp:
            temp_otp_storage.pop(email, None) 
            return True
        return False
    else:
        stored_otp =  redis_client.get(f"otp:{email}")
        if stored_otp and stored_otp == otp:
            redis_client.delete(f"otp:{email}")  
            return True
        return False

temp_otp_storage = {
}  



# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str



class TokenData(BaseModel):
    username: str | None = None



class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None



class UserInDB(User):
    hashed_password: str



class SignInRequest(BaseModel):
    email: str
    password: str



class SignUpRequest(BaseModel):
    email: str
    name: str
    password: str
    otp: str



class OtpRequest(BaseModel):
    email: str



class VerifyOtpRequest(BaseModel):
    email: str
    otp: str



class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    otp: str



class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str



class UpdateProfileRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None



class DeleteAccountRequest(BaseModel):
    password: str



class CheckEmailRequest(BaseModel):
    email: str



# Response models
class AuthResponse(BaseModel):
    success: bool
    message: str
    user: User | None = None
    access_token: str | None = None



class OtpResponse(BaseModel):
    success: bool
    message: str



class VerifyResponse(BaseModel):
    success: bool
    message: str


# Security utils
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Router
router = APIRouter(prefix="/auth", tags=["auth"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_email(email: str, db: Database):
    return db.get_user_by_email(email)

def get_user_by_username(username: str, db: Database):
    return db.get_user_by_username(username)

def authenticate_user(email: str, password: str, db: Database):
    logger().info(f"Authenticating user with email: {email}")
    user = db.get_user_by_email(email=email)
    if not user:
        logger().warning(f"User not found for email: {email}")
        return False
    if not verify_password(password, user.get('hashed_password')):
        logger().warning(f"Invalid password for email: {email}")
        return False
    logger().info(f"User authenticated successfully: {email}")
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Database = Depends(get_database),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        logger().warning("Invalid token provided")
        raise credentials_exception
    
    user = get_user_by_username(token_data.username, db)
    if user is None:
        logger().warning(f"User not found for username: {token_data.username}")
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[dict, Depends(get_current_user)],
):
    if current_user.get('disabled', False):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@router.post("/signin", response_model=AuthResponse)
async def sign_in(
    payload: SignInRequest,
    db: Database = Depends(get_database),
):
    logger().info(f"Sign in attempt for email: {payload.email}")
    
    user = authenticate_user(payload.email, payload.password, db)
    if not user:
        logger().warning(f"Failed sign in attempt for email: {payload.email}")
        return AuthResponse(
            success=False,
            message="Invalid email or password",
            user=None,
            access_token=None
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    
    logger().info(f"User signed in successfully: {payload.email}")
    return AuthResponse(
        success=True,
        message="Successfully signed in",
        user=User(
            username=user['email'],
            email=user['email'],
            full_name=user['full_name'],
            disabled=user.get('disabled', False)
        ),
        access_token=access_token
    )

@router.post("/signup", response_model=AuthResponse)
async def sign_up(
    payload: SignUpRequest,
    db: Database = Depends(get_database),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    if db.get_user_by_email(payload.email):
        logger().warning(f"User already exists for email: {payload.email}")
        return AuthResponse(
            success=False,
            message="User with this email already exists",
            user=None,
            access_token=None
        )
    
    logger().info(f"Sign up attempt for email: {payload.email}")
    otp_valid = await verify_otp(payload.email, payload.otp, redis_client)
    if not otp_valid:
        logger().warning(f"Invalid OTP for email: {payload.email}")
        return AuthResponse(
            success=False,
            message="Invalid or expired OTP",
            user=None,
            access_token=None
        )
    
    hashed_password = get_password_hash(payload.password)
    new_user: UsersDB = {
        "full_name": payload.name,
        "email": payload.email,
        "hashed_password": hashed_password,
        "active": True,
        "role": "user",
    }
    
    db.save_user(new_user)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": payload.email}, expires_delta=access_token_expires
    )
    
    logger().info(f"User registered successfully: {payload.email}")
    return AuthResponse(
        success=True,
        message="Account created successfully",
        user=User(
            username=payload.email,
            email=payload.email,
            full_name=payload.name,
            disabled=False
        ),
        access_token=access_token
    )

@router.post("/signup/otp", response_model=OtpResponse) 
async def send_signup_otp(
    payload: OtpRequest,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    logger().info(f"Sending signup OTP to: {payload.email}")
    otp = await generate_and_store_otp(payload.email, 5, redis_client)
    logger().info(f"OTP sent to {payload.email}: {otp}")
    return OtpResponse(
        success=True,
        message="OTP sent to your email address"
    )

@router.post("/signin/otp", response_model=OtpResponse)
async def send_signin_otp(
    payload: OtpRequest,
    db: Database = Depends(get_database),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Send OTP for signin"""
    logger().info(f"Sending signin OTP to: {payload.email}")
    
    user = get_user_by_email(payload.email, db)
    if not user:
        logger().warning(f"No user found for email: {payload.email}")
        return OtpResponse(
            success=False,
            message="No account found with this email address"
        )
    
    otp = await generate_and_store_otp(payload.email, 5, redis_client)
    
    logger().info(f"OTP sent to {payload.email}: {otp}")
    
    return OtpResponse(
        success=True,
        message="OTP sent to your email address"
    )

@router.post("/forgot-password/otp", response_model=OtpResponse)
async def send_forgot_password_otp(
    payload: OtpRequest,
    db: Database = Depends(get_database),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Send OTP for password reset"""
    logger().info(f"Sending forgot password OTP to: {payload.email}")
    
    user = get_user_by_email(payload.email, db)
    if not user:
        logger().warning(f"No user found for email: {payload.email}")
        return OtpResponse(
            success=False,
            message="No account found with this email address"
        )
    
    otp = await generate_and_store_otp(payload.email, 5, redis_client)
    
    # TODO: Replace with actual email sending logic
    logger().info(f"Password reset OTP sent to {payload.email}: {otp}")
    
    return OtpResponse(
        success=True,
        message="Password reset OTP sent to your email address"
    )

@router.post("/signup/verify-otp", response_model=VerifyResponse)
async def verify_signup_otp(
    payload: VerifyOtpRequest,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Verify OTP for signup"""
    logger().info(f"Verifying signup OTP for: {payload.email}")
    
    otp_valid = await verify_otp(payload.email, payload.otp, redis_client)
    
    if not otp_valid:
        logger().warning(f"Invalid OTP for email: {payload.email}")
        return VerifyResponse(
            success=False,
            message="Invalid or expired OTP"
        )
    
    logger().info(f"OTP verified successfully for: {payload.email}")
    return VerifyResponse(
        success=True,
        message="OTP verified successfully"
    )

@router.post("/signin/verify-otp", response_model=VerifyResponse)
async def verify_signin_otp(
    payload: VerifyOtpRequest,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Verify OTP for signin"""
    logger().info(f"Verifying signin OTP for: {payload.email}")
    
    otp_valid = await verify_otp(payload.email, payload.otp, redis_client)
    
    if not otp_valid:
        logger().warning(f"Invalid OTP for email: {payload.email}")
        return VerifyResponse(
            success=False,
            message="Invalid or expired OTP"
        )
    
    logger().info(f"Signin OTP verified successfully for: {payload.email}")
    return VerifyResponse(
        success=True,
        message="OTP verified successfully"
    )

@router.post("/forgot-password/verify-otp", response_model=VerifyResponse)
async def verify_forgot_password_otp(
    payload: VerifyOtpRequest,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Verify OTP for password reset"""
    logger().info(f"Verifying forgot password OTP for: {payload.email}")
    
    otp_valid = await verify_otp(payload.email, payload.otp, redis_client)
    
    if not otp_valid:
        logger().warning(f"Invalid OTP for email: {payload.email}")
        return VerifyResponse(
            success=False,
            message="Invalid or expired OTP"
        )
    
    logger().info(f"Password reset OTP verified successfully for: {payload.email}")
    return VerifyResponse(
        success=True,
        message="OTP verified successfully"
    )

@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(
    payload: ResetPasswordRequest,
    db: Database = Depends(get_database),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Reset password using OTP"""
    logger().info(f"Password reset attempt for: {payload.email}")
    
    otp_valid = await verify_otp(payload.email, payload.otp, redis_client)
    if not otp_valid:
        logger().warning(f"Invalid OTP for password reset: {payload.email}")
        return AuthResponse(
            success=False,
            message="Invalid or expired OTP",
            user=None,
            access_token=None
        )
    
    user = get_user_by_email(payload.email, db)
    if not user:
        logger().warning(f"User not found for password reset: {payload.email}")
        return AuthResponse(
            success=False,
            message="User not found",
            user=None,
            access_token=None
        )
    
    hashed_password = get_password_hash(payload.new_password)
    db.update_user_password(payload.email, hashed_password)
    
    logger().info(f"Password reset successfully for: {payload.email}")
    return AuthResponse(
        success=True,
        message="Password reset successfully",
        user=None,
        access_token=None
    )

@router.post("/signup/resend-otp", response_model=OtpResponse)
async def resend_signup_otp(
    payload: OtpRequest,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Resend OTP for signup"""
    logger().info(f"Resending signup OTP to: {payload.email}")
    
    otp = await generate_and_store_otp(payload.email, 5, redis_client)
    
    return OtpResponse(
        success=True,
        message="OTP resent to your email address"
    )

@router.post("/signin/resend-otp", response_model=OtpResponse)
async def resend_signin_otp(
    payload: OtpRequest,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Resend OTP for signin"""
    logger().info(f"Resending signin OTP to: {payload.email}")
    
    otp = await generate_and_store_otp(payload.email, 5, redis_client)
    
    return OtpResponse(
        success=True,
        message="OTP resent to your email address"
    )

@router.post("/forgot-password/resend-otp", response_model=OtpResponse)
async def resend_forgot_password_otp(
    payload: OtpRequest,
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """Resend OTP for password reset"""
    logger().info(f"Resending forgot password OTP to: {payload.email}")
    
    otp = await generate_and_store_otp(payload.email, 5, redis_client)
    
    return OtpResponse(
        success=True,
        message="OTP resent to your email address"
    )

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Database = Depends(get_database),
):
    """OAuth2 compatible token login"""
    logger().info(f"Token login attempt for: {form_data.username}")
    
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        logger().warning(f"Failed token login for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['email']}, expires_delta=access_token_expires
    )
    
    logger().info(f"Token generated successfully for: {form_data.username}")
    return Token(access_token=access_token, token_type="bearer")

# ... (Rest of the endpoints remain the same, just remove the unused redis parameters) ...


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: Annotated[dict, Depends(get_current_active_user)],

):
    """Refresh access token"""
    logger().info(f"Token refresh for user: {current_user['email']}")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user['email']}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/signout")
async def sign_out(
    current_user: Annotated[dict, Depends(get_current_active_user)],

):
    """Sign out user"""
    logger().info(f"User signed out: {current_user['email']}")
    return {"success": True, "message": "Successfully signed out"}


@router.get("/verify-token")
async def verify_token(
    current_user: Annotated[dict, Depends(get_current_active_user)],

):
    """Verify if token is valid"""
    logger().info(f"Token verification for user: {current_user['email']}")
    return {
        "success": True,
        "message": "Token is valid",
        "user": User(
            username=current_user['email'],
            email=current_user['email'],
            full_name=current_user['full_name'],
            disabled=current_user.get('disabled', False)
        )
    }


@router.get("/profile", response_model=User)
async def get_user_profile(
    current_user: Annotated[dict, Depends(get_current_active_user)],

):
    """Get user profile"""
    logger().info(f"Profile request for user: {current_user['email']}")
    return User(
        username=current_user['email'],
        email=current_user['email'],
        full_name=current_user['full_name'],
        disabled=current_user.get('disabled', False)
    )


@router.put("/profile")
async def update_user_profile(
    payload: UpdateProfileRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
    db: Database = Depends(get_database),

):
    """Update user profile"""
    logger().info(f"Profile update for user: {current_user['email']}")
    
    update_data = {}
    if payload.name:
        update_data['full_name'] = payload.name
    if payload.email:
        update_data['email'] = payload.email
    if payload.phone:
        update_data['phone'] = payload.phone
    if payload.avatar:
        update_data['avatar'] = payload.avatar
    
    if update_data:
        db.update_user_profile(current_user['email'], update_data)
        logger().info(f"Profile updated successfully for user: {current_user['email']}")
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "user": User(
            username=current_user['email'],
            email=payload.email or current_user['email'],
            full_name=payload.name or current_user['full_name'],
            disabled=current_user.get('disabled', False)
        )
    }


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
    db: Database = Depends(get_database),

):
    """Change password for authenticated users"""
    logger().info(f"Password change request for user: {current_user['email']}")
    
    if not verify_password(payload.current_password, current_user['hashed_password']):
        logger().warning(f"Invalid current password for user: {current_user['email']}")
        return {"success": False, "message": "Current password is incorrect"}
    
    hashed_password = get_password_hash(payload.new_password)
    db.update_user_password(current_user['email'], hashed_password)
    
    logger().info(f"Password changed successfully for user: {current_user['email']}")
    return {"success": True, "message": "Password changed successfully"}


@router.delete("/delete-account")
async def delete_account(
    payload: DeleteAccountRequest,
    current_user: Annotated[dict, Depends(get_current_active_user)],
    db: Database = Depends(get_database),

):
    """Delete user account"""
    logger().info(f"Account deletion request for user: {current_user['email']}")
    
    if not verify_password(payload.password, current_user['hashed_password']):
        logger().warning(f"Invalid password for account deletion: {current_user['email']}")
        return {"success": False, "message": "Password is incorrect"}
    
    db.delete_user(current_user['email'])
    
    logger().info(f"Account deleted successfully for user: {current_user['email']}")
    return {"success": True, "message": "Account deleted successfully"}


# Utility Routes
@router.post("/check-email")
async def check_email_exists(
    payload: CheckEmailRequest,
    db: Database = Depends(get_database),

):
    """Check if email exists"""
    logger().info(f"Email check for: {payload.email}")
    
    user = get_user_by_email(payload.email, db)
    exists = user is not None
    
    return {
        "success": True,
        "exists": exists,
        "message": "Email exists" if exists else "Email not found"
    }


# Legacy routes for backward compatibility
@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[dict, Depends(get_current_active_user)],
):
    """Get current user (legacy route)"""
    return User(
        username=current_user['email'],
        email=current_user['email'],
        full_name=current_user['full_name'],
        disabled=current_user.get('disabled', False)
    )


@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[dict, Depends(get_current_active_user)],
):
    """Get user items (legacy route)"""
    return [{"item_id": "Foo", "owner": current_user['email']}]