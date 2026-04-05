import { authFetch, apiFetch} from "@/src/api/client";
import { supabase } from "@/src/config/supabase";
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
export type RegisterRequest = {
  user_id: string;
  email: string;
  name: string;
};

export async function registerBackend(
  userData: { user_id: string; email: string; name: string }, 
  manualToken?: string // הסימן ? הופך אותו לאופציונלי
) {
  // אם קיבלנו טוקן ידנית, נשתמש ב-apiFetch רגיל ונזריק את הטוקן ל-Headers
  if (manualToken) {
    return apiFetch("/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
      headers: {
        Authorization: `Bearer ${manualToken}`,
      },
    });
  }

  // ברירת מחדל: שימוש ב-authFetch שמושך את הטוקן מהסשן הגלובלי
  return authFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify(userData),
  });
}

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
