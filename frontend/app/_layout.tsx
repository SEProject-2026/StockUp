import React, { createContext, useContext, useEffect, useState } from "react";
import { Stack, useRouter, useSegments } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import * as Notifications from 'expo-notifications';
import { Session } from "@supabase/supabase-js";

import { supabase } from "@/src/lib/supabase"; 
import { InventoryProvider } from "../src/context/inventory-context";
import { RealtimeProvider } from "../src/providers/RealtimeProvider";
import { approveJoinRequest, rejectJoinRequest } from "@/src/api/homes";

// --- 1. Auth Context ---
const AuthContext = createContext<{ session: Session | null; loading: boolean }>({
  session: null,
  loading: true,
});

export const useAuth = () => useContext(AuthContext);

// --- 2. Navigation Guard  ---
function NavigationGuard() {
  const { session, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;

    // checking if the user is in the auth group pages (login/signup) or not
    const inAuthGroup = segments[0] === "login" || segments[0] === "signup";

    if (!session && !inAuthGroup) {
      // there's no user and they're trying to access a protected page -> send to Login
      router.replace("/login");
    } else if (session && inAuthGroup) {
      // there is a user and they're trying to access the login/signup pages -> send to Home
      router.replace("/home/home");
    }
  }, [session, loading, segments]);

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: "fade",
        animationDuration: 150,
      }}
    />
  );
}

export default function RootLayout() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  //A. Supabase Auth Management
  useEffect(() => {
    // first check - is there an active session?
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    // Listening for changes in real time
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Notification management
  useEffect(() => {
    const handleNotification = (response: Notifications.NotificationResponse) => {
      const data = response.notification.request.content.data;
      const actionId = response.actionIdentifier;
      const action = data?.action;

      if (actionId === 'APPROVE') {
        if (data?.home_id && data?.user_id) {
          approveJoinRequest(data.home_id as string, data.user_id as string)
            .catch(e => console.error("❌ שגיאה באישור:", e));
        }
      } 
      else if (actionId === 'REJECT') {
        if (data?.home_id && data?.user_id) {
          rejectJoinRequest(data.home_id as string, data.user_id as string)
            .catch(e => console.error("❌ שגיאה בדחייה:", e));
        }
      } 
      else if (actionId === Notifications.DEFAULT_ACTION_IDENTIFIER) {
        if (action === 'join_request') {
          setTimeout(() => {
            router.push({
              pathname: '/settings',
              params: { homeId: data.home_id as string, openRequests: 'true' }
            });
          }, 500);
        }
      }
    };

    const subscription = Notifications.addNotificationResponseReceivedListener(handleNotification);
    Notifications.getLastNotificationResponseAsync().then(response => {
      if (response) handleNotification(response);
    });

    return () => subscription.remove();
  }, []);

  return (
    <AuthContext.Provider value={{ session, loading }}>
      <RealtimeProvider>
        <GestureHandlerRootView style={{ flex: 1 }}>
          <InventoryProvider>
            <NavigationGuard />
          </InventoryProvider>
        </GestureHandlerRootView>
      </RealtimeProvider>
    </AuthContext.Provider>
  );
}