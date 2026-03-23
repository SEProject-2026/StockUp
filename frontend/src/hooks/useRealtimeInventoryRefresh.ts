import { useEffect, useRef } from "react";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

export function useRealtimeInventoryRefresh(
  homeId: string | undefined,
  refreshInventory: () => Promise<void>
) {
  const { inventoryVersionByHome } = useRealtimeContext();
  const firstRunRef = useRef(true);
  const lastVersionRef = useRef<number>(0);

  const currentVersion = homeId ? (inventoryVersionByHome[homeId] ?? 0) : 0;

  useEffect(() => {
    if (!homeId) return;

    // הגנה נוספת: בדקי אם הגרסה באמת השתנתה מאז הפעם האחרונה
    if (currentVersion === lastVersionRef.current) return;
    
    if (firstRunRef.current) {
      firstRunRef.current = false;
      lastVersionRef.current = currentVersion;
      return;
    }

    console.log("[InventoryRefresh] Triggering refresh for version:", currentVersion);
    lastVersionRef.current = currentVersion;
    void refreshInventory();
  }, [homeId, currentVersion, refreshInventory]); // refreshInventory חייבת להיות יציבה!
}