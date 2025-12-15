import React from "react";
import { InventoryScreenBase } from "./inventory";

export default function PantryScreen() {
  return (
    <InventoryScreenBase
      initialCategory="pantry"
      hideTabs={true}
      title="מזווה"
    />
  );
}
