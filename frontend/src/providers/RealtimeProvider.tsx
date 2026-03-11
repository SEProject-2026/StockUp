import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { supabase } from "@/src/lib/supabase";
import { getCurrentUserId } from "@/src/auth/token";

type RealtimeContextValue = {
  homesVersion: number;
  inventoryVersionByHome: Record<string, number>;
  joinRequestsVersionByHome: Record<string, number>;
  bumpInventoryVersion: (homeId: string) => void;
  bumpJoinRequestsVersion: (homeId: string) => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const [homesVersion, setHomesVersion] = useState(0);
  const [inventoryVersionByHome, setInventoryVersionByHome] = useState<Record<string, number>>({});
  const [joinRequestsVersionByHome, setJoinRequestsVersionByHome] = useState<Record<string, number>>({});

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

  const bumpJoinRequestsVersion = useCallback((homeId: string) => {
    if (!homeId) return;
    setJoinRequestsVersionByHome((prev) => ({
      ...prev,
      [homeId]: (prev[homeId] ?? 0) + 1,
    }));
  }, []);

  useEffect(() => {
    let mounted = true;

    const setup = async () => {
      try {
        const userId = await getCurrentUserId();

        console.log("[Realtime] stored userId:", userId);

        if (!mounted || !userId) {
          console.log("[Realtime] no stored user_id");
          return;
        }

        const userHomeChannel = supabase
          .channel(`rt-user-home-${userId}`)
          .on(
            "postgres_changes",
            {
              event: "*",
              schema: "public",
              table: "user_home",
            },
            (payload) => {
              console.log("[Realtime] user_home payload:", payload);

              const next = payload.new as { user_id?: string; home_id?: string } | null;
              const oldRow = payload.old as { user_id?: string; home_id?: string } | null;
              const rowUserId = next?.user_id ?? oldRow?.user_id;

              if (rowUserId === userId) {
                bumpHomesVersion();
              }
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] user_home status:", status);
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

        const joinRequestsChannel = supabase
          .channel(`rt-home-join-requests-${userId}`)
          .on(
            "postgres_changes",
            {
              event: "*",
              schema: "public",
              table: "home_join_requests",
            },
            (payload) => {
              console.log("[Realtime] home_join_requests payload:", payload);

              const next = payload.new as { home_id?: string; user_id?: string } | null;
              const oldRow = payload.old as { home_id?: string; user_id?: string } | null;
              const changedHomeId = next?.home_id ?? oldRow?.home_id;

              if (changedHomeId) {
                bumpJoinRequestsVersion(changedHomeId);
              }

              // אם בקשה אושרה/נדחתה ונוצר/נמחק שיוך, גם homes יתעדכן דרך user_home
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] home_join_requests status:", status);
          });

        channelsRef.current = [userHomeChannel, productItemsChannel, joinRequestsChannel];
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
  }, [bumpHomesVersion, bumpInventoryVersion, bumpJoinRequestsVersion]);

  const value = useMemo(
    () => ({
      homesVersion,
      inventoryVersionByHome,
      joinRequestsVersionByHome,
      bumpInventoryVersion,
      bumpJoinRequestsVersion,
    }),
    [homesVersion, inventoryVersionByHome, joinRequestsVersionByHome, bumpInventoryVersion, bumpJoinRequestsVersion]
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