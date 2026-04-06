import React, { createContext, useContext, useEffect, useState } from "react";
import { Stack, useRouter, useSegments } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import * as Notifications from 'expo-notifications';
import * as SplashScreen from 'expo-splash-screen';
import { Session } from "@supabase/supabase-js";

import { supabase } from "@/src/config/supabase"; 
import { InventoryProvider } from "../src/context/inventory-context";
import { RealtimeProvider } from "../src/providers/RealtimeProvider";
import { AuthProvider, useAuth } from "@/src/context/auth-context"; // <--- Centralize Auth
import { approveJoinRequest, rejectJoinRequest } from "@/src/api/homes";

// --- 1. Auth Context (Merged into src/context/auth-context.tsx) ---

// --- 2. Navigation Guard ---
SplashScreen.preventAutoHideAsync();

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

  // A. ניהול Auth - Moved to AuthProvider in RootLayout return

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

  // C. הסתרת ה-Splash Screen לאחר השהייה
  useEffect(() => {
    const hideSplash = async () => {
      // נחכה 2 שניות (או 1.5 שניות לבידור)
      await new Promise(resolve => setTimeout(resolve, 2000));
      await SplashScreen.hideAsync();
    };
    hideSplash();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <AuthProvider>
        <RealtimeProvider>
          <InventoryProvider>
            <NavigationGuard />
          </InventoryProvider>
        </RealtimeProvider>
      </AuthProvider>
    </GestureHandlerRootView>
  );
}