import { useEffect } from "react";
import { supabase } from "../../app/shopping-list/supabase";

export function useShoppingListsRealtime(
  homeId: string | undefined,
  onUpdate: () => void
) {
  useEffect(() => {
    if (!homeId) return;

    // הגדרת ערוץ האזנה לשינויים בטבלת shopping_lists
    const channel = supabase
      .channel(`public:shopping_lists:home_id=${homeId}`)
      .on(
        "postgres_changes",
        {
          event: "*", // מאזין להכל: INSERT, UPDATE, DELETE
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