import React from "react";
import { Stack } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { InventoryProvider } from "./inventory/inventory-store";

export default function RootLayout() {
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
