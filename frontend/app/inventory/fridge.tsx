import React from "react";
import { InventoryScreenBase } from "../screens/InventoryScreen";

export default function FridgeScreen() {
  return (
    <InventoryScreenBase
      initialCategory="fridge"
      hideTabs={true}
      title="מקרר"
    />
  );
}
