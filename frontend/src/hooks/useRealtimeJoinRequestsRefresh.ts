import { useEffect, useRef } from "react";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

export function useRealtimeJoinRequestsRefresh(
  homeId: string | undefined,
  refreshJoinRequests: () => Promise<void>
) {
  const { joinRequestsVersionByHome } = useRealtimeContext();
  
  // Ref-ים לשמירת המצב הקודם
  const lastHomeIdRef = useRef<string | undefined>(undefined);
  const lastVersionRef = useRef<number>(-1);
  const refreshRef = useRef(refreshJoinRequests);

  // תמיד מעדכנים את הפונקציה ב-Ref
  useEffect(() => {
    refreshRef.current = refreshJoinRequests;
  }, [refreshJoinRequests]);

  const currentVersion = homeId ? (joinRequestsVersionByHome[homeId] ?? 0) : 0;

  useEffect(() => {
    // 1. הגנה: אם אין homeId, או שה-homeId והגרסה זהים למה שכבר עיבדנו - עצור מיד
    if (!homeId || (homeId === lastHomeIdRef.current && currentVersion <= lastVersionRef.current)) {
      return;
    }

    // 2. טיפול במצב טעינה ראשוני (גרסה 0) - מעדכנים Ref בלי להריץ ריענון
    if (lastVersionRef.current === -1 && currentVersion === 0) {
      lastHomeIdRef.current = homeId;
      lastVersionRef.current = 0;
      return;
    }

    // 3. ריענון אמיתי - קורה רק אם ה-ID השתנה או שהגרסה עלתה
    console.log("[JoinRequestsRefresh] TRIGGERED", { homeId, currentVersion });

    lastHomeIdRef.current = homeId;
    lastVersionRef.current = currentVersion;

    void refreshRef.current();

  }, [homeId, currentVersion]); // Dependencies מינימליים
}