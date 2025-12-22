// components/inventory/InventoryFiltersBar.tsx
import React from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import {CategoryKey} from "@/app/inventory/inventory";


type StatusFilter = "all" | "soon" | "expired";

const TABS = [
  { key: "fridge", label: "מקרר" },
  { key: "freezer", label: "מקפיא" },
  { key: "pantry", label: "מזווה" },
  { key: "all", label: "הכול" },
] as const;

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";

type Props = {
  hideTabs?: boolean;
  selectedTab: CategoryKey;
  onChangeTab: (tab: CategoryKey) => void;
  search: string;
  onChangeSearch: (value: string) => void;
  statusFilter: StatusFilter;
  onChangeStatusFilter: (value: StatusFilter) => void;
  /** האם להציג את כל אפשרויות הסינון (חיפוש + תוקף) */
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
  return (
    <>
      {/* טאבים של קטגוריות – תמיד כשלא hideTabs */}
      {!hideTabs && (
        <View style={styles.tabsContainer}>
          <View style={styles.tabsRow}>
            {TABS.map((tab) => {
              const active = tab.key === selectedTab;
              return (
                <TouchableOpacity
                  key={tab.key}
                  style={[styles.tab, active && styles.tabActive]}
                  onPress={() => onChangeTab(tab.key as CategoryKey)}
                >
                  <Text
                    style={[styles.tabText, active && styles.tabTextActive]}
                  >
                    {tab.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      )}

      {/* פאנל פילטרים – יופיע רק כשהמשתמש לוחץ על אייקון הפילטר במסך */}
      {filtersVisible && (
        <>
          {/* Search */}
          <View style={styles.searchBox}>
            <Ionicons name="search-outline" size={18} color={BRAND_MUTED} />
            <TextInput
              style={styles.searchInput}
              placeholder="חיפוש לפי שם מוצר..."
              placeholderTextColor="#9CA3AF"
              value={search}
              onChangeText={onChangeSearch}
            />
          </View>

          {/* date filter */}
          <View style={styles.filterRow}>
            <View style={styles.filtersLeft}>
              <FilterChip
                label="הכול"
                active={statusFilter === "all"}
                onPress={() => onChangeStatusFilter("all")}
              />
              <FilterChip
                label="תוקף קרוב"
                active={statusFilter === "soon"}
                onPress={() => onChangeStatusFilter("soon")}
                style={{ marginLeft: 8 }}
              />
              <FilterChip
                label="פג תוקף"
                active={statusFilter === "expired"}
                onPress={() => onChangeStatusFilter("expired")}
                style={{ marginLeft: 8 }}
              />
            </View>

            <Text style={styles.sortLabel}>מיון לפי מוצר</Text>
          </View>
        </>
      )}
    </>
  );
};

function FilterChip({
  label,
  active,
  onPress,
  style,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
  style?: any;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[styles.filterChip, active && styles.filterChipActive, style]}
    >
      <Text
        style={[styles.filterChipText, active && styles.filterChipTextActive]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  tabsContainer: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
  },
  tabsRow: {
    flexDirection: "row-reverse",
    backgroundColor: BRAND_BLUE_SOFT,
    borderRadius: 999,
    padding: 4,
    gap: 4,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  tabActive: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  tabText: {
    fontSize: 13,
    color: BRAND_MUTED,
  },
  tabTextActive: {
    color: BRAND_TEXT,
    fontWeight: "600",
  },
  searchBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    marginHorizontal: 16,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 4,
    gap: 8,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 1,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: BRAND_TEXT,
    textAlign: "right",
  },
  filterRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    marginTop: 6,
    marginBottom: 4,
  },
  filtersLeft: {
    flexDirection: "row-reverse",
    alignItems: "center",
  },
  sortLabel: {
    fontSize: 13,
    color: BRAND_MUTED,
    fontWeight: "600",
    textAlign: "right",
  },
  filterChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  filterChipActive: {
    backgroundColor: "#0284C7",
    borderColor: "#0284C7",
  },
  filterChipText: {
    fontSize: 12,
    color: BRAND_MUTED,
  },
  filterChipTextActive: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
});
