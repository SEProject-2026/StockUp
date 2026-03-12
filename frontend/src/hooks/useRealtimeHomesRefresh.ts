import { useEffect, useRef } from "react";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

type LoadHomesFn = (mode?: "initial" | "refresh") => Promise<void>;

export function useRealtimeHomesRefresh(loadHomes: LoadHomesFn) {
  const { homesVersion } = useRealtimeContext();
  const firstRunRef = useRef(true);

  useEffect(() => {
    if (firstRunRef.current) {
      firstRunRef.current = false;
      return;
    }

    loadHomes("refresh");
  }, [homesVersion, loadHomes]);
}