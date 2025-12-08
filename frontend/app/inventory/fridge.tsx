import React from "react";
import { InventoryScreenBase } from "./index";

export default function FridgeScreen() {
  return (
    <InventoryScreenBase
      initialCategory="fridge"
      hideTabs={true}
      title="מקרר"
    />
  );
}
