import React from "react";
import { InventoryScreenBase } from "./inventory";
import { Category } from "@/src/context/inventory-context";

export default function FridgeScreen() {
  return (
    <InventoryScreenBase
      initialCategory="fridge"
      hideTabs={true}
      title="מקרר"
    />
  );
}
