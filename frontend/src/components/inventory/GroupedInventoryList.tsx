import React, { useMemo, useState } from "react";
import { View, Text, SectionList, StyleSheet, Pressable, TouchableOpacity } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";

import type { InventoryRow, ProductGroupVM, LocationSectionVM } from "@/src/components/inventory/inventory.utils";
import { locationColor, locationLabel } from "@/src/components/inventory/inventory.utils";
import { COLORS } from "./filters.constants";

type Props = {
  groupedItems: LocationSectionVM[];
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
  const isSearching = searchQuery.trim().length >= 2;

  const toggle = (key: string) => {
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const sections = useMemo(() => {
    return groupedItems.map(sec => ({
      title: sec.label,
      location: sec.location,
      data: sec.items
    }));
  }, [groupedItems]);

  return (
    <SectionList
      sections={sections}
      keyExtractor={(g) => g.key}
      contentContainerStyle={styles.listContent}
      stickySectionHeadersEnabled={true}
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="none"
      removeClippedSubviews={false}
      ListEmptyComponent={
        <View style={styles.emptyContainer}>
          <Ionicons name="cube-outline" size={48} color={COLORS.BORDER} />
          <Text style={styles.emptyText}>לא נמצאו פריטים במלאי.</Text>
        </View>
      }
      renderSectionHeader={({ section: { title, location } }) => (
        <View style={styles.sectionHeaderContainer}>
          <View style={[styles.sectionHeaderInner, { backgroundColor: locationColor(location as any) + "10" }]}>
            <Ionicons name={getCategoryIcon(location as any)} size={16} color={locationColor(location as any)} />
            <Text style={[styles.sectionHeaderText, { color: locationColor(location as any) }]}>{title}</Text>
          </View>
        </View>
      )}
      renderItem={({ item: g }) => (
        <ProductGroupCard
          group={g}
          expanded={isSearching ? true : !!expanded[g.key]}
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
        <TouchableOpacity style={styles.addCard} onPress={onAddItem} activeOpacity={0.7}>
          <LinearGradient colors={["#F8FAFC", "#F1F5F9"]} style={styles.addCardInner}>
            <View style={styles.addIconCircle}>
              <Ionicons name="add" size={24} color={COLORS.ACCENT} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.addTitle}>הוספת מוצר חדש</Text>
              <Text style={styles.addSubtitle}>הוסיפי פריט נוסף למלאי שלך בצורה פשוטה.</Text>
            </View>
          </LinearGradient>
        </TouchableOpacity>
      }
    />
  );
};

function getCategoryIcon(loc: any): keyof typeof Ionicons.glyphMap {
  switch (loc) {
    case "fridge": return "snow-outline";
    case "freezer": return "cube-outline";
    case "pantry": return "restaurant-outline";
    case "cleaning": return "water-outline";
    default: return "ellipsis-horizontal-outline";
  }
}


function ProductGroupCard(props: {
  group: ProductGroupVM;
  expanded: boolean;
  onToggle: () => void;
  onChangeQty: (itemId: string, delta: number) => void;
  onEditItem: (item: InventoryRow) => void;
  onDeleteItem: (itemId: string) => void;
}) {
  const { group, expanded, onToggle, onChangeQty, onEditItem, onDeleteItem } = props;

  const mainLocationColor = useMemo(() => {
    if (group.sections.length === 1) return locationColor(group.sections[0].location);
    return COLORS.ACCENT;
  }, [group.sections]);

  return (
    <View style={[styles.groupCard, expanded && styles.groupCardExpanded]}>
      <Pressable 
        style={({ pressed }) => [styles.cardHeader, pressed && { backgroundColor: COLORS.BG_DIM }]} 
        onPress={onToggle}
      >
        <View style={[styles.accentStrip, { backgroundColor: mainLocationColor }]} />
        
        <View style={styles.headerContent}>
          <View style={styles.titleRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.itemName} numberOfLines={1}>{group.title}</Text>
              {group.subtitle ? (
                <Text style={styles.itemSubtitle} numberOfLines={1}>{group.subtitle}</Text>
              ) : null}
            </View>
            <View style={styles.qtyBadge}>
              <Text style={styles.qtyBadgeText}>x{group.totalQuantity}</Text>
            </View>
          </View>

          <View style={styles.metaRow}>
            <View style={styles.metaItem}>
              <Ionicons name="layers-outline" size={14} color={COLORS.BRAND_MUTED} />
              <Text style={styles.metaText}>{countItems(group)} רשומות</Text>
            </View>
            <View style={styles.metaItem}>
              <Ionicons name="location-outline" size={14} color={COLORS.BRAND_MUTED} />
              <Text style={styles.metaText}>
                {group.sections.length === 1 ? locationLabel(group.sections[0].location) : `${group.sections.length} אזורים`}
              </Text>
            </View>
            <Ionicons 
              name={expanded ? "chevron-up" : "chevron-down"} 
              size={18} 
              color={COLORS.BRAND_MUTED} 
              style={{ marginLeft: "auto" }}
            />
          </View>
        </View>
      </Pressable>

      {expanded && (
        <View style={styles.childrenContainer}>
          {group.sections.map((sec) => (
            <View key={sec.location} style={styles.sectionBlock}>
              <View style={styles.sectionHeader}>
                <View style={[styles.sectionIndicator, { backgroundColor: locationColor(sec.location) }]} />
                <Text style={styles.sectionTitle}>{locationLabel(sec.location)}</Text>
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

  const statusConfig = useMemo(() => {
    switch (item.status) {
      case "EXPIRED":
        return { label: "פג תוקף", bg: COLORS.DANGER_SOFT, text: COLORS.DANGER };
      case "GOING_TO_EXPIRE":
        return { label: "תוקף קרוב", bg: COLORS.WARNING_SOFT, text: COLORS.WARNING };
      default:
        return item.expirationDate ? { label: "תקין", bg: COLORS.SUCCESS_SOFT, text: COLORS.SUCCESS } : null;
    }
  }, [item.status, item.expirationDate]);

  return (
    <View style={styles.batchRow}>
      <View style={styles.batchInfo}>
        <View style={styles.batchDateRow}>
          <Ionicons name="calendar-outline" size={14} color={COLORS.BRAND_MUTED} />
          <Text style={styles.batchDateText}>
            {item.expirationDate ? item.expirationDate : "ללא תאריך תוקף"}
          </Text>
        </View>
        {statusConfig && (
          <View style={[styles.statusBadge, { backgroundColor: statusConfig.bg }]}>
            <Text style={[styles.statusBadgeText, { color: statusConfig.text }]}>{statusConfig.label}</Text>
          </View>
        )}
      </View>

      <View style={styles.batchActions}>
        <View style={styles.qtyControl}>
          <TouchableOpacity style={styles.qtyBtn} onPress={() => onChangeQty(item.itemId, -1)}>
            <Ionicons name="remove" size={16} color="#FFF" />
          </TouchableOpacity>
          <Text style={styles.qtyValueText}>{item.quantity}</Text>
          <TouchableOpacity style={styles.qtyBtn} onPress={() => onChangeQty(item.itemId, 1)}>
            <Ionicons name="add" size={16} color="#FFF" />
          </TouchableOpacity>
        </View>

        <View style={styles.actionButtons}>
          <TouchableOpacity style={styles.iconBtn} onPress={() => onEditItem(item)}>
            <Ionicons name="pencil-sharp" size={16} color={COLORS.ACCENT} />
          </TouchableOpacity>
          <TouchableOpacity style={[styles.iconBtn, { backgroundColor: COLORS.DANGER_SOFT }]} onPress={() => onDeleteItem(item.itemId)}>
            <Ionicons name="trash-outline" size={16} color={COLORS.DANGER} />
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  listContent: { paddingHorizontal: 16, paddingTop: 4, paddingBottom: 60 },
  sectionHeaderContainer: {
    backgroundColor: COLORS.BG_DIM,
    paddingTop: 16,
    paddingBottom: 8,
  },
  sectionHeaderInner: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  sectionHeaderText: {
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  emptyContainer: { alignItems: "center", justifyContent: "center", marginTop: 60, opacity: 0.5 },
  emptyText: { marginTop: 12, fontSize: 16, color: COLORS.BRAND_MUTED, fontWeight: "600" },

  groupCard: {
    backgroundColor: COLORS.CARD_BG,
    borderRadius: 20,
    marginBottom: 12,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: COLORS.BORDER,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 2,
  },
  groupCardExpanded: {
    shadowOpacity: 0.08,
    shadowRadius: 15,
    elevation: 4,
    borderColor: COLORS.ACCENT + "40",
  },
  cardHeader: {
    flexDirection: "row",
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  accentStrip: {
    position: "absolute",
    right: 0,
    top: 0,
    bottom: 0,
    width: 4,
  },
  headerContent: { flex: 1 },
  titleRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 8 },
  itemName: { fontSize: 15, fontWeight: "800", color: COLORS.BRAND_TEXT, textAlign: "right" },
  itemSubtitle: { fontSize: 12, color: COLORS.BRAND_MUTED, textAlign: "right", marginTop: 2 },
  
  qtyBadge: {
    backgroundColor: COLORS.BRAND_BLUE_SOFT,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.ACCENT + "20",
  },
  qtyBadgeText: { color: COLORS.ACCENT, fontWeight: "800", fontSize: 13 },

  metaRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  metaItem: { flexDirection: "row", alignItems: "center", gap: 4 },
  metaText: { fontSize: 12, color: COLORS.BRAND_MUTED, fontWeight: "600" },

  childrenContainer: {
    paddingHorizontal: 16,
    paddingBottom: 16,
    backgroundColor: COLORS.BG_DIM,
    borderTopWidth: 1,
    borderTopColor: COLORS.BORDER,
  },
  sectionBlock: { marginTop: 14 },
  sectionHeader: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 8 },
  sectionIndicator: { width: 8, height: 8, borderRadius: 4 },
  sectionTitle: { fontSize: 12, fontWeight: "800", color: COLORS.BRAND_TEXT },

  batchRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 10,
    marginBottom: 6,
    borderWidth: 1,
    borderColor: COLORS.BORDER,
  },
  batchInfo: { flex: 1, alignItems: "flex-start", gap: 6 },
  batchDateRow: { flexDirection: "row", alignItems: "center", gap: 4 },
  batchDateText: { fontSize: 12, color: COLORS.BRAND_TEXT, fontWeight: "600" },
  
  statusBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  statusBadgeText: { fontSize: 11, fontWeight: "800" },

  batchActions: { alignItems: "center", gap: 10 },
  qtyControl: { 
    flexDirection: "row", 
    alignItems: "center", 
    backgroundColor: COLORS.BG_DIM,
    borderRadius: 10,
    padding: 2,
    gap: 8,
  },
  qtyBtn: { 
    width: 24, 
    height: 24, 
    borderRadius: 8, 
    backgroundColor: COLORS.ACCENT, 
    alignItems: "center", 
    justifyContent: "center" 
  },
  qtyValueText: { fontSize: 13, fontWeight: "800", color: COLORS.BRAND_TEXT, minWidth: 20, textAlign: "center" },

  actionButtons: { flexDirection: "row", gap: 8 },
  iconBtn: {
    width: 32,
    height: 32,
    borderRadius: 10,
    backgroundColor: COLORS.BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },

  addCard: { marginTop: 12, borderRadius: 20, overflow: "hidden" },
  addCardInner: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    gap: 16,
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: COLORS.BORDER,
    borderRadius: 20,
  },
  addIconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: COLORS.ACCENT,
    shadowOpacity: 0.1,
    shadowRadius: 5,
    elevation: 2,
  },
  addTitle: { fontSize: 15, fontWeight: "800", color: COLORS.BRAND_TEXT, textAlign: "right" },
  addSubtitle: { fontSize: 11, color: COLORS.BRAND_MUTED, marginTop: 2, textAlign: "right" },
});
