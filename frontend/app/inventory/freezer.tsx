import React from "react";
import { InventoryScreenBase } from "./inventory";

export default function FridgeScreen() {
  return (
    <InventoryScreenBase
      initialCategory="freezer"
      hideTabs={true}
      title="מקפיא"
    />
  );
}
