import React from "react";
import { InventoryScreenBase } from "./index";

export default function PantryScreen() {
  return (
    <InventoryScreenBase
      initialCategory="pantry"
      hideTabs={true}
      title="מזווה"
    />
  );
}
