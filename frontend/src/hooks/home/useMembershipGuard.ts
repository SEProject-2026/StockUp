import { useEffect, useRef } from "react";
import { router } from "expo-router";
import { supabase } from "@/src/config/supabase";
import { useRealtimeContext } from "@/src/providers/RealtimeProvider";

export function useMembershipGuard(homeId: string | undefined) {
  const { homesVersion } = useRealtimeContext();
  const initialVersionRef = useRef(homesVersion);

  useEffect(() => {
    const checkAccess = async () => {
      if (homesVersion === initialVersionRef.current || !homeId) return;

      try {
        const { data, error } = await supabase
          .from("user_home")
          .select("id")
          .eq("home_id", homeId)
          .maybeSingle();

        if (!data && !error) {
          console.log(`[Guard] Access revoked for home ${homeId}. Redirecting...`);
          router.replace("/home/home");
        }
      } catch (err) {
        console.log("[Guard] Error:", err);
      }
    };

    checkAccess();
  }, [homesVersion, homeId]);
}