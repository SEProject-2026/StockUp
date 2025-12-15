import React from "react";
import { InventoryScreenBase } from "./inventory";

export default function FridgeScreen() {
  return (
    <InventoryScreenBase
      initialCategory="fridge"
      hideTabs={true}
      title="מקרר"
    />
  );
}
