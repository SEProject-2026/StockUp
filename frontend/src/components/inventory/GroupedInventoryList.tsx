import React, { useMemo, useRef, useState } from "react";
import { View, Text, FlatList, StyleSheet, Pressable, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import type { InventoryRow, ProductGroupVM } from "@/src/components/inventory/inventory.utils";
import { locationColor, locationLabel } from "@/src/components/inventory/inventory.utils";

const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BLUE_SOFT = "#F0FAFF";

type Props = {
  groupedItems: ProductGroupVM[];
  searchQuery: string;
  onChangeQty: (itemId: string, delta: number) => void;
  onEditItem: (item: InventoryRow) => void;
  onDeleteItem: (itemId: string) => void;
  onAddItem: () => void;
};

export const GroupedInventoryList: React.FC<Props> = ({
  groupedItems,
  searchQuery,
  onChangeQty,
  onEditItem,
  onDeleteItem,
  onAddItem,
}) => {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const listRef = useRef<FlatList<ProductGroupVM>>(null);
  const isSearching = searchQuery.trim().length >= 2;

  const toggle = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <FlatList
      ref={listRef}
      data={groupedItems}
      keyExtractor={(g) => g.key}
      contentContainerStyle={styles.listContent}
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="none"
      removeClippedSubviews={false}
      maintainVisibleContentPosition={{ minIndexForVisible: 1, autoscrollToTopThreshold: 40 }}
      ListEmptyComponent={
        <Text style={styles.emptyText}>לא נמצאו פריטים בקטגוריה / חיפוש הזה.</Text>
      }
      renderItem={({ item: g }) => (
        <ProductGroupCard
          group={g}
          expanded={isSearching ? false : !!expanded[g.key]}
          onToggle={() => {
            if (isSearching) return;
            toggle(g.key);
          }}
          onChangeQty={onChangeQty}
          onEditItem={onEditItem}
          onDeleteItem={onDeleteItem}
        />
      )}
      ListFooterComponent={
        <TouchableOpacity style={styles.addCard} onPress={onAddItem}>
          <View style={styles.addIconCircle}>
            <Ionicons name="add" size={20} color="#0284C7" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.addTitle}>הוספת מוצר חדש</Text>
            <Text style={styles.addSubtitle}>הוספת פריט נוסף למלאי שלך, לפי האזור הנבחר.</Text>
          </View>
        </TouchableOpacity>
      }
    />
  );
};

function ProductGroupCard(props: {
  group: ProductGroupVM;
  expanded: boolean;
  onToggle: () => void;
  onChangeQty: (itemId: string, delta: number) => void;
  onEditItem: (item: InventoryRow) => void;
  onDeleteItem: (itemId: string) => void;
}) {
  const { group, expanded, onToggle, onChangeQty, onEditItem, onDeleteItem } = props;

  // strip color: if only one location, use it; otherwise neutral
  const stripColor = useMemo(() => {
    if (group.sections.length === 1) return locationColor(group.sections[0].location);
    return "#E5E7EB";
  }, [group.sections]);

  return (
    <View style={styles.groupCard}>
      <View style={styles.itemRow}>
        <View style={[styles.itemStrip, { backgroundColor: stripColor }]} />

        <Pressable style={styles.itemMain} onPress={onToggle}>
          <View style={styles.itemHeaderRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.itemName} numberOfLines={1}>
                {group.title}
              </Text>
              {group.subtitle ? (
                <Text style={styles.itemSubtitle} numberOfLines={1}>
                  {group.subtitle}
                </Text>
              ) : null}
            </View>

            <View style={styles.groupHeaderRight}>
              <Text style={styles.groupTotalQtyText}>סה״כ x{group.totalQuantity}</Text>
              <Ionicons name={expanded ? "chevron-up" : "chevron-down"} size={18} color="#0369A1" />
            </View>
          </View>

          <View style={styles.itemMetaRow}>
            <Text style={styles.groupCountText}>{countItems(group)} רשומות</Text>
            <Text style={styles.locationsHintText}>
              {group.sections.length === 1 ? locationLabel(group.sections[0].location) : `${group.sections.length} אזורים`}
            </Text>
          </View>
        </Pressable>
      </View>

      {expanded && (
        <View style={styles.groupChildrenContainer}>
          {group.sections.map((sec) => (
            <View key={sec.location} style={styles.sectionBlock}>
              <View style={styles.sectionHeader}>
                <View style={[styles.sectionDot, { backgroundColor: locationColor(sec.location) }]} />
                <Text style={styles.sectionTitle}>
                  {locationLabel(sec.location)} • x{sec.totalQuantity}
                </Text>
              </View>

              {sec.items.map((item) => (
                <BatchRow
                  key={item.itemId}
                  item={item}
                  onChangeQty={onChangeQty}
                  onEditItem={onEditItem}
                  onDeleteItem={onDeleteItem}
                />
              ))}
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

function countItems(group: ProductGroupVM) {
  return group.sections.reduce((acc, s) => acc + s.items.length, 0);
}

function BatchRow(props: {
  item: InventoryRow;
  onChangeQty: (itemId: string, delta: number) => void;
  onEditItem: (item: InventoryRow) => void;
  onDeleteItem: (itemId: string) => void;
}) {
  const { item, onChangeQty, onEditItem, onDeleteItem } = props;

  return (
    <View style={styles.batchRow}>
      <View style={styles.batchInfo}>
        <View style={styles.batchTextCol}>
          <View style={styles.batchDateRow}>
            <Ionicons name="time-outline" size={14} color={BRAND_MUTED} />
            <Text style={styles.batchInfoText}>
              {item.expirationDate ? `תוקף: ${item.expirationDate}` : "ללא תאריך תוקף"}
            </Text>
          </View>
        </View>
      </View>

      <View style={styles.batchActions}>
        <View style={styles.qtyControl}>
          <TouchableOpacity style={styles.qtyButton} onPress={() => onChangeQty(item.itemId, -1)}>
            <Text style={styles.qtyButtonText}>−</Text>
          </TouchableOpacity>
          <Text style={styles.qtyValue}>{item.quantity}</Text>
          <TouchableOpacity style={styles.qtyButton} onPress={() => onChangeQty(item.itemId, 1)}>
            <Text style={styles.qtyButtonText}>+</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.batchIconButton} onPress={() => onEditItem(item)}>
          <Ionicons name="create-outline" size={18} color="#0369A1" />
        </TouchableOpacity>

        <TouchableOpacity style={styles.batchIconButton} onPress={() => onDeleteItem(item.itemId)}>
          <Ionicons name="trash-outline" size={18} color="#DC2626" />
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  listContent: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 40, gap: 8 },
  emptyText: { textAlign: "center", marginTop: 32, color: BRAND_MUTED, fontSize: 14 },

  groupCard: { marginBottom: 8 },
  itemRow: {
    flexDirection: "row",
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    overflow: "hidden",
  },
  itemStrip: { width: 4 },
  itemMain: { flex: 1, paddingHorizontal: 12, paddingVertical: 10 },

  itemHeaderRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 4,
    gap: 10,
  },
  groupHeaderRight: { flexDirection: "row", alignItems: "center", gap: 6 },
  groupTotalQtyText: { fontSize: 13, fontWeight: "600", color: "#0369A1" },

  itemName: {
    fontSize: 16,
    fontWeight: "800",
    textAlign: "right",
    color: BRAND_TEXT,
  },
  itemSubtitle: {
    marginTop: 2,
    fontSize: 12,
    color: BRAND_MUTED,
    textAlign: "right",
  },

  itemMetaRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    marginTop: 6,
    alignItems: "center",
  },
  groupCountText: { fontSize: 12, color: BRAND_MUTED },
  locationsHintText: { fontSize: 12, color: BRAND_MUTED },

  groupChildrenContainer: {
    marginHorizontal: 10,
    marginTop: 6,
    marginBottom: 2,
    borderLeftWidth: 1,
    borderLeftColor: "#E5E7EB",
    paddingLeft: 8,
    gap: 10,
  },

  sectionBlock: { gap: 6 },
  sectionHeader: { flexDirection: "row-reverse", alignItems: "center", gap: 8 },
  sectionDot: { width: 8, height: 8, borderRadius: 4 },
  sectionTitle: { fontSize: 12, fontWeight: "800", color: BRAND_TEXT, textAlign: "right" },

  batchRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 6,
  },
  batchInfo: { flex: 1, alignItems: "flex-end" },
  batchTextCol: { alignItems: "flex-end", justifyContent: "center", flex: 1 },
  batchDateRow: { flexDirection: "row-reverse", alignItems: "center", gap: 6, marginTop: 2 },
  batchInfoText: { fontSize: 12, color: BRAND_MUTED, textAlign: "right" },

  batchActions: { flexDirection: "row", alignItems: "center", gap: 6, marginLeft: 8 },
  qtyControl: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: BRAND_BLUE_SOFT,
    borderRadius: 999,
    paddingHorizontal: 6,
    paddingVertical: 2,
    gap: 4,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  qtyButton: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0284C7",
  },
  qtyButtonText: { color: "#FFF", fontSize: 14, fontWeight: "700" },
  qtyValue: { minWidth: 18, textAlign: "center", fontSize: 13, fontWeight: "600", color: "#0369A1" },

  batchIconButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },

  addCard: {
    marginTop: 12,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    paddingHorizontal: 12,
    paddingVertical: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 12,
  },
  addIconCircle: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },
  addTitle: { fontSize: 15, fontWeight: "600", color: BRAND_TEXT, textAlign: "right" },
  addSubtitle: { fontSize: 12, color: BRAND_MUTED, marginTop: 2, textAlign: "right" },
});
