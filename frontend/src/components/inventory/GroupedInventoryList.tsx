import React, { useState, useRef } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  Pressable,
  TouchableOpacity,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { InventoryItem } from "@/src/context/inventory-context";

type GroupedInventory = {
  key: string;
  name: string;
  category: InventoryItem["category"];
  totalQuantity: number;
  items: InventoryItem[];
};

const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BLUE_SOFT = "#F0FAFF";

type Props = {
  groupedItems: GroupedInventory[];
  searchQuery: string;
  onChangeQty: (id: string, delta: number) => void;
  onEditItem: (item: InventoryItem) => void;
  onDeleteItem: (id: string) => void;
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
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(
    {}
  );
  const listRef = useRef<FlatList<GroupedInventory>>(null);
  const isSearching = searchQuery.trim().length >= 2;

  const toggleGroup = (groupKey: string) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupKey]: !prev[groupKey],
    }));
  };

  return (
    <FlatList
      ref={listRef}
      data={groupedItems}
      keyExtractor={(group) => group.key}
      contentContainerStyle={styles.listContent}
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="none"
      removeClippedSubviews={false}
      maintainVisibleContentPosition={{
        minIndexForVisible: 1,
        autoscrollToTopThreshold: 40,
      }}
      ListEmptyComponent={
        <Text style={styles.emptyText}>
          לא נמצאו פריטים בקטגוריה / חיפוש הזה.
        </Text>
      }
      renderItem={({ item: group }) => (
        <GroupedInventoryRow
          group={group}
          expanded={isSearching ? false : !!expandedGroups[group.key]}
          onToggle={() => {
            if (isSearching) return;
            toggleGroup(group.key);
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
            <Text style={styles.addSubtitle}>
              הוספת פריט נוסף למלאי שלך, לפי האזור הנבחר.
            </Text>
          </View>
        </TouchableOpacity>
      }
    />
  );
};

type RowProps = {
  group: GroupedInventory;
  expanded: boolean;
  onToggle: () => void;
  onChangeQty: (id: string, delta: number) => void;
  onEditItem: (item: InventoryItem) => void;
  onDeleteItem: (id: string) => void;
};

const GroupedInventoryRow: React.FC<RowProps> = ({
  group,
  expanded,
  onToggle,
  onChangeQty,
  onEditItem,
  onDeleteItem,
}) => {
  const categoryLabel =
    group.category === "fridge"
      ? "מקרר"
      : group.category === "freezer"
      ? "מקפיא"
      : group.category === "pantry"
      ? "מזווה"
      : group.category === "cleaning supplies"
      ? "חומרי ניקוי"
      : "אחר";

  const categoryColor =
    group.category === "fridge"
      ? "#0284C7"
      : group.category === "freezer"
      ? "#6366F1"
      : group.category === "pantry"
      ? "#F97316"
      : group.category === "cleaning supplies"
      ? "#10B981"
      : "#6B7280";

  return (
    <View style={styles.groupCard}>
      <View style={styles.itemRow}>
        <View style={[styles.itemStrip, { backgroundColor: categoryColor }]} />
        <Pressable style={styles.itemMain} onPress={onToggle}>
          <View style={styles.itemHeaderRow}>
            <Text style={styles.itemName}>{group.name}</Text>

            <View style={styles.groupHeaderRight}>
              <Text style={styles.groupTotalQtyText}>
                סה״כ x{group.totalQuantity}
              </Text>
              <Ionicons
                name={expanded ? "chevron-up" : "chevron-down"}
                size={18}
                color="#0369A1"
              />
            </View>
          </View>

          <View style={styles.itemMetaRow}>
            <View style={styles.itemMetaGroup}>
              <Ionicons
                name="location-outline"
                size={14}
                color={BRAND_MUTED}
              />
              <Text style={styles.itemMetaText}>{categoryLabel}</Text>
            </View>
            <Text style={styles.groupCountText}>
              {group.items.length} רשומות
            </Text>
          </View>
        </Pressable>
      </View>

      {expanded && (
        <View style={styles.groupChildrenContainer}>
          {group.items
            .slice()
            .sort((a: any, b: any) =>
              (a.expiresAt ?? "").localeCompare(b.expiresAt ?? "")
            )
            .map((item: any) => {
              const showOriginal =
                item.originalName &&
                item.originalName.trim() &&
                item.originalName !== group.name;

              return (
                <View key={item.id} style={styles.batchRow}>
                  <View style={styles.batchInfo}>
                    <View style={styles.batchTextCol}>
                      {showOriginal ? (
                        <Text style={styles.batchOriginalText} numberOfLines={1}>
                          {item.originalName}
                        </Text>
                      ) : null}

                      <View style={styles.batchDateRow}>
                        <Ionicons
                          name="time-outline"
                          size={14}
                          color={BRAND_MUTED}
                        />
                        <Text style={styles.batchInfoText}>
                          {item.expiresAt
                            ? `תוקף: ${item.expiresAt}`
                            : "ללא תאריך תוקף"}
                        </Text>
                      </View>
                    </View>
                  </View>

                  <View style={styles.batchActions}>
                    <View style={styles.qtyControl}>
                      <TouchableOpacity
                        style={styles.qtyButton}
                        onPress={() => onChangeQty(item.id, -1)}
                      >
                        <Text style={styles.qtyButtonText}>−</Text>
                      </TouchableOpacity>
                      <Text style={styles.qtyValue}>{item.quantity}</Text>
                      <TouchableOpacity
                        style={styles.qtyButton}
                        onPress={() => onChangeQty(item.id, 1)}
                      >
                        <Text style={styles.qtyButtonText}>+</Text>
                      </TouchableOpacity>
                    </View>

                    <TouchableOpacity
                      style={styles.batchIconButton}
                      onPress={() => onEditItem(item)}
                    >
                      <Ionicons
                        name="create-outline"
                        size={18}
                        color="#0369A1"
                      />
                    </TouchableOpacity>

                    <TouchableOpacity
                      style={styles.batchIconButton}
                      onPress={() => onDeleteItem(item.id)}
                    >
                      <Ionicons
                        name="trash-outline"
                        size={18}
                        color="#DC2626"
                      />
                    </TouchableOpacity>
                  </View>
                </View>
              );
            })}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 40,
    gap: 8,
  },
  emptyText: {
    textAlign: "center",
    marginTop: 32,
    color: BRAND_MUTED,
    fontSize: 14,
  },
  groupCard: { marginBottom: 8 },
  groupHeaderRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  groupTotalQtyText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#0369A1",
  },
  groupCountText: { fontSize: 12, color: BRAND_MUTED },
  groupChildrenContainer: {
    marginHorizontal: 10,
    marginTop: 4,
    marginBottom: 2,
    borderLeftWidth: 1,
    borderLeftColor: "#E5E7EB",
    paddingLeft: 8,
    gap: 4,
  },

  batchRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 6,
  },

  batchInfo: {
    flex: 1,
    alignItems: "flex-end",
  },

  batchTextCol: {
    alignItems: "flex-end",
    justifyContent: "center",
    flex: 1,
  },

  batchDateRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    marginTop: 2,
  },

  batchInfoText: {
    fontSize: 12,
    color: BRAND_MUTED,
    textAlign: "right",
  },

  batchOriginalText: {
    fontSize: 12,
    color: BRAND_TEXT,
    fontWeight: "700",
    textAlign: "right",
  },

  batchActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginLeft: 8,
  },

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
  },
  itemName: {
    flex: 1,
    fontSize: 15,
    fontWeight: "600",
    textAlign: "right",
    marginLeft: 8,
    color: BRAND_TEXT,
  },
  itemMetaRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    marginTop: 4,
  },
  itemMetaGroup: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 4,
  },
  itemMetaText: { fontSize: 12, color: BRAND_MUTED },

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
  qtyButtonText: {
    color: "#FFF",
    fontSize: 14,
    fontWeight: "700",
  },
  qtyValue: {
    minWidth: 18,
    textAlign: "center",
    fontSize: 13,
    fontWeight: "600",
    color: "#0369A1",
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
  addTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: BRAND_TEXT,
    textAlign: "right",
  },
  addSubtitle: {
    fontSize: 12,
    color: BRAND_MUTED,
    marginTop: 2,
    textAlign: "right",
  },
});
