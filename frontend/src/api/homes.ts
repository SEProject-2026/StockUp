import { authFetch } from "@/src/api/client";

export type GeneralResponse<T> = {
  status: "success" | "error";
  message?: string;
  data?: T;
};

export type HomeDTO = {
  id: string;
  name: string;
  membersCount?: number;
  updatedAt?: string;
};

export async function createHome(payload: { name: string }) {
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

export async function joinHomeByCode(payload: { code: string }) {
  return authFetch<GeneralResponse<HomeDTO>>("/homes/join", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
