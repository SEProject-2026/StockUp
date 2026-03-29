// src/features/inventory/components/InventoryFiltersBar.tsx
import React, { useState } from "react";
import { View, TextInput, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import type { locationKey } from "@/src/components/inventory/inventory.utils";
import InventorylocationTabs from "./InventoryLocationTabs";
import InventoryStatusChips from "./InventoryStatusChips";
import InventorylocationPickerModal from "./InventoryLocationPickerModal";
import { COLORS, type StatusFilter } from "./filters.constants";

type Props = {
  hideTabs?: boolean;

  selectedTab: locationKey;
  onChangeTab: (tab: locationKey) => void;

  search: string;
  onChangeSearch: (value: string) => void;

  statusFilter: StatusFilter;
  onChangeStatusFilter: (value: StatusFilter) => void;

  filtersVisible?: boolean;
};

export const InventoryFiltersBar: React.FC<Props> = ({
  hideTabs,
  selectedTab,
  onChangeTab,
  search,
  onChangeSearch,
  statusFilter,
  onChangeStatusFilter,
  filtersVisible = true,
}) => {
  const [catOpen, setCatOpen] = useState(false);

  return (
    <>
      {!hideTabs && (
        <InventorylocationTabs
          selectedTab={selectedTab}
          onChangeTab={onChangeTab}
          onOpenMore={() => setCatOpen(true)}
        />
      )}

      {filtersVisible && (
        <>
          <View style={styles.searchBox}>
            <Ionicons name="search-outline" size={18} color={COLORS.BRAND_MUTED} />
            <TextInput
              style={styles.searchInput}
              placeholder="חיפוש לפי שם מוצר..."
              placeholderTextColor="#9CA3AF"
              value={search}
              onChangeText={onChangeSearch}
              textAlign="right"
              autoCorrect={false}
              autoCapitalize="none"
            />
          </View>

          <InventoryStatusChips value={statusFilter} onChange={onChangeStatusFilter} />
        </>
      )}

      <InventorylocationPickerModal
        open={catOpen}
        selectedTab={selectedTab}
        onClose={() => setCatOpen(false)}
        onPick={(c) => {
          onChangeTab(c);
          setCatOpen(false);
        }}
      />
    </>
  );
};

const styles = StyleSheet.create({
  searchBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    marginHorizontal: 16,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginTop: 8,
    marginBottom: 4,
    gap: 10,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    // Modern shadow
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 3,
  },
  searchInput: {
    flex: 1,
    fontSize: 15,
    fontWeight: "500",
    color: COLORS.BRAND_TEXT,
    textAlign: "right",
  },
});
