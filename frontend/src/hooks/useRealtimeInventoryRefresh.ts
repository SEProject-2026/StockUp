import { useEffect, useRef } from "react";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

export function useRealtimeInventoryRefresh(
  homeId: string | undefined,
  refreshInventory: () => Promise<void>
) {
  const { inventoryVersionByHome } = useRealtimeContext();
  const firstRunRef = useRef(true);

  const currentVersion = homeId
    ? (inventoryVersionByHome[homeId] ?? 0)
    : 0;

  useEffect(() => {
    if (!homeId) return;

    console.log("[InventoryRefresh] homeId:", homeId, "version:", currentVersion);

    if (firstRunRef.current) {
      firstRunRef.current = false;
      return;
    }

    refreshInventory();
  }, [homeId, currentVersion, refreshInventory]);
}