import { authFetch } from "@/src/api/client";

export type GeneralResponse<T = unknown> = {
  status: "success" | "error";
  message?: string;
  data?: T;
};

// ---------- Request DTOs ----------

export type CreateHomeRequest = {
  name: string;
};

export type JoinHomeRequest = {
  home_code: string;
};

export type AnswerJoinRequestRequest = {
  user_id: string;
  approved: boolean;
};

export type UpdateHomeHeadRequest = {
  new_head_id: string;
};

export type UpdateExpirationRangeRequest = {
  new_range: number;
};

// ---------- Response DTOs ----------

export type HomeDTO = {
  id: string;
  name: string;
  admin_id: string;
  member_ids: string[];
  join_requests: string[];
  expiration_range: number;
};

export type JoinCodeDTO = {
  join_code: string;
};

/**
 * ה-backend מחזיר details בלי schema מפורש כאן,
 * לכן נשאיר טיפוס גמיש.
 */
export type HomeDetailsDTO = Record<string, unknown>;

/**
 * לפי ה-backend:
 * service.get_join_requests(...) מחזיר dict mapping UUID -> Name
 * כלומר בצד ה-frontend זה יהיה אובייקט:
 * {
 *   "user-uuid-1": "Eden",
 *   "user-uuid-2": "Noa"
 * }
 */
export type JoinRequestsDTO = Record<string, string>;

// ---------- API functions ----------

export async function createHome(payload: CreateHomeRequest) {
  return authFetch<GeneralResponse<HomeDTO>>("/homes/create", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getMyHomes() {
  return authFetch<GeneralResponse<HomeDTO[]>>("/homes/my_homes", {
    method: "GET",
  });
}

export async function getHomeJoinCode(homeId: string) {
  return authFetch<GeneralResponse<JoinCodeDTO>>(`/homes/${homeId}/join_code`, {
    method: "GET",
  });
}

export async function joinHomeByCode(payload: JoinHomeRequest) {
  return authFetch<GeneralResponse<null>>("/homes/join", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function answerJoinRequest(
  homeId: string,
  payload: AnswerJoinRequestRequest
) {
  return authFetch<GeneralResponse<HomeDTO>>(
    `/homes/${homeId}/answer_request`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function approveJoinRequest(homeId: string, userId: string) {
  return authFetch<GeneralResponse>(`/homes/${homeId}/answer_request`, {
    method: "POST",
    body: JSON.stringify({
        user_id: userId,
        approved: true
    })
  });
}

export async function rejectJoinRequest(homeId: string, userId: string) {
  return authFetch<GeneralResponse>(`/homes/${homeId}/answer_request`, {
    method: "POST",
    body: JSON.stringify({
        user_id: userId,
        approved: false
    })
  });
}

export async function removeMember(homeId: string, targetUserId: string) {
  return authFetch<GeneralResponse<HomeDTO>>(
    `/homes/${homeId}/members/${targetUserId}`,
    {
      method: "DELETE",
    }
  );
}

export async function leaveHome(homeId: string) {
  return authFetch<GeneralResponse<null>>(`/homes/${homeId}/leave`, {
    method: "POST",
  });
}

export async function switchHomeHead(
  homeId: string,
  payload: UpdateHomeHeadRequest
) {
  return authFetch<GeneralResponse<HomeDTO>>(`/homes/${homeId}/switch_head`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteHome(homeId: string) {
  return authFetch<GeneralResponse<null>>(`/homes/${homeId}`, {
    method: "DELETE",
  });
}

export async function getHomeDetails(homeId: string) {
  return authFetch<GeneralResponse<HomeDetailsDTO>>(
    `/homes/${homeId}/details`,
    {
      method: "GET",
    }
  );
}

export async function updateExpirationRange(
  homeId: string,
  payload: UpdateExpirationRangeRequest
) {
  return authFetch<GeneralResponse<HomeDTO>>(
    `/homes/${homeId}/expiration_range`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    }
  );
}

export async function getJoinRequests(homeId: string) {
  return authFetch<GeneralResponse<JoinRequestsDTO>>(
    `/homes/${homeId}/join_requests`,
    {
      method: "GET",
    }
  );
}