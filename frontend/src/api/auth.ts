import { authFetch } from "@/src/api/client";
import { supabase } from "@/src/lib/supabase";
import { setSelectedHomeId } from "../utils/selected-home";

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
export async function logout() {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;

    await setSelectedHomeId(null);
    
    console.log("[Auth] Logout successful and storage cleared.");
  } catch (e) {
    console.error("[Auth] Error during logout:", e);
    throw e;
  }
}

export async function updateName(payload: { name: string }) {
  return authFetch<GeneralResponse<UserDTO>>("/auth/update_name", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function changePassword(payload: { new_password: string }) {
  const { error } = await supabase.auth.updateUser({
    password: payload.new_password
  });
  if (error) throw error;
}

export async function updatePushToken(token: string) {
  return authFetch<GeneralResponse>("/auth/me/push-token", {
    method: "PATCH",
    body: JSON.stringify({ push_token: token }),
  });
}
