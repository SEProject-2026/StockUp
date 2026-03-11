import { useEffect, useRef } from "react";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

export function useRealtimeJoinRequestsRefresh(
  homeId: string | undefined,
  refreshJoinRequests: () => Promise<void>
) {
  const { joinRequestsVersionByHome } = useRealtimeContext();
  const firstRunRef = useRef(true);

  const currentVersion = homeId
    ? (joinRequestsVersionByHome[homeId] ?? 0)
    : 0;

  useEffect(() => {
    if (!homeId) return;

    console.log("[JoinRequestsRefresh] homeId:", homeId, "version:", currentVersion);

    if (firstRunRef.current) {
      firstRunRef.current = false;
      return;
    }

    refreshJoinRequests();
  }, [homeId, currentVersion, refreshJoinRequests]);
}