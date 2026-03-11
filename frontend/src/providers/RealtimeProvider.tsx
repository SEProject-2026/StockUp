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

  const channelsRef = useRef<ReturnType<typeof supabase.channel>[]>([]);

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
        const rawUser = await AsyncStorage.getItem("user");
        if (!rawUser || !mounted) return;

        const parsedUser = JSON.parse(rawUser);
        const userId = parsedUser?.id;
        if (!userId) return;

        const homeMembersChannel = supabase
          .channel(`rt-home-members-${userId}`)
          .on(
            "postgres_changes",
            {
              event: "*",
              schema: "public",
              table: "home_members",
              filter: `user_id=eq.${userId}`,
            },
            () => {
              bumpHomesVersion();
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] home_members:", status);
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
            () => {
              bumpHomesVersion();
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] homes:", status);
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
              const next = payload.new as { home_id?: string } | null;
              const oldRow = payload.old as { home_id?: string } | null;
              const homeId = next?.home_id ?? oldRow?.home_id;

              if (homeId) {
                bumpInventoryVersion(homeId);
              }
            }
          )
          .subscribe((status) => {
            console.log("[Realtime] product_items:", status);
          });

        channelsRef.current = [homeMembersChannel, homesChannel, productItemsChannel];
      } catch (error) {
        console.log("[Realtime] setup error:", error);
      }
    };

    setup();

    return () => {
      mounted = false;

      for (const channel of channelsRef.current) {
        supabase.removeChannel(channel);
      }

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