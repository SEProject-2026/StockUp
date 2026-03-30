import React from "react";
import { useEffect } from "react";
import { Stack, useRouter } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { I18nManager } from "react-native";
import { InventoryProvider } from "../src/context/inventory-context";
import * as Notifications from 'expo-notifications';
import { approveJoinRequest, rejectJoinRequest } from "@/src/api/homes";
import { RealtimeProvider } from "../src/providers/RealtimeProvider";

export default function RootLayout() {
  const router = useRouter();

  // Force RTL for Hebrew
  if (!I18nManager.isRTL) {
    I18nManager.allowRTL(true);
    I18nManager.forceRTL(true);
  }

  useEffect(() => {
    // הפונקציה המרכזית שעושה את העבודה, לא משנה מאיפה ההתראה הגיעה
    const handleNotification = (response: Notifications.NotificationResponse) => {
      const data = response.notification.request.content.data;
      const actionId = response.actionIdentifier;
      const action = data?.action;

      // טיפול בכפתור אישור
      if (actionId === 'APPROVE') {
        if (data?.home_id && data?.user_id) {
          console.log("✅ שולח לאישור. בית:", data.home_id, "משתמש:", data.user_id);
          approveJoinRequest(data.home_id as string, data.user_id as string )
            .catch(e => console.error("❌ שגיאה באישור:", e));
        }
      } 
      // טיפול בכפתור דחייה
      else if (actionId === 'REJECT') {
        if (data?.home_id && data?.user_id) {
          console.log("🗑️ שולח לדחייה...");
          rejectJoinRequest(data.home_id as string, data.user_id as string)
            .catch(e => console.error("❌ שגיאה בדחייה:", e));
        }
      } 
      // טיפול בלחיצה רגילה על ההתראה (כדי להיכנס אליה)
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

    // --- רשת הביטחון הכפולה שלנו --- //

    // 1. תופס לחיצות כשהאפליקציה פתוחה או נמצאת ברקע (Background)
    const subscription = Notifications.addNotificationResponseReceivedListener(handleNotification);

    // 2. תופס לחיצות כשהאפליקציה הייתה סגורה לגמרי והרגע נדלקה (Cold Start)
    Notifications.getLastNotificationResponseAsync().then(response => {
      if (response) {
        handleNotification(response);
      }
    });

    // ניקוי כשהקומפוננטה יורדת
    return () => subscription.remove();
  }, []);
  return (
    <RealtimeProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <InventoryProvider>
          <Stack
            screenOptions={{
              headerShown: false,
              animation: "fade", 
              animationDuration: 150,
            }}
          />
        </InventoryProvider>
      </GestureHandlerRootView>
    </RealtimeProvider>);
}
