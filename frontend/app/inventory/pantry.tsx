import React from "react";
import { InventoryScreenBase } from "./inventory";
import { Category } from "@/src/context/inventory-context";

export default function PantryScreen() {
  return (
    <InventoryScreenBase
      initialCategory="pantry"
      hideTabs={true}
      title="מזווה"
    />
  );
}
