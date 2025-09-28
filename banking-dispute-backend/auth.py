from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import APIRouter, Depends, FastAPI, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

# JWT settings
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fake DB
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

# In-memory storage for demonstration
temp_otp_storage = {}  # {email: otp}
temp_user_signup_data = {}  # {email: {name, password, otp}}

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

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def get_user_by_email(email: str):
    for username, user_data in fake_users_db.items():
        if user_data["email"] == email:
            return UserInDB(**user_data)
    return None

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
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
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/signin", response_model=AuthResponse)
async def sign_in(payload: SignInRequest):
    """Sign in with email and password"""
    # Find user by email
    user = get_user_by_email(payload.email)
    if not user:
        return AuthResponse(
            success=False,
            message="Invalid email or password",
            user=None,
            access_token=None
        )
    
    if not verify_password(payload.password, user.hashed_password):
        return AuthResponse(
            success=False,
            message="Invalid email or password", 
            user=None,
            access_token=None
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        success=True,
        message="Successfully signed in",
        user=User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled
        ),
        access_token=access_token
    )

@router.post("/signup", response_model=AuthResponse)
async def sign_up(payload: SignUpRequest):
    """Sign up with email, name, password, and OTP verification"""
    # Check if OTP is valid
    stored_otp = temp_otp_storage.get(payload.email)
    if not stored_otp or stored_otp != payload.otp:
        return AuthResponse(
            success=False,
            message="Invalid or expired OTP",
            user=None,
            access_token=None
        )
    
    if get_user_by_email(payload.email):
        return AuthResponse(
            success=False,
            message="User with this email already exists",
            user=None,
            access_token=None
        )
    
    username = payload.email.split("@")[0]  
    hashed_password = get_password_hash(payload.password)
    
    fake_users_db[username] = {
        "username": username,
        "full_name": payload.name,
        "email": payload.email,
        "hashed_password": hashed_password,
        "disabled": False,
    }
    
    temp_otp_storage.pop(payload.email, None)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    return AuthResponse(
        success=True,
        message="Account created successfully",
        user=User(
            username=username,
            email=payload.email,
            full_name=payload.name,
            disabled=False
        ),
        access_token=access_token
    )

# OTP Routes

@router.post("/signup/otp", response_model=OtpResponse)
async def send_signup_otp(payload: OtpRequest):
    """Send OTP for signup"""
    hardcoded_otp = "123456"
    temp_otp_storage[payload.email] = hardcoded_otp
    
    return OtpResponse(
        success=True,
        message="OTP sent to your email address"
    )

@router.post("/signin/otp", response_model=OtpResponse)  
async def send_signin_otp(payload: OtpRequest):
    hardcoded_otp = "123456"
    user = get_user_by_email(payload.email)
    if not user:
        return OtpResponse(
            success=False,
            message="No account found with this email address"
        )
    
    temp_otp_storage[payload.email] = hardcoded_otp
    
    return OtpResponse(
        success=True,
        message="OTP sent to your email address"
    )

@router.post("/forgot-password/otp", response_model=OtpResponse)
async def send_forgot_password_otp(payload: OtpRequest):
    hardcoded_otp = "123456"
    
    # Check if user exists
    user = get_user_by_email(payload.email)
    if not user:
        return OtpResponse(
            success=False,
            message="No account found with this email address"
        )
    
    temp_otp_storage[payload.email] = hardcoded_otp
    
    return OtpResponse(
        success=True,
        message="Password reset OTP sent to your email address"
    )


@router.post("/signup/verify-otp", response_model=VerifyResponse)
async def verify_signup_otp(payload: VerifyOtpRequest):
    stored_otp = temp_otp_storage.get(payload.email)
    
    if not stored_otp or stored_otp != payload.otp:
        return VerifyResponse(
            success=False,
            message="Invalid or expired OTP"
        )
    
    return VerifyResponse(
        success=True,
        message="OTP verified successfully"
    )

@router.post("/signin/verify-otp", response_model=VerifyResponse)
async def verify_signin_otp(payload: VerifyOtpRequest):
    stored_otp = temp_otp_storage.get(payload.email)
    
    if not stored_otp or stored_otp != payload.otp:
        return VerifyResponse(
            success=False,
            message="Invalid or expired OTP"
        )
    
    return VerifyResponse(
        success=True,
        message="OTP verified successfully"
    )

@router.post("/forgot-password/verify-otp", response_model=VerifyResponse)
async def verify_forgot_password_otp(payload: VerifyOtpRequest):
    stored_otp = temp_otp_storage.get(payload.email)
    
    if not stored_otp or stored_otp != payload.otp:
        return VerifyResponse(
            success=False,
            message="Invalid or expired OTP"
        )
    
    return VerifyResponse(
        success=True,
        message="OTP verified successfully"
    )


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(payload: ResetPasswordRequest):
    stored_otp = temp_otp_storage.get(payload.email)
    if not stored_otp or stored_otp != payload.otp:
        return AuthResponse(
            success=False,
            message="Invalid or expired OTP",
            user=None,
            access_token=None
        )
    
    user = get_user_by_email(payload.email)
    if not user:
        return AuthResponse(
            success=False,
            message="User not found",
            user=None,
            access_token=None
        )
    
    hashed_password = get_password_hash(payload.new_password)
    fake_users_db[user.username]["hashed_password"] = hashed_password
    
    temp_otp_storage.pop(payload.email, None)
    
    return AuthResponse(
        success=True,
        message="Password reset successfully",
        user=None,
        access_token=None
    )


@router.post("/signup/resend-otp", response_model=OtpResponse)
async def resend_signup_otp(payload: OtpRequest):
    hardcoded_otp = "123456"
    temp_otp_storage[payload.email] = hardcoded_otp
    
    return OtpResponse(
        success=True,
        message="OTP resent to your email address"
    )

@router.post("/signin/resend-otp", response_model=OtpResponse)
async def resend_signin_otp(payload: OtpRequest):
    hardcoded_otp = "123456"
    temp_otp_storage[payload.email] = hardcoded_otp
    
    return OtpResponse(
        success=True,
        message="OTP resent to your email address"
    )

@router.post("/forgot-password/resend-otp", response_model=OtpResponse)
async def resend_forgot_password_otp(payload: OtpRequest):
    hardcoded_otp = "123456"
    temp_otp_storage[payload.email] = hardcoded_otp
    
    return OtpResponse(
        success=True,
        message="OTP resent to your email address"
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """OAuth2 compatible token login"""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/refresh-token", response_model=Token)
async def refresh_token(current_user: Annotated[User, Depends(get_current_active_user)]):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.post("/signout")
async def sign_out(current_user: Annotated[User, Depends(get_current_active_user)]):
    return {"success": True, "message": "Successfully signed out"}

@router.get("/verify-token")
async def verify_token(current_user: Annotated[User, Depends(get_current_active_user)]):
    """Verify if token is valid"""
    return {
        "success": True, 
        "message": "Token is valid",
        "user": current_user
    }


@router.get("/profile", response_model=User)
async def get_user_profile(current_user: Annotated[User, Depends(get_current_active_user)]):
    """Get user profile"""
    return current_user

@router.put("/profile")
async def update_user_profile(
    payload: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Update user profile"""
    user_data = fake_users_db[current_user.username]
    
    if payload.name:
        user_data["full_name"] = payload.name
    if payload.email:
        user_data["email"] = payload.email
    
    return {
        "success": True,
        "message": "Profile updated successfully",
        "user": User(**user_data)
    }

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Change password for authenticated users"""
    user_data = fake_users_db[current_user.username]
    
    if not verify_password(payload.current_password, user_data["hashed_password"]):
        return {"success": False, "message": "Current password is incorrect"}
    
    user_data["hashed_password"] = get_password_hash(payload.new_password)
    
    return {"success": True, "message": "Password changed successfully"}

@router.delete("/delete-account")
async def delete_account(
    payload: DeleteAccountRequest,
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    user_data = fake_users_db[current_user.username]
    
    if not verify_password(payload.password, user_data["hashed_password"]):
        return {"success": False, "message": "Password is incorrect"}
    
    fake_users_db.pop(current_user.username, None)
    
    return {"success": True, "message": "Account deleted successfully"}

# Utility Routes

@router.post("/check-email")
async def check_email_exists(payload: CheckEmailRequest):
    """Check if email exists"""
    user = get_user_by_email(payload.email)
    return {
        "success": True,
        "exists": user is not None,
        "message": "Email exists" if user else "Email not found"
    }

# Legacy routes for backward compatibility
@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current user (legacy route)"""
    return current_user

@router.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get user items (legacy route)"""
    return [{"item_id": "Foo", "owner": current_user.username}]