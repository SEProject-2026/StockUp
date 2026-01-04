// components/inventory/InventoryFiltersBar.tsx
import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  Modal,
  Pressable,
  ScrollView,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import type { CategoryKey } from "@/src/components/inventory/inventory.utils";

type StatusFilter = "all" | "soon" | "expired";

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const ACCENT = "#0284C7";

const CATEGORIES: Array<{
  key: CategoryKey;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
}> = [
  { key: "all", label: "הכול", icon: "apps-outline" },
  { key: "fridge", label: "מקרר", icon: "snow-outline" },
  { key: "freezer", label: "מקפיא", icon: "cube-outline" },
  { key: "pantry", label: "מזווה", icon: "restaurant-outline" },
  { key: "cleaning supplies", label: "חומרי ניקוי", icon: "water-outline" },
  { key: "other", label: "אחר", icon: "ellipsis-horizontal-outline" },
];

const QUICK_KEYS: CategoryKey[] = ["all", "fridge", "freezer", "pantry"];

type Props = {
  hideTabs?: boolean;
  selectedTab: CategoryKey;
  onChangeTab: (tab: CategoryKey) => void;
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

  const selected = useMemo(
    () => CATEGORIES.find((c) => c.key === selectedTab) ?? CATEGORIES[0],
    [selectedTab]
  );

  const quickCats = useMemo(
    () => CATEGORIES.filter((c) => QUICK_KEYS.includes(c.key)),
    []
  );

  const extraCats = useMemo(
    () => CATEGORIES.filter((c) => !QUICK_KEYS.includes(c.key)),
    []
  );

  const selectedIsExtra = !QUICK_KEYS.includes(selectedTab);
  const selectedExtra = selectedIsExtra ? selected : null;

  return (
    <>
      {!hideTabs && (
        <View style={styles.categoryContainer}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.categoryChipsRow}
          >
            {quickCats.map((c) => (
              <CategoryChip
                key={c.key}
                label={c.label}
                icon={c.icon}
                active={selectedTab === c.key}
                onPress={() => onChangeTab(c.key)}
              />
            ))}

            {selectedExtra && (
              <CategoryChip
                key={`selected-extra-${selectedExtra.key}`}
                label={selectedExtra.label}
                icon={selectedExtra.icon}
                active={true}
                onPress={() => setCatOpen(true)}
                style={{ borderStyle: "dashed" }}
              />
            )}

            <CategoryChip
              label="עוד"
              icon="chevron-down"
              active={false}
              onPress={() => setCatOpen(true)}
              style={{ marginRight: 6 }}
            />
          </ScrollView>

          <Text style={styles.selectedHint}>
            נבחר: <Text style={styles.selectedHintStrong}>{selected.label}</Text>
          </Text>
        </View>
      )}

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

          {/* status filter */}
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

      <Modal
        visible={catOpen}
        animationType="fade"
        transparent
        onRequestClose={() => setCatOpen(false)}
      >
        <Pressable style={styles.backdrop} onPress={() => setCatOpen(false)} />

        <View style={styles.sheet}>
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>בחירת קטגוריה</Text>
            <TouchableOpacity onPress={() => setCatOpen(false)} activeOpacity={0.8}>
              <Ionicons name="close" size={20} color={BRAND_MUTED} />
            </TouchableOpacity>
          </View>

          {CATEGORIES.map((c) => {
            const active = c.key === selectedTab;
            return (
              <TouchableOpacity
                key={c.key}
                style={[styles.sheetRow, active && styles.sheetRowActive]}
                onPress={() => {
                  onChangeTab(c.key);
                  setCatOpen(false);
                }}
                activeOpacity={0.85}
              >
                <View style={styles.sheetRowRight}>
                  <View style={styles.sheetRowLabelWrap}>
                    <Text style={[styles.sheetRowText, active && styles.sheetRowTextActive]}>
                      {c.label}
                    </Text>
                    {active && <Ionicons name="checkmark" size={18} color={ACCENT} />}
                  </View>

                  <Ionicons
                    name={c.icon}
                    size={18}
                    color={active ? ACCENT : BRAND_MUTED}
                  />
                </View>
              </TouchableOpacity>
            );
          })}

        </View>
      </Modal>
    </>
  );
};

function CategoryChip({
  label,
  icon,
  active,
  onPress,
  style,
}: {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  active: boolean;
  onPress: () => void;
  style?: any;
}) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[styles.catChip, active && styles.catChipActive, style]}
      activeOpacity={0.85}
    >
      <Ionicons
        name={icon}
        size={16}
        color={active ? "#FFFFFF" : BRAND_MUTED}
      />
      <Text style={[styles.catChipText, active && styles.catChipTextActive]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

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
      activeOpacity={0.85}
    >
      <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  categoryContainer: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
  },
  categoryChipsRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingVertical: 4,
  },
  catChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    backgroundColor: BRAND_BLUE_SOFT,
    borderRadius: 999,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  catChipActive: {
    backgroundColor: ACCENT,
    borderColor: ACCENT,
  },
  catChipText: {
    fontSize: 12,
    color: BRAND_MUTED,
    fontWeight: "600",
  },
  catChipTextActive: {
    color: "#FFFFFF",
  },
  selectedHint: {
    marginTop: 6,
    textAlign: "right",
    fontSize: 12,
    color: BRAND_MUTED,
  },
  selectedHintStrong: {
    color: BRAND_TEXT,
    fontWeight: "800",
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
    backgroundColor: ACCENT,
    borderColor: ACCENT,
  },
  filterChipText: {
    fontSize: 12,
    color: BRAND_MUTED,
  },
  filterChipTextActive: {
    color: "#FFFFFF",
    fontWeight: "600",
  },

  // Modal
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.25)",
  },
  sheet: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 18,
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    padding: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  sheetHeader: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingBottom: 8,
  },
  sheetTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: BRAND_TEXT,
    textAlign: "right",
  },
  sheetRow: {
    paddingVertical: 12,
    paddingHorizontal: 10,
    borderRadius: 12,
  },
  sheetRowActive: {
    backgroundColor: BRAND_BLUE_SOFT,
  },
  sheetRowRight: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  sheetRowLabelWrap: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
  },
  sheetRowText: {
    fontSize: 14,
    color: BRAND_TEXT,
    textAlign: "right",
  },
  sheetRowTextActive: {
    fontWeight: "700",
    color: ACCENT,
  },
  modalFooterHintWrap: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#EEF2F7",
  },
  modalFooterHint: {
    fontSize: 12,
    color: BRAND_MUTED,
    textAlign: "right",
    lineHeight: 18,
  },
});
