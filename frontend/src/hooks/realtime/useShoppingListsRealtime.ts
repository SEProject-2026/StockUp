import { useEffect } from "react";
import { supabase } from "@/src/config/supabase";

export function useShoppingListsRealtime(
  homeId: string | undefined,
  onUpdate: () => void
) {
  useEffect(() => {
    if (!homeId) return;

    const channel = supabase
      .channel(`public:shopping_lists:home_id=${homeId}`)
      .on(
        "postgres_changes",
        {
          event: "*", 
          schema: "public",
          table: "shopping_lists",
          filter: `home_id=eq.${homeId}`,
        },
        () => {
          console.log("[Realtime] Shopping lists changed, refreshing...");
          onUpdate();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [homeId, onUpdate]);
}