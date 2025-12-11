import React from "react";
import { InventoryScreenBase } from "../screens/InventoryScreen";

export default function FridgeScreen() {
  return (
    <InventoryScreenBase
      initialCategory="freezer"
      hideTabs={true}
      title="מקפיא"
    />
  );
}
