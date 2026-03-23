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
import { router } from "expo-router"; 
import { useAuth } from "@/src/context/auth-context"; // שימוש ב-Hook המרכזי שיצרנו

type RealtimeContextValue = {
  homesVersion: number;
  inventoryVersionByHome: Record<string, number>;
  joinRequestsVersionByHome: Record<string, number>;
  bumpInventoryVersion: (homeId: string) => void;
  bumpJoinRequestsVersion: (homeId: string) => void;
};

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  // שוליפים את ה-session מה-Provider שעוטף אותנו ב-RootLayout
  const { session } = useAuth();
  const userId = session?.user?.id;

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

  const bumpAllInventoryVersions = useCallback(() => {
    setInventoryVersionByHome((prev) => {
      const newState = { ...prev };
      Object.keys(newState).forEach((id) => {
        newState[id] = (newState[id] ?? 0) + 1;
      });
      return newState;
    });
  }, []);

  const bumpJoinRequestsVersion = useCallback((homeId: string) => {
    if (!homeId) return;
    setJoinRequestsVersionByHome((prev) => ({
      ...prev,
      [homeId]: (prev[homeId] ?? 0) + 1,
    }));
  }, []);

  useEffect(() => {
    // אם אין משתמש מחובר, אנחנו לא מנסים להירשם לערוצים
    if (!userId) {
      console.log("[Realtime] No active session, skipping channel setup.");
      return;
    }

    console.log("[Realtime] Setting up channels for user:", userId);

    const setup = async () => {
      try {
        // 1. User Home Channel
        const userHomeChannel = supabase
          .channel(`rt-user-home-${userId}`)
          .on(
            "postgres_changes",
            { event: "*", schema: "public", table: "user_home" },
            (payload) => {
              console.log("[Realtime] user_home payload:", payload);
              const next = payload.new as { user_id?: string } | null;
              const oldRow = payload.old as { user_id?: string } | null;
              const rowUserId = next?.user_id ?? oldRow?.user_id;

              if (rowUserId === userId) {
                if (payload.eventType === "DELETE") {
                  console.log("[Realtime] User removed from home, redirecting...");
                  router.replace("/home/home"); 
                  return;
                }
                bumpHomesVersion();
              }
            }
          )
          .subscribe();

        // 2. Products Channel
        const productsChannel = supabase
          .channel(`rt-products-${userId}`)
          .on(
            "postgres_changes",
            { event: "*", schema: "public", table: "products" },
            (payload) => {
              const next = payload.new as { home_id?: string } | null;
              const oldRow = payload.old as { home_id?: string } | null;
              const changedHomeId = next?.home_id ?? oldRow?.home_id;

              if (payload.eventType === "DELETE" && !changedHomeId) {
                bumpAllInventoryVersions();
              } else if (changedHomeId) {
                bumpInventoryVersion(changedHomeId);
              }
            }
          )
          .subscribe();

        // 3. Product Items Channel
        const productItemsChannel = supabase
          .channel(`rt-product-items-${userId}`)
          .on(
            "postgres_changes",
            { event: "*", schema: "public", table: "product_items" },
            async (payload) => {
              if (payload.eventType === "DELETE") {
                 bumpAllInventoryVersions();
                 return;
              }
              const next = payload.new as { product_id?: string } | null;
              const productId = next?.product_id;
              if (!productId) return;

              const { data } = await supabase
                .from("products")
                .select("home_id")
                .eq("id", productId)
                .single();

              if (data?.home_id) {
                bumpInventoryVersion(data.home_id);
              }
            }
          )
          .subscribe();

        // 4. Join Requests Channel
        const joinRequestsChannel = supabase
          .channel(`rt-home-join-requests-${userId}`)
          .on(
            "postgres_changes",
            { event: "*", schema: "public", table: "home_join_requests" },
            (payload) => {
              const next = payload.new as { home_id?: string } | null;
              const oldRow = payload.old as { home_id?: string } | null;
              const changedHomeId = next?.home_id ?? oldRow?.home_id;
              if (changedHomeId) {
                bumpJoinRequestsVersion(changedHomeId);
              }
            }
          )
          .subscribe();

        channelsRef.current = [
          userHomeChannel,
          productsChannel,
          productItemsChannel,
          joinRequestsChannel,
        ];
      } catch (error) {
        console.error("[Realtime] Setup error:", error);
      }
    };

    setup();

    // פונקציית ניקוי - רצה כשהמשתמש מתנתק או כשהקומפוננטה יורדת
    return () => {
      console.log("[Realtime] Cleaning up channels for user:", userId);
      channelsRef.current.forEach((channel) => {
        supabase.removeChannel(channel);
      });
      channelsRef.current = [];
    };
  }, [userId, bumpHomesVersion, bumpInventoryVersion, bumpJoinRequestsVersion, bumpAllInventoryVersions]);

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