import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { supabase } from "@/src/lib/supabase";

type RealtimeContextValue = {
  homesVersion: number;
  inventoryVersionByHome: Record<string, number>;
  bumpInventoryVersion: (homeId: string) => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [homesVersion, setHomesVersion] = useState(0);
  const [inventoryVersionByHome, setInventoryVersionByHome] = useState<Record<string, number>>({});

  const channelsRef = useRef<any[]>([]);

  const bumpHomesVersion = useCallback(() => {
    setHomesVersion((prev) => prev + 1);
  }, []);

  const bumpInventoryVersion = useCallback((homeId: string) => {
    if (!homeId) return;

    setInventoryVersionByHome((prev) => ({
      ...prev,
      [homeId]: (prev[homeId] ?? 0) + 1,
    }));
  }, []);

  useEffect(() => {
    let mounted = true;

    const setup = async () => {
      try {
        const { data } = await supabase.auth.getUser();

        const userId = data?.user?.id;

        console.log("[Realtime] supabase user:", userId);

        if (!userId) return;

        const userHomeChannel = supabase
          .channel(`rt-user-home-${userId}`)
          .on(
            "postgres_changes",
            {
              event: "*",
              schema: "public",
              table: "user_home",
              filter: `user_id=eq.${userId}`,
            },
            (payload) => {
              console.log("[Realtime] user_home payload:", payload);
              bumpHomesVersion();
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] user_home status:", status);
          });

        const homesChannel = supabase
          .channel(`rt-homes-${userId}`)
          .on(
            "postgres_changes",
            {
              event: "*",
              schema: "public",
              table: "homes",
            },
            (payload) => {
              console.log("[Realtime] homes payload:", payload);
              bumpHomesVersion();
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] homes status:", status);
          });

        const productItemsChannel = supabase
          .channel(`rt-product-items-${userId}`)
          .on(
            "postgres_changes",
            {
              event: "*",
              schema: "public",
              table: "product_items",
            },
            (payload) => {
              console.log("[Realtime] product_items payload:", payload);

              const next = payload.new as { home_id?: string } | null;
              const oldRow = payload.old as { home_id?: string } | null;
              const changedHomeId = next?.home_id ?? oldRow?.home_id;

              if (changedHomeId) {
                bumpInventoryVersion(changedHomeId);
              }
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] product_items status:", status);
          });

        channelsRef.current = [userHomeChannel, homesChannel, productItemsChannel];
      } catch (error) {
        console.log("[Realtime] setup error:", error);
      }
    };

    setup();

    return () => {
      mounted = false;

      channelsRef.current.forEach((channel) => {
        try {
          supabase.removeChannel(channel);
        } catch (error) {
          console.log("[Realtime] remove channel error:", error);
        }
      });

      channelsRef.current = [];
    };
  }, [bumpHomesVersion, bumpInventoryVersion]);

  const value = useMemo(
    () => ({
      homesVersion,
      inventoryVersionByHome,
      bumpInventoryVersion,
    }),
    [homesVersion, inventoryVersionByHome, bumpInventoryVersion]
  );

  return <RealtimeContext.Provider value={value}>{children}</RealtimeContext.Provider>;
}

export function useRealtimeContext() {
  const ctx = useContext(RealtimeContext);

  if (!ctx) {
    throw new Error("useRealtimeContext must be used inside RealtimeProvider");
  }

  return ctx;
}