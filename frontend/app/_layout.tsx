import React, { createContext, useContext, useEffect, useState } from "react";
import { Stack, useRouter, useSegments } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import * as Notifications from 'expo-notifications';
import { Session } from "@supabase/supabase-js";

import { supabase } from "@/src/lib/supabase"; 
import { InventoryProvider } from "../src/context/inventory-context";
import { RealtimeProvider } from "../src/providers/RealtimeProvider";
import { approveJoinRequest, rejectJoinRequest } from "@/src/api/homes";

// --- 1. Auth Context (נשאר כאן זמנית, אך מומלץ להעביר לקובץ נפרד ב-src/context) ---
const AuthContext = createContext<{ session: Session | null; loading: boolean }>({
  session: null,
  loading: true,
});

export const useAuth = () => useContext(AuthContext);

// --- 2. Navigation Guard ---
function NavigationGuard() {
  const { session, loading } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;

    // הגדרת דפים שניתן לגשת אליהם ללא התחברות
    const isAuthPage = 
      segments[0] === "login" || 
      segments[0] === "signup" || 
      segments[0] === "reset-password"; // הוספנו את איפוס הסיסמה לרשימה הלבנה

    if (!session && !isAuthPage) {
      // אין משתמש והוא מנסה להיכנס לדף מוגן -> שלח ללוגין
      router.replace("/login");
    } else if (session && isAuthPage) {
      // יש משתמש והוא מנסה להיכנס לדפי התחברות -> שלח לבית
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
    >
      <Stack.Screen name="login" options={{ headerShown: false }} />
      <Stack.Screen name="signup" options={{ headerShown: false }} />
      <Stack.Screen name="reset-password" options={{ headerShown: false }} /> 
      <Stack.Screen name="home/home" options={{ headerShown: false }} />
    </Stack>
  );
}

export default function RootLayout() {
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  // A. ניהול Auth
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  // B. ניהול התראות
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
    return () => subscription.remove();
  }, [router]);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <AuthContext.Provider value={{ session, loading }}>
        <RealtimeProvider>
          <InventoryProvider>
            <NavigationGuard />
          </InventoryProvider>
        </RealtimeProvider>
      </AuthContext.Provider>
    </GestureHandlerRootView>
  );
}