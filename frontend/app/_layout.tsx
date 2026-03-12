import React from "react";
import { useEffect } from "react";
import { Stack, useRouter } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { InventoryProvider } from "../src/context/inventory-context";
import * as Notifications from 'expo-notifications';

export default function RootLayout() {
  const router = useRouter();
  const response = Notifications.useLastNotificationResponse();
  useEffect(() => {
    if (response) {
      const data = response.notification.request.content.data;
      const action = data?.action;

      console.log("User tapped on notification with action:", action);

      switch (action) {
        case 'join_request':
          router.push(`/home/${data.home_id}`);
          break;
          
        case 'receipt_added':
          router.push('/home/home'); 
          break;
          
        case 'expiration_alert':
          router.push('/home/home');
          break;
          
        default:
          console.log("Unknown notification action");
      }
    }
  }, [response]);
  return (
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
  );
}
