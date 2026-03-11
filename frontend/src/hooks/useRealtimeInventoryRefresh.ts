import { useEffect, useRef } from "react";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

type RefreshInventoryFn = () => Promise<void>;

export function useRealtimeInventoryRefresh(
  homeId: string | undefined,
  refreshInventory: RefreshInventoryFn
) {
  const { inventoryVersionByHome } = useRealtimeContext();
  const firstRunRef = useRef(true);
  const currentVersion = homeId ? (inventoryVersionByHome[homeId] ?? 0) : 0;

  useEffect(() => {
    if (!homeId) return;

    if (firstRunRef.current) {
      firstRunRef.current = false;
      return;
    }

    refreshInventory();
  }, [homeId, currentVersion, refreshInventory]);
}