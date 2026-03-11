import { apiFetch, authFetch } from "@/src/api/client";
import {
  setAccessToken,
  clearAccessToken,
  setCurrentUserId,
  clearCurrentUserId,
  getCurrentUserId,
} from "@/src/auth/token";
const userId = await getCurrentUserId();

export type GeneralResponse<T = any> = {
  status: "success" | "error";
  message: string;
  data?: T;
};

export type UserDTO = {
  id?: string;
  email: string;
  name?: string;
};

export type LoginResponse = {
  status: "success" | "error";
  access_token: string;
  data: UserDTO;
};

export async function register(payload: {
  email: string;
  password: string;
  password_confirm: string;
  name: string;
}) {
  return apiFetch<GeneralResponse<UserDTO>>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(payload: { email: string; password: string }) {
  const res = await apiFetch<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (res.access_token) {
    await setAccessToken(res.access_token);
  }

  if (res.data?.id) {
    await setCurrentUserId(res.data.id);
  }

  return res;
}

export async function logout() {
  await clearAccessToken();
  await clearCurrentUserId();
}

export async function updateName(payload: { name: string }) {
  return authFetch<GeneralResponse<UserDTO>>("/auth/update_name", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: {
  current_password: string;
  new_password: string;
}) {
  return authFetch<GeneralResponse>("/auth/password", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
