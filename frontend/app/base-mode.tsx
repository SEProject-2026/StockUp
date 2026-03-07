// frontend/app/base-mode.tsx
import React, { useEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  Modal,
  Alert,
  ActivityIndicator,
  Pressable,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";

import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";

const BRAND = {
  BG: "#F4F4F4",
  CARD: "#FFFFFF",
  BORDER: "#E5E7EB",
  TEXT: "#111827",
  MUTED: "#6B7280",
  PRIMARY: "#0284C7",
  PRIMARY_SOFT: "#E5F3FF",
  DANGER: "#DC2626",
  NOTE_LINE: "#E8EDF5",
  NOTE_MARGIN: "#D8E6F8",
};

type BaseLocation = "FRIDGE" | "FREEZER" | "PANTRY" | "CLEANING_SUPPLIES" | "OTHER";

type BaseItem = {
  id: string;
  name: string;
  targetQty: number;
  unit?: string;
  location: BaseLocation;
};

type GroupedSection = {
  location: BaseLocation;
  title: string;
  items: BaseItem[];
};

const LOCATIONS: BaseLocation[] = ["FRIDGE", "FREEZER", "PANTRY", "CLEANING_SUPPLIES", "OTHER"];

function normalizeName(s: string) {
  return s.trim().toLowerCase();
}

// ------------------------------
// API placeholders
// ------------------------------
async function apiGetBaseMode(): Promise<BaseItem[]> {
  return [
    { id: "b1", name: "חלב 3%", targetQty: 2, unit: "יח׳", location: "FRIDGE" },
    { id: "b2", name: "ביצים", targetQty: 1, unit: "תבנית", location: "FRIDGE" },
    { id: "b3", name: "קוטג׳", targetQty: 3, unit: "יח׳", location: "FRIDGE" },
    { id: "b4", name: "עוף", targetQty: 1, unit: "יח׳", location: "FREEZER" },
    { id: "b5", name: "אפונה קפואה", targetQty: 2, unit: "יח׳", location: "FREEZER" },
    { id: "b6", name: "אורז", targetQty: 1, unit: "יח׳", location: "PANTRY" },
    { id: "b7", name: "פסטה", targetQty: 2, unit: "יח׳", location: "PANTRY" },
    { id: "b8", name: "נייר טואלט", targetQty: 2, unit: "חבילות", location: "CLEANING_SUPPLIES" },
    { id: "b9", name: "סבון כלים", targetQty: 1, unit: "יח׳", location: "CLEANING_SUPPLIES" },
  ];
}

async function apiCreateBaseItem(item: Omit<BaseItem, "id">): Promise<BaseItem> {
  return {
    id: `base_${Date.now()}`,
    ...item,
  };
}

async function apiUpdateBaseItem(id: string, patch: Partial<BaseItem>): Promise<void> {
  return;
}

async function apiDeleteBaseItem(id: string): Promise<void> {
  return;
}

// ------------------------------
// Helpers
// ------------------------------
function locationLabel(loc: BaseLocation) {
  switch (loc) {
    case "FRIDGE":
      return "מקרר";
    case "FREEZER":
      return "מקפיא";
    case "PANTRY":
      return "מזווה";
    case "CLEANING_SUPPLIES":
      return "ניקיון";
    default:
      return "אחר";
  }
}

function locationIcon(loc: BaseLocation) {
  switch (loc) {
    case "FRIDGE":
      return "snow-outline";
    case "FREEZER":
      return "snow";
    case "PANTRY":
      return "cube-outline";
    case "CLEANING_SUPPLIES":
      return "sparkles-outline";
    default:
      return "ellipsis-horizontal";
  }
}

function SummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: any;
}) {
  return (
    <View style={styles.summaryCard}>
      <View style={styles.summaryIconWrap}>
        <Ionicons name={icon} size={17} color={BRAND.PRIMARY} />
      </View>

      <View style={{ flex: 1 }}>
        <Text style={styles.summaryTitle}>{title}</Text>
        <Text style={styles.summaryValue}>{value}</Text>
      </View>
    </View>
  );
}

function AddBaseItemModal(props: {
  open: boolean;
  onClose: () => void;
  onAdd: (item: Omit<BaseItem, "id">) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [loc, setLoc] = useState<BaseLocation>("FRIDGE");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    const n = name.trim();
    const q = Number(qty);

    if (!n) {
      Alert.alert("חסר שם מוצר", "אנא הזיני שם מוצר.");
      return;
    }

    if (!Number.isFinite(q) || q <= 0) {
      Alert.alert("כמות לא תקינה", "אנא הזיני מספר חיובי.");
      return;
    }

    try {
      setSubmitting(true);
      await props.onAdd({
        name: n,
        targetQty: q,
        unit: "יח׳",
        location: loc,
      });

      setName("");
      setQty("1");
      setLoc("FRIDGE");
      props.onClose();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal visible={props.open} transparent animationType="fade" onRequestClose={props.onClose}>
      <Pressable style={styles.modalBackdrop} onPress={props.onClose}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <View style={styles.modalHandle} />

          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>הוספת פריט למצב בסיס</Text>
            <TouchableOpacity onPress={props.onClose} style={styles.iconBtn} disabled={submitting}>
              <Ionicons name="close" size={20} color={BRAND.TEXT} />
            </TouchableOpacity>
          </View>

          <Text style={styles.modalSubtitle}>
            הגדירי כמה יחידות באופן אידיאלי צריכות להיות בבית.
          </Text>

          <View style={styles.field}>
            <Text style={styles.label}>שם מוצר</Text>
            <TextInput
              value={name}
              onChangeText={setName}
              placeholder="לדוגמה: קוטג׳"
              placeholderTextColor={BRAND.MUTED}
              style={styles.input}
              textAlign="right"
              editable={!submitting}
            />
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>כמות רצויה</Text>
            <TextInput
              value={qty}
              onChangeText={setQty}
              keyboardType="numeric"
              placeholder="1"
              placeholderTextColor={BRAND.MUTED}
              style={styles.input}
              textAlign="right"
              editable={!submitting}
            />
          </View>

          <Text style={styles.label}>מיקום</Text>
          <View style={styles.locationWrap}>
            {LOCATIONS.map((l) => (
              <TouchableOpacity
                key={l}
                onPress={() => setLoc(l)}
                style={[styles.locationOption, loc === l && styles.locationOptionActive]}
                disabled={submitting}
              >
                <Ionicons
                  name={locationIcon(l) as any}
                  size={16}
                  color={loc === l ? BRAND.PRIMARY : BRAND.MUTED}
                />
                <Text style={[styles.locationOptionText, loc === l && styles.locationOptionTextActive]}>
                  {locationLabel(l)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <PrimaryButton
            title={submitting ? "מוסיף..." : "הוסף פריט"}
            onPress={submit}
            disabled={submitting}
          />
        </Pressable>
      </Pressable>
    </Modal>
  );
}

function NotebookRow({
  item,
  busy,
  onIncrease,
  onDecrease,
  onRemove,
}: {
  item: BaseItem;
  busy: boolean;
  onIncrease: () => void;
  onDecrease: () => void;
  onRemove: () => void;
}) {
  return (
    <View style={[styles.noteRow, busy && { opacity: 0.6 }]}>
      <View style={styles.noteActions}>
        <TouchableOpacity onPress={onRemove} disabled={busy} style={styles.noteIconBtn}>
          <Ionicons name="trash-outline" size={16} color={BRAND.DANGER} />
        </TouchableOpacity>

        <TouchableOpacity onPress={onDecrease} disabled={busy} style={styles.noteIconBtn}>
          <Ionicons name="remove" size={16} color={BRAND.PRIMARY} />
        </TouchableOpacity>

        <View style={styles.noteQtyPill}>
          <Text style={styles.noteQtyText}>{item.targetQty}</Text>
        </View>

        <TouchableOpacity onPress={onIncrease} disabled={busy} style={styles.noteIconBtn}>
          <Ionicons name="add" size={16} color={BRAND.PRIMARY} />
        </TouchableOpacity>
      </View>

      <View style={styles.noteTextWrap}>
        <Text style={styles.noteTitle}>{item.name}</Text>
        <Text style={styles.noteMeta}>{item.unit ?? "יח׳"}</Text>
      </View>
    </View>
  );
}

function LocationSection({
  section,
  busyIds,
  onIncrease,
  onDecrease,
  onRemove,
}: {
  section: GroupedSection;
  busyIds: string[];
  onIncrease: (id: string) => void;
  onDecrease: (id: string) => void;
  onRemove: (id: string) => void;
}) {
  if (section.items.length === 0) return null;

  return (
    <View style={styles.sectionBlock}>
      <View style={styles.locationHeader}>
        <View style={styles.locationHeaderLine} />
        <View style={styles.locationHeaderChip}>
          <Ionicons name={locationIcon(section.location) as any} size={15} color={BRAND.PRIMARY} />
          <Text style={styles.locationHeaderText}>{section.title}</Text>
        </View>
      </View>

      <View style={styles.notebookCard}>
        {section.items.map((item) => (
          <NotebookRow
            key={item.id}
            item={item}
            busy={busyIds.includes(item.id)}
            onIncrease={() => onIncrease(item.id)}
            onDecrease={() => onDecrease(item.id)}
            onRemove={() => onRemove(item.id)}
          />
        ))}
      </View>
    </View>
  );
}

export default function BaseModeScreen() {
  const insets = useSafeAreaInsets();

  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<BaseItem[]>([]);
  const [query, setQuery] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [busyIds, setBusyIds] = useState<string[]>([]);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setItems(await apiGetBaseMode());
      } catch {
        Alert.alert("שגיאה", "לא הצלחתי לטעון מצב בסיס.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const totalTarget = useMemo(() => {
    return items.reduce((sum, x) => sum + (x.targetQty || 0), 0);
  }, [items]);

  const groupedSections = useMemo(() => {
    const q = normalizeName(query);

    return LOCATIONS.map((loc) => {
      const groupedItems = items
        .filter((item) => item.location === loc)
        .filter((item) => (q ? normalizeName(item.name).includes(q) : true))
        .sort((a, b) => a.name.localeCompare(b.name));

      return {
        location: loc,
        title: locationLabel(loc),
        items: groupedItems,
      };
    }).filter((section) => section.items.length > 0);
  }, [items, query]);

  function markBusy(id: string) {
    setBusyIds((prev) => (prev.includes(id) ? prev : [...prev, id]));
  }

  function unmarkBusy(id: string) {
    setBusyIds((prev) => prev.filter((x) => x !== id));
  }

  async function addItem(payload: Omit<BaseItem, "id">) {
    const exists = items.some(
      (x) => normalizeName(x.name) === normalizeName(payload.name) && x.location === payload.location
    );

    if (exists) {
      Alert.alert("כבר קיים", "המוצר כבר קיים במצב בסיס באותו מיקום.");
      return;
    }

    try {
      const created = await apiCreateBaseItem(payload);
      setItems((prev) => [...prev, created]);
    } catch {
      Alert.alert("שגיאה", "לא הצלחתי להוסיף את הפריט.");
    }
  }

  async function bumpQty(id: string, delta: number) {
    const current = items.find((x) => x.id === id);
    if (!current) return;

    const nextQty = Math.max(1, current.targetQty + delta);
    if (nextQty === current.targetQty) return;

    const previousItems = items;
    setItems((prev) =>
      prev.map((it) => (it.id === id ? { ...it, targetQty: nextQty } : it))
    );
    markBusy(id);

    try {
      await apiUpdateBaseItem(id, { targetQty: nextQty });
    } catch {
      setItems(previousItems);
      Alert.alert("שגיאה", "לא הצלחתי לעדכן את הכמות.");
    } finally {
      unmarkBusy(id);
    }
  }

  async function removeItem(id: string) {
    const previousItems = items;
    setItems((prev) => prev.filter((x) => x.id !== id));
    markBusy(id);

    try {
      await apiDeleteBaseItem(id);
    } catch {
      setItems(previousItems);
      Alert.alert("שגיאה", "לא הצלחתי למחוק את הפריט.");
    } finally {
      unmarkBusy(id);
    }
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />
        <ScreenHeader title="מצב בסיס" onBack={() => router.back()} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={BRAND.PRIMARY} />
          <Text style={styles.loadingText}>טוען מצב בסיס...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />

        <ScreenHeader title="מצב בסיס" onBack={() => router.back()} />

        <AddBaseItemModal open={addOpen} onClose={() => setAddOpen(false)} onAdd={addItem} />

        <FlatList
          data={groupedSections}
          keyExtractor={(section) => section.location}
          contentContainerStyle={[styles.content, { paddingBottom: 110 + insets.bottom }]}
          keyboardShouldPersistTaps="handled"
          ListHeaderComponent={
            <>
              <View style={styles.heroCard}>
                <Text style={styles.heroTitle}>המלאי האידיאלי של הבית</Text>
                <Text style={styles.heroSubtitle}>
                  כאן מגדירים מה תמיד אמור להיות בבית. הרשימה מסודרת לפי מיקומים, כמו דף רשימות אחד ארוך.
                </Text>

                <View style={styles.summaryRow}>
                  <SummaryCard title="פריטים" value={`${items.length}`} icon="list-outline" />
                  <SummaryCard title='סה"כ יעד' value={`${totalTarget}`} icon="stats-chart-outline" />
                </View>
              </View>

              <View style={styles.searchCard}>
                <Ionicons name="search" size={18} color={BRAND.MUTED} />
                <TextInput
                  value={query}
                  onChangeText={setQuery}
                  placeholder="חיפוש בכל הרשימה..."
                  placeholderTextColor={BRAND.MUTED}
                  style={styles.searchInput}
                  textAlign="right"
                />
                {!!query && (
                  <TouchableOpacity onPress={() => setQuery("")}>
                    <Ionicons name="close-circle" size={18} color={BRAND.MUTED} />
                  </TouchableOpacity>
                )}
              </View>
            </>
          }
          renderItem={({ item }) => (
            <LocationSection
              section={item}
              busyIds={busyIds}
              onIncrease={(id) => bumpQty(id, 1)}
              onDecrease={(id) => bumpQty(id, -1)}
              onRemove={removeItem}
            />
          )}
          ItemSeparatorComponent={() => <View style={{ height: 14 }} />}
          ListEmptyComponent={
            <View style={styles.emptyCard}>
              <Ionicons name="folder-open-outline" size={24} color={BRAND.MUTED} />
              <Text style={styles.emptyTitle}>אין פריטים להצגה</Text>
              <Text style={styles.emptyText}>אפשר להוסיף פריט חדש לרשימה.</Text>
            </View>
          }
        />

        <View style={[styles.bottomBar, { paddingBottom: 16 + insets.bottom }]}>
          <PrimaryButton title="הוסף פריט" onPress={() => setAddOpen(true)} />
        </View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: BRAND.BG,
  },

  content: {
    padding: 16,
    gap: 0,
  },

  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },

  loadingText: {
    marginTop: 8,
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 13,
  },

  heroCard: {
    backgroundColor: "rgba(255,255,255,0.92)",
    borderRadius: 22,
    padding: 15,
    borderWidth: 1,
    borderColor: "#E8ECF3",
    marginBottom: 12,
  },

  heroTitle: {
    fontSize: 18,
    fontWeight: "900",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  heroSubtitle: {
    marginTop: 6,
    color: BRAND.MUTED,
    fontWeight: "700",
    lineHeight: 18,
    fontSize: 12.5,
    textAlign: "right",
  },

  summaryRow: {
    flexDirection: "row-reverse",
    gap: 10,
    marginTop: 12,
  },

  summaryCard: {
    flex: 1,
    backgroundColor: BRAND.CARD,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    padding: 11,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },

  summaryIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: BRAND.PRIMARY_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },

  summaryTitle: {
    color: BRAND.MUTED,
    fontWeight: "800",
    fontSize: 11,
    textAlign: "right",
  },

  summaryValue: {
    marginTop: 2,
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 16,
    textAlign: "right",
  },

  searchCard: {
    marginBottom: 14,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 11,
    borderRadius: 16,
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
  },

  searchInput: {
    flex: 1,
    color: BRAND.TEXT,
    fontWeight: "700",
    fontSize: 13,
  },

  sectionBlock: {
    marginBottom: 2,
  },

  locationHeader: {
    position: "relative",
    marginBottom: 8,
    justifyContent: "center",
  },

  locationHeaderLine: {
    height: 1,
    backgroundColor: "#DCE4EF",
    width: "100%",
  },

  locationHeaderChip: {
    position: "absolute",
    alignSelf: "flex-end",
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    backgroundColor: BRAND.BG,
    paddingHorizontal: 10,
    height: 26,
    borderRadius: 999,
  },

  locationHeaderText: {
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 13,
  },

  notebookCard: {
    position: "relative",
    backgroundColor: "rgba(255,255,255,0.97)",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#E8ECF3",
    overflow: "hidden",
    paddingVertical: 2,
  },

  leftMarginLine: {
    position: "absolute",
    left: 34,
    top: 0,
    bottom: 0,
    width: 2,
    backgroundColor: BRAND.NOTE_MARGIN,
    opacity: 0.9,
  },

  noteRow: {
    minHeight: 54,
    borderBottomWidth: 1,
    borderBottomColor: BRAND.NOTE_LINE,
    paddingRight: 14,
    paddingLeft: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "transparent",
  },

  noteActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },

  noteIconBtn: {
    width: 28,
    height: 28,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F7FAFD",
    borderWidth: 1,
    borderColor: "#E7EDF5",
  },

  noteQtyPill: {
    minWidth: 30,
    height: 28,
    paddingHorizontal: 8,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F7FAFD",
    borderWidth: 1,
    borderColor: "#E7EDF5",
  },

  noteQtyText: {
    fontSize: 12,
    fontWeight: "900",
    color: BRAND.TEXT,
  },

  noteTextWrap: {
    flex: 1,
    alignItems: "flex-end",
    marginLeft: 12,
  },

  noteTitle: {
    fontSize: 14,
    fontWeight: "800",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  noteMeta: {
    marginTop: 2,
    fontSize: 11,
    color: BRAND.MUTED,
    fontWeight: "700",
    textAlign: "right",
  },

  emptyCard: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 16,
    paddingVertical: 24,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },

  emptyTitle: {
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 14,
  },

  emptyText: {
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 12,
  },

  bottomBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    padding: 16,
    backgroundColor: "rgba(244,244,244,0.95)",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },

  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(17,24,39,0.35)",
    justifyContent: "flex-end",
    padding: 12,
  },

  modalCard: {
    backgroundColor: BRAND.CARD,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
  },

  modalHandle: {
    alignSelf: "center",
    width: 42,
    height: 5,
    borderRadius: 999,
    backgroundColor: "#D1D5DB",
    marginBottom: 12,
  },

  modalHeader: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
  },

  modalTitle: {
    fontSize: 16,
    fontWeight: "900",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  modalSubtitle: {
    marginTop: 6,
    marginBottom: 14,
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 12,
    textAlign: "right",
    lineHeight: 18,
  },

  iconBtn: {
    padding: 6,
  },

  field: {
    marginBottom: 12,
  },

  label: {
    marginBottom: 6,
    color: BRAND.MUTED,
    fontWeight: "800",
    fontSize: 11.5,
    textAlign: "right",
  },

  input: {
    backgroundColor: "#FAFBFD",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 13,
    paddingHorizontal: 12,
    paddingVertical: 11,
    color: BRAND.TEXT,
    fontWeight: "700",
    fontSize: 13,
  },

  locationWrap: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 14,
  },

  locationOption: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 11,
    paddingVertical: 9,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    backgroundColor: "#fff",
  },

  locationOptionActive: {
    backgroundColor: "#F4FBFF",
    borderColor: "rgba(2,132,199,0.35)",
  },

  locationOptionText: {
    color: BRAND.MUTED,
    fontWeight: "800",
    fontSize: 12,
  },

  locationOptionTextActive: {
    color: BRAND.TEXT,
  },
});