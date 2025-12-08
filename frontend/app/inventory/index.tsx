// frontend/app/inventory/index.tsx
import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  Alert,
  Modal,
  Pressable,
  Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import {
  useInventory,
  Category,
  InventoryItem,
} from "../inventory-store";
import DateTimePicker from "@react-native-community/datetimepicker";

export type CategoryKey = Category | "all";

const TABS = [
  { key: "fridge", label: "מקרר" },
  { key: "freezer", label: "מקפיא" },
  { key: "pantry", label: "מזווה" },
  { key: "all", label: "הכול" },
] as const;

type StatusFilter = "all" | "soon" | "expired";

type InventoryScreenBaseProps = {
  initialCategory: CategoryKey;
  hideTabs?: boolean;
  title: string;
};

export function InventoryScreenBase({
  initialCategory,
  hideTabs,
  title,
}: InventoryScreenBaseProps) {
  const { items, updateItem, removeItem } = useInventory();

  const [selectedTab, setSelectedTab] = useState<CategoryKey>(initialCategory);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>("all");

  // מצב לעריכת מוצר בפופ-אפ
  const [editItem, setEditItem] = useState<InventoryItem | null>(null);
  const [editName, setEditName] = useState("");
  const [editQty, setEditQty] = useState("");
  const [editExpiresAt, setEditExpiresAt] = useState<Date | undefined>();
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [showEditDatePicker, setShowEditDatePicker] = useState(false);

  const effectiveCategory: CategoryKey = hideTabs ? initialCategory : selectedTab;

  const { filteredItems, stats } = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let fridge = 0;
    let freezer = 0;
    let pantry = 0;
    let expiringSoon = 0;

    const filtered = items.filter((item) => {
      // קטגוריה
      if (effectiveCategory !== "all" && item.category !== effectiveCategory) {
        return false;
      }

      // חיפוש
      if (search && !item.name.includes(search)) {
        return false;
      }

      // סטטוס תוקף
      if (statusFilter !== "all") {
        if (!item.expiresAt) {
          // בלי תאריך תוקף – מופיע רק ב"הכול"
          return false;
        }
        const exp = new Date(item.expiresAt);
        exp.setHours(0, 0, 0, 0);
        const diffDays =
          (exp.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);

        if (statusFilter === "soon") {
          // 0–3 ימים קדימה
          if (!(diffDays >= 0 && diffDays <= 3)) return false;
        } else if (statusFilter === "expired") {
          if (!(diffDays < 0)) return false;
        }
      }

      return true;
    });

    // סטטיסטיקות כלליות
    items.forEach((item) => {
      if (item.category === "fridge") fridge++;
      if (item.category === "freezer") freezer++;
      if (item.category === "pantry") pantry++;

      if (item.expiresAt) {
        const exp = new Date(item.expiresAt);
        exp.setHours(0, 0, 0, 0);
        const diffMs = exp.getTime() - today.getTime();
        const diffDays = diffMs / (1000 * 60 * 60 * 24);
        if (diffDays >= 0 && diffDays <= 3) {
          expiringSoon++;
        }
      }
    });

    return {
      filteredItems: filtered,
      stats: {
        total: items.length,
        fridge,
        freezer,
        pantry,
        expiringSoon,
      },
    };
  }, [items, effectiveCategory, search, statusFilter]);

  // עדכון כמות עם + / −
  const handleChangeQty = (id: string, delta: number) => {
    const current = items.find((it) => it.id === id);
    if (!current) return;
    const next = current.quantity + delta;
    if (next < 1) return; // לא יורדים מתחת ל־1, למחיקה יש כפתור נפרד
    updateItem(id, { quantity: next });
  };

  // מחיקת מוצר
  const handleDelete = (id: string) => {
    const current = items.find((it) => it.id === id);
    Alert.alert(
      "מחיקת מוצר",
      `למחוק את "${current?.name ?? "המוצר"}" מהמלאי?`,
      [
        { text: "ביטול", style: "cancel" },
        {
          text: "מחק",
          style: "destructive",
          onPress: () => removeItem(id),
        },
      ]
    );
  };

  // פתיחת מודאל עריכה
  const openEditModal = (item: InventoryItem) => {
    setEditItem(item);
    setEditName(item.name);
    setEditQty(String(item.quantity));
    setEditExpiresAt(item.expiresAt ? new Date(item.expiresAt) : undefined);
    setEditModalVisible(true);
  };

  const closeEditModal = () => {
    setEditModalVisible(false);
    setShowEditDatePicker(false);
  };

  const onChangeEditDate = (_: any, selectedDate?: Date) => {
    if (Platform.OS === "android") {
      if (selectedDate) setEditExpiresAt(selectedDate);
      setShowEditDatePicker(false);
    } else {
      if (selectedDate) setEditExpiresAt(selectedDate);
    }
  };

  const saveEdit = () => {
    if (!editItem) return;

    if (!editName.trim()) {
      Alert.alert("שגיאה", "חייב להיות שם מוצר");
      return;
    }
    const qty = parseInt(editQty, 10);
    if (isNaN(qty) || qty <= 0) {
      Alert.alert("שגיאה", "כמות חייבת להיות מספר חיובי");
      return;
    }

    const formattedExpires = editExpiresAt
      ? editExpiresAt.toISOString().slice(0, 10)
      : undefined;

    updateItem(editItem.id, {
      name: editName.trim(),
      quantity: qty,
      expiresAt: formattedExpires,
    });

    closeEditModal();
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* Header */}
      <View style={styles.headerRow}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="chevron-back" size={24} />
        </TouchableOpacity>
        <Text style={styles.title}>{title}</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Summary card */}
      <View style={styles.summaryCard}>
        <View style={styles.summaryHeaderRow}>
          <Text style={styles.summaryTitle}>סיכום המלאי</Text>
          <View style={styles.summaryBadge}>
            <Ionicons name="cube-outline" size={16} />
            <Text style={styles.summaryBadgeText}>{stats.total} מוצרים</Text>
          </View>
        </View>
        <View style={styles.summaryRow}>
          <SummaryChip label="מקרר" value={stats.fridge} color="#6B8FB3" />
          <SummaryChip label="מקפיא" value={stats.freezer} color="#7BA99C" />
          <SummaryChip label="מזווה" value={stats.pantry} color="#C4956D" />
        </View>
        <View style={styles.summaryFooterRow}>
          <Ionicons name="warning-outline" size={16} />
          <Text style={styles.summaryFooterText}>
            {stats.expiringSoon > 0
              ? `${stats.expiringSoon} מוצרים עם תוקף קרוב`
              : "אין כרגע מוצרים עם תוקף קרוב"}
          </Text>
        </View>
      </View>

      {/* Tabs לפי אזור */}
      {!hideTabs && (
        <View style={styles.tabsContainer}>
          <View style={styles.tabsRow}>
            {TABS.map((tab) => {
              const active = tab.key === selectedTab;
              return (
                <TouchableOpacity
                  key={tab.key}
                  style={[styles.tab, active && styles.tabActive]}
                  onPress={() => setSelectedTab(tab.key as CategoryKey)}
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

      {/* Search */}
      <View style={styles.searchBox}>
        <Ionicons name="search-outline" size={18} />
        <TextInput
          style={styles.searchInput}
          placeholder="חיפוש לפי שם מוצר..."
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {/* פילטר תוקף */}
      <View style={styles.filterRow}>
        <View style={styles.filtersLeft}>
          <FilterChip
            label="הכול"
            active={statusFilter === "all"}
            onPress={() => setStatusFilter("all")}
          />
          <FilterChip
            label="תוקף קרוב"
            active={statusFilter === "soon"}
            onPress={() => setStatusFilter("soon")}
            style={{ marginLeft: 8 }}
          />
          <FilterChip
            label="פג תוקף"
            active={statusFilter === "expired"}
            onPress={() => setStatusFilter("expired")}
            style={{ marginLeft: 8 }}
          />
        </View>

        <Text style={styles.sortLabel}>מיון לפי:</Text>
      </View>

      {/* List */}
      <FlatList
        data={filteredItems}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <Text style={styles.emptyText}>
            לא נמצאו פריטים בקטגוריה / חיפוש הזה.
          </Text>
        }
        renderItem={({ item }) => (
          <InventoryRow
            item={item}
            onEdit={() => openEditModal(item)}
            onChangeQty={(delta) => handleChangeQty(item.id, delta)}
            onDelete={() => handleDelete(item.id)}
          />
        )}
      />

      {/* כפתור הוספה */}
      <TouchableOpacity
        style={styles.addButton}
        onPress={() => router.push("/add-item")}
      >
        <Ionicons name="add" size={18} color="#FFF" />
        <Text style={styles.addButtonText}>הוספת מוצר</Text>
      </TouchableOpacity>

      {/* MODAL עריכת מוצר */}
      <Modal
        visible={editModalVisible}
        transparent
        animationType="slide"
        onRequestClose={closeEditModal}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>עריכת מוצר</Text>

            <Text style={styles.modalLabel}>שם המוצר</Text>
            <TextInput
              style={styles.modalInput}
              value={editName}
              onChangeText={setEditName}
              placeholder="שם המוצר"
            />

            <Text style={styles.modalLabel}>כמות</Text>
            <TextInput
              style={styles.modalInput}
              value={editQty}
              onChangeText={setEditQty}
              keyboardType="numeric"
              placeholder="כמות"
            />

            <Text style={styles.modalLabel}>תאריך תוקף</Text>
            <TouchableOpacity
              style={styles.modalDateButton}
              onPress={() => setShowEditDatePicker(true)}
            >
              <Ionicons name="time-outline" size={18} color="#374151" />
              <Text style={styles.modalDateButtonText}>
                {editExpiresAt
                  ? editExpiresAt.toLocaleDateString("he-IL")
                  : "בחרי תאריך (לא חובה)"}
              </Text>
            </TouchableOpacity>

          {showEditDatePicker && (
            <View style={styles.datePickerWrapper}>
              <DateTimePicker
                value={editExpiresAt || new Date()}
                mode="date"
                display={Platform.OS === "ios" ? "spinner" : "default"}
                onChange={onChangeEditDate}
                locale="he-IL"
                minimumDate={new Date()}
                {...(Platform.OS === "ios" ? { themeVariant: "dark" } : {})}
              />
            </View>
          )}


            <View style={styles.modalButtonsRow}>
              <TouchableOpacity
                style={styles.modalButton}
                onPress={closeEditModal}
              >
                <Text style={styles.modalButtonText}>ביטול</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalButton, styles.modalButtonPrimary]}
                onPress={saveEdit}
              >
                <Text
                  style={[
                    styles.modalButtonText,
                    styles.modalButtonTextPrimary,
                  ]}
                >
                  שמירה
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

/* ---------- SMALL COMPONENTS ---------- */

function SummaryChip({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <View style={[styles.summaryChip, { backgroundColor: color + "22" }]}>
      <View style={[styles.summaryDot, { backgroundColor: color }]} />
      <Text style={styles.summaryChipLabel}>{label}</Text>
      <Text style={styles.summaryChipValue}>{value}</Text>
    </View>
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
    >
      <Text
        style={[styles.filterChipText, active && styles.filterChipTextActive]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

function InventoryRow({
  item,
  onEdit,
  onChangeQty,
  onDelete,
}: {
  item: InventoryItem;
  onEdit: () => void;
  onChangeQty: (delta: number) => void;
  onDelete: () => void;
}) {
  const categoryColor =
    item.category === "fridge"
      ? "#6B8FB3"
      : item.category === "freezer"
      ? "#7BA99C"
      : "#C4956D";

  return (
    <View style={styles.itemRow}>
      {/* Left colored strip */}
      <View style={[styles.itemStrip, { backgroundColor: categoryColor }]} />

      {/* תוכן הפריט – לחיצה פותחת עריכה */}
      <Pressable style={styles.itemMain} onPress={onEdit}>
        <View style={styles.itemHeaderRow}>
          <Text style={styles.itemName}>{item.name}</Text>

          {/* שליטה בכמות */}
          <View style={styles.qtyControl}>
            <TouchableOpacity
              style={styles.qtyButton}
              onPress={() => onChangeQty(-1)}
            >
              <Text style={styles.qtyButtonText}>−</Text>
            </TouchableOpacity>
            <Text style={styles.qtyValue}>{item.quantity}</Text>
            <TouchableOpacity
              style={styles.qtyButton}
              onPress={() => onChangeQty(1)}
            >
              <Text style={styles.qtyButtonText}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.itemMetaRow}>
          <View style={styles.itemMetaGroup}>
            <Ionicons name="location-outline" size={14} />
            <Text style={styles.itemMetaText}>
              {item.category === "fridge"
                ? "מקרר"
                : item.category === "freezer"
                ? "מקפיא"
                : "מזווה"}
            </Text>
          </View>

          {item.expiresAt && (
            <View style={styles.itemMetaGroup}>
              <Ionicons name="time-outline" size={14} />
              <Text style={styles.itemMetaText}>תוקף: {item.expiresAt}</Text>
            </View>
          )}
        </View>
      </Pressable>

      {/* כפתור מחיקה */}
      <TouchableOpacity style={styles.deleteIconWrapper} onPress={onDelete}>
        <Ionicons name="trash-outline" size={18} color="#DC2626" />
      </TouchableOpacity>
    </View>
  );
}

// זה המסך של "רשימת מוצרים כוללת"
export default function InventoryScreen() {
  return (
    <InventoryScreenBase initialCategory="all" title="מלאי" hideTabs={false} />
  );
}

/* ---------- STYLES ---------- */

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F3F5F9",
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
    justifyContent: "space-between",
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
  },

  summaryCard: {
    marginHorizontal: 16,
    marginTop: 8,
    marginBottom: 8,
    padding: 16,
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 2,
  },
  summaryHeaderRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 10,
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: "600",
  },
  summaryBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 16,
    backgroundColor: "#F0F2F8",
  },
  summaryBadgeText: {
    fontSize: 12,
  },
  summaryRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    gap: 8,
    marginBottom: 10,
  },
  summaryChip: {
    flex: 1,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 12,
  },
  summaryDot: {
    width: 8,
    height: 8,
    borderRadius: 999,
  },
  summaryChipLabel: {
    fontSize: 13,
    fontWeight: "500",
  },
  summaryChipValue: {
    fontSize: 15,
    fontWeight: "700",
  },
  summaryFooterRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    marginTop: 4,
  },
  summaryFooterText: {
    fontSize: 12,
    color: "#555",
  },

  tabsContainer: {
    paddingHorizontal: 16,
    paddingBottom: 4,
  },
  tabsRow: {
    flexDirection: "row-reverse",
    backgroundColor: "#E1E5F0",
    borderRadius: 999,
    padding: 4,
    gap: 4,
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
  },
  tabText: {
    fontSize: 13,
    color: "#555",
  },
  tabTextActive: {
    color: "#111",
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
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 1,
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
  },

  filterRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    marginTop: 6,
    marginBottom: 4,
  },
  filtersLeft: {
    flexDirection: "row",
    alignItems: "center",
  },
  sortLabel: {
    fontSize: 13,
    color: "#374151",
    fontWeight: "600",
    textAlign: "right",
  },
  filterChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "#E5E7EB",
  },
  filterChipActive: {
    backgroundColor: "#111827",
  },
  filterChipText: {
    fontSize: 12,
    color: "#4B5563",
  },
  filterChipTextActive: {
    color: "#FFFFFF",
    fontWeight: "600",
  },

  listContent: {
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 90,
    gap: 8,
  },
  emptyText: {
    textAlign: "center",
    marginTop: 32,
    color: "#777",
    fontSize: 14,
  },

  itemRow: {
    flexDirection: "row",
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOpacity: 0.03,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 1,
    overflow: "hidden",
  },
  itemStrip: {
    width: 4,
  },
  itemMain: {
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
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
  },

  qtyControl: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#F3F4F6",
    borderRadius: 999,
    paddingHorizontal: 6,
    paddingVertical: 2,
    gap: 4,
  },
  qtyButton: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#111827",
  },
  qtyButtonText: {
    color: "#FFF",
    fontSize: 14,
    fontWeight: "700",
    lineHeight: 16,
  },
  qtyValue: {
    minWidth: 18,
    textAlign: "center",
    fontSize: 13,
    fontWeight: "600",
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
  itemMetaText: {
    fontSize: 12,
    color: "#666",
  },

  deleteIconWrapper: {
    width: 40,
    alignItems: "center",
    justifyContent: "center",
  },

  addButton: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 16,
    backgroundColor: "#111827",
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: 8,
  },
  addButtonText: {
    color: "#FFF",
    fontSize: 15,
    fontWeight: "600",
  },

  /* MODAL */
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.35)",
    justifyContent: "center",
    alignItems: "center",
    padding: 16,
  },
  modalCard: {
    width: "100%",
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    padding: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "700",
    textAlign: "right",
    marginBottom: 12,
  },
  modalLabel: {
    textAlign: "right",
    marginTop: 8,
    marginBottom: 4,
    fontSize: 13,
  },
  modalInput: {
    borderRadius: 10,
    backgroundColor: "#F9FAFB",
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  modalDateButton: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: "#F9FAFB",
  },
  modalDateButtonText: {
    fontSize: 14,
    color: "#374151",
  },
  modalButtonsRow: {
    flexDirection: "row-reverse",
    gap: 8,
    marginTop: 16,
  },
  modalButton: {
    flex: 1,
    borderRadius: 999,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#E5E7EB",
  },
  modalButtonPrimary: {
    backgroundColor: "#111827",
  },
  modalButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#111827",
  },
  modalButtonTextPrimary: {
    color: "#FFFFFF",
  },
  datePickerWrapper: {
    marginTop: 8,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#111827", // רקע כהה כדי שהספינר יבלוט
    paddingVertical: 8,
    height: 220, // חשוב: גובה קבוע כדי שהספינר יהיה באמת נראה
  },
});
