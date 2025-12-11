import React from "react";
import { InventoryScreenBase } from "../screens/InventoryScreen";

export default function PantryScreen() {
  return (
    <InventoryScreenBase
      initialCategory="pantry"
      hideTabs={true}
      title="מזווה"
    />
  );
}
