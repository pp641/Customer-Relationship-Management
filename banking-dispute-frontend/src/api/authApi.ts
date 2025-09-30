import axios from "axios";
import { BASE_URL } from "../Constants/constants";

// Send OTP for signup/signin/forgot-password


export const validatePassword = (pass: string) => {
    return pass.length >= 8;
}
export const SendOtp = async (email: string, authmode: string) => {
  const response = await axios.post(
    `${BASE_URL}/auth/${authmode}/otp`,
    {
      email: email,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};

export const VerifyOtp = async (
  email: string,
  otp: string,
  authmode: string
) => {
  const response = await axios.post(
    `${BASE_URL}/auth/${authmode}/verify-otp`,
    {
      email: email,
      otp: otp,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};

export const SignIn = async (email: string, password: string) => {
  const response = await axios.post(
    `${BASE_URL}/auth/signin`,
    {
      email: email,
      password: password,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};

export const SignUp = async (
  email: string,
  name: string,
  password: string,
  otp: string
) => {
  const response = await axios.post(
    `${BASE_URL}/auth/signup`,
    {
      email: email,
      name: name,
      password: password,
      otp: otp,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};

export const ResetPassword = async (
  email: string,
  newPassword: string,
  otp: string
) => {
  const response = await axios.post(
    `${BASE_URL}/auth/reset-password`,
    {
      email: email,
      new_password: newPassword,
      otp: otp,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};

// Refresh Token
export const RefreshToken = async (refreshToken: string) => {
  const response = await axios.post(
    `${BASE_URL}/auth/refresh-token`,
    {
      refresh_token: refreshToken,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};

// Sign Out / Logout
export const SignOut = async (token: string) => {
  const response = await axios.post(
    `${BASE_URL}/auth/signout`,
    {},
    {
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      timeout: 5000,
    }
  );
  return response.data;
};

export const VerifyToken = async (token: string) => {
  const response = await axios.get(
    `${BASE_URL}/auth/verify-token`,
    {
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      timeout: 5000,
    }
  );
  return response.data;
};

// Get User Profile
export const GetUserProfile = async (token: string) => {
  const response = await axios.get(
    `${BASE_URL}/auth/profile`,
    {
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      timeout: 5000,
    }
  );
  return response.data;
};

// Update User Profile
export const UpdateUserProfile = async (
  token: string,
  userData: {
    name?: string;
    email?: string;
    phone?: string;
    avatar?: string;
  }
) => {
  const response = await axios.put(
    `${BASE_URL}/auth/profile`,
    userData,
    {
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      timeout: 5000,
    }
  );
  return response.data;
};

export const ChangePassword = async (
  token: string,
  currentPassword: string,
  newPassword: string
) => {
  const response = await axios.post(
    `${BASE_URL}/auth/change-password`,
    {
      current_password: currentPassword,
      new_password: newPassword,
    },
    {
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      timeout: 5000,
    }
  );
  return response.data;
};

// Delete Account
export const DeleteAccount = async (token: string, password: string) => {
  const response = await axios.delete(
    `${BASE_URL}/auth/delete-account`,
    {
      data: { password: password },
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      timeout: 5000,
    }
  );
  return response.data;
};

export const CheckEmailExists = async (email: string) => {
  const response = await axios.post(
    `${BASE_URL}/auth/check-email`,
    {
      email: email,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};

// Resend OTP
export const ResendOtp = async (email: string, authmode: string) => {
  const response = await axios.post(
    `${BASE_URL}/auth/${authmode}/resend-otp`,
    {
      email: email,
    },
    {
      headers: { "Content-Type": "application/json" },
      timeout: 5000,
    }
  );
  return response.data;
};