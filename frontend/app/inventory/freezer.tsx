import React from "react";
import { InventoryScreenBase } from "./inventory";
import { Category } from "@/src/context/inventory-context";

export default function FreezerScreen() {
  return (
    <InventoryScreenBase
      initialCategory="freezer"
      hideTabs={true}
      title="מקפיא"
    />
  );
}
