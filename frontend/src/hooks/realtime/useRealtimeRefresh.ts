import { useEffect, useRef } from "react";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

// --- Homes Refresh ---
type LoadHomesFn = (mode?: "initial" | "refresh") => Promise<void>;

export function useRealtimeHomesRefresh(loadHomes: LoadHomesFn) {
  const { homesVersion } = useRealtimeContext();

  useEffect(() => {
    loadHomes("refresh");
  }, [homesVersion, loadHomes]);
}

// --- Inventory Refresh ---
export function useRealtimeInventoryRefresh(
  homeId: string | undefined,
  refreshInventory: () => Promise<void>
) {
  const { inventoryVersionByHome } = useRealtimeContext();
  const lastVersionRef = useRef<number>(0);

  const currentVersion = homeId ? (inventoryVersionByHome[homeId] ?? 0) : 0;

  useEffect(() => {
    if (!homeId) return;

    // הגנה נוספת: בדקי אם הגרסה באמת השתנתה מאז הפעם האחרונה
    if (currentVersion === lastVersionRef.current) return;
    
    console.log("[InventoryRefresh] Triggering refresh for version:", currentVersion);
    lastVersionRef.current = currentVersion;
    void refreshInventory();
  }, [homeId, currentVersion, refreshInventory]);
}

// --- Join Requests Refresh ---
export function useRealtimeJoinRequestsRefresh(
  homeId: string | undefined,
  refreshJoinRequests: () => Promise<void>,
  enabled: boolean = true
) {
  const { joinRequestsVersionByHome } = useRealtimeContext();
  
  const lastHomeIdRef = useRef<string | undefined>(undefined);
  const lastVersionRef = useRef<number>(-1);
  const refreshRef = useRef(refreshJoinRequests);

  useEffect(() => {
    refreshRef.current = refreshJoinRequests;
  }, [refreshJoinRequests]);

  const currentVersion = homeId ? (joinRequestsVersionByHome[homeId] ?? 0) : 0;

  useEffect(() => {
    if (!homeId || !enabled || (homeId === lastHomeIdRef.current && currentVersion <= lastVersionRef.current)) {
      return;
    }

    if (lastVersionRef.current === -1 && currentVersion === 0) {
      lastHomeIdRef.current = homeId;
      lastVersionRef.current = 0;
      return;
    }

    console.log("[JoinRequestsRefresh] TRIGGERED", { homeId, currentVersion });

    lastHomeIdRef.current = homeId;
    lastVersionRef.current = currentVersion;

    void refreshRef.current();
  }, [homeId, currentVersion]);
}
