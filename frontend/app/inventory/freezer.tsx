import React from "react";
import { InventoryScreenBase } from "./inventory";

export default function FreezerScreen() {
  return (
    <InventoryScreenBase
      initialCategory="freezer"
      hideTabs={true}
      title="מקפיא"
    />
  );
}
