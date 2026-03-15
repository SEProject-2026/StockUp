import React from "react";
import { Stack } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { InventoryProvider } from "../src/context/inventory-context";
import { RealtimeProvider } from "../src/providers/RealtimeProvider";

export default function RootLayout() {
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
