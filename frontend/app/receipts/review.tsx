// frontend/app/receipts/review.tsx
import React, { useMemo, useState, useEffect, useCallback, ComponentProps, JSX } from "react";
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Modal,
  TextInput,
  Alert,
  Platform,
  FlatList,
  KeyboardAvoidingView,
} from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";

import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import { getSelectedHomeId } from "../home/selected-home";
import { addProduct } from "@/src/api/stock";
import { consumeLastScannedReceipt } from "@/src/context/receipt-scan-store";

// -------- Brand
const BRAND_BG = "#F5F6F8";
const CARD = "#FFFFFF";
const BORDER = "#E6E8EE";
const TEXT = "#111827";
const MUTED = "#6B7280";

const BRAND_PINK = "#FF4FA3";
const BRAND_PINK_SOFT = "#FFE0EF";

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_BLUE_LINE = "#DCEBFA";

const SHADOW = Platform.select({
  ios: {
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 6 },
  },
  android: { elevation: 2 },
  default: {},
});

// --------------------
// Locations (UI-level)
// --------------------
type LocationKey = "fridge" | "freezer" | "pantry" | "cleaning" | "other";
type StorageCategory = LocationKey;
type IconProps = Omit<
  ComponentProps<typeof MaterialCommunityIcons>,
  "name"
>;
const LOCATION_LABEL: Record<LocationKey, string> = {
  fridge: "מקרר",
  freezer: "מקפיא",
  pantry: "מזווה",
  cleaning: "ניקיון וטואלטיקה",
  other: "אחר",
};

const LOCATION_ICON: Record<
  LocationKey,
  (props: IconProps) => JSX.Element
> = {
  fridge: (props) => (
    <MaterialCommunityIcons name="fridge-outline" {...props} />
  ),
  freezer: (props) => (
    <MaterialCommunityIcons name="snowflake-variant" {...props} />
  ),
  pantry: (props) => (
    <MaterialCommunityIcons name="food-variant" {...props} />
  ),
  cleaning: (props) => (
    <MaterialCommunityIcons name="spray-bottle" {...props} />
  ),
  other: (props) => (
    <MaterialCommunityIcons name="dots-horizontal" {...props} />
  ),
};


function storageCategoryToLocationType(cat?: string | null): string {
  const s = String(cat ?? "").toLowerCase().trim();
  switch (s) {
    case "fridge":
      return "FRIDGE";
    case "freezer":
      return "FREEZER";
    case "pantry":
      return "PANTRY";
    case "cleaning":
      return "CLEANING_SUPPLIES";
    default:
      return "OTHER";
  }
}

function normalizeCategory(v: any): StorageCategory {
  const s = String(v ?? "").trim().toLowerCase();
  if (s === "fridge" || s === "freezer" || s === "pantry" || s === "cleaning" || s === "other") return s;
  return "other";
}

function categoryToDefaultLocation(cat?: any): LocationKey {
  return normalizeCategory(cat);
}

type DetectedItem = {
  id: string;
  barcode?: string;
  name: string;
  quantity: number;
  unit?: string;

  storage_category?: StorageCategory;
  location: LocationKey;
};

function uuid() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

function PrimaryButtonCompat(props: {
  title: string;
  onPress: () => void;
  leftIcon?: React.ReactNode;
  disabled?: boolean;
}) {
  const { title, onPress, leftIcon, disabled } = props;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Btn: any = PrimaryButton;

  return (
    <Btn title={title} onPress={onPress} disabled={disabled}>
      <View style={{ flexDirection: "row-reverse", alignItems: "center", gap: 10 }}>
        {leftIcon}
        <Text style={{ fontWeight: "900", color: TEXT, letterSpacing: 0.2 }}>{title}</Text>
      </View>
    </Btn>
  );
}

function parseReceiptParam(receiptParam?: string): any | null {
  if (!receiptParam) return null;
  try {
    return JSON.parse(receiptParam);
  } catch {}
  try {
    return JSON.parse(decodeURIComponent(receiptParam));
  } catch {}
  try {
    return JSON.parse(decodeURIComponent(decodeURIComponent(receiptParam)));
  } catch {}
  return null;
}

function mapReceiptToDetectedItems(receipt: any | null): DetectedItem[] {
  if (!receipt) return [];

  const inner = receipt?.data?.receipt ?? receipt?.data ?? receipt;
  const rawItems = inner.items ?? inner.detected_items ?? inner?.data?.items ?? [];
  if (!Array.isArray(rawItems)) return [];

  return rawItems
    .map((it: any) => {
      const name = String(it.name ?? it.product_name ?? it.title ?? "").trim();
      const qRaw = it.quantity ?? it.qty ?? 1;
      const quantity = Number(String(qRaw).replace(",", "."));
      const unit = it.unit ? String(it.unit) : undefined;

      if (!name) return null;

      const storage_category = it.storage_category ?? it.storageCategory ?? it.category;
      const normalizedCat = normalizeCategory(storage_category);
      const location = categoryToDefaultLocation(normalizedCat);

      return {
        id: uuid(),
        barcode: it.barcode ? String(it.barcode) : undefined,
        name,
        quantity: Number.isFinite(quantity) && quantity > 0 ? quantity : 1,
        unit,
        storage_category: normalizedCat,
        location,
      } as DetectedItem;
    })
    .filter(Boolean) as DetectedItem[];
}

function Chip({
  icon,
  label,
  tone = "blue",
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  tone?: "blue" | "pink";
}) {
  const bg = tone === "pink" ? BRAND_PINK_SOFT : BRAND_BLUE_SOFT;
  const border = tone === "pink" ? "#FFD0E6" : BRAND_BLUE_LINE;
  const iconColor = tone === "pink" ? BRAND_PINK : TEXT;

  return (
    <View style={[styles.chip, { backgroundColor: bg, borderColor: border }]}>
      <Ionicons name={icon} size={14} color={iconColor} />
      <Text style={styles.chipText}>{label}</Text>
    </View>
  );
}

function LocationPill({ loc }: { loc: LocationKey }) {
  return (
    <View style={styles.locPill}>
      {LOCATION_ICON[loc]({ size: 14, color: TEXT })}
      <Text style={styles.locPillText}>{LOCATION_LABEL[loc]}</Text>
    </View>
  );
}

function LocationSelector({
  value,
  onChange,
}: {
  value: LocationKey;
  onChange: (v: LocationKey) => void;
}) {
  const options: LocationKey[] = ["fridge", "freezer", "pantry", "cleaning", "other"];

  return (
    <View style={{ marginTop: 12 }}>
      <Text style={styles.fieldLabel}>מיקום בבית</Text>
      <View style={styles.locRow}>
        {options.map((opt) => {
          const active = value === opt;
          return (
            <Pressable
              key={opt}
              onPress={() => onChange(opt)}
              style={[styles.locChip, active && styles.locChipActive]}
            >
              {LOCATION_ICON[opt]({ size: 16, color: active ? BRAND_PINK : TEXT })}
              <Text style={[styles.locChipText, active && { color: TEXT }]}>{LOCATION_LABEL[opt]}</Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

function QtyBadge({ qty, unit }: { qty: number; unit?: string }) {
  const text = `${qty}${unit ? ` ${unit}` : ""}`;
  return (
    <View style={styles.qtyBadge}>
      <Text style={styles.qtyBadgeText}>{text}</Text>
    </View>
  );
}

function EmptyState({
  icon,
  title,
  subtitle,
  actionText,
  onAction,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle: string;
  actionText?: string;
  onAction?: () => void;
}) {
  return (
    <View style={styles.emptyCard}>
      <View style={styles.emptyIcon}>
        <Ionicons name={icon} size={22} color={MUTED} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.emptyTitle}>{title}</Text>
        <Text style={styles.emptyText}>{subtitle}</Text>

        {actionText && onAction ? (
          <Pressable onPress={onAction} style={styles.inlineAction}>
            <Ionicons name="add-circle-outline" size={16} color={BRAND_PINK} />
            <Text style={styles.inlineActionText}>{actionText}</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

export default function ReceiptReviewDetectedProductsScreen() {
  const { receipt } = useLocalSearchParams<{ receipt?: string }>();

  const receiptFromParam = useMemo(() => parseReceiptParam(receipt), [receipt]);
  const receiptObj = useMemo(() => receiptFromParam ?? consumeLastScannedReceipt(), [receiptFromParam]);

  const [items, setItems] = useState<DetectedItem[]>([]);
  const [editItem, setEditItem] = useState<DetectedItem | null>(null);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const [query, setQuery] = useState("");

  useEffect(() => {
    setItems(mapReceiptToDetectedItems(receiptObj));
  }, [receiptObj]);

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter((x) => x.name.toLowerCase().includes(q));
  }, [items, query]);

  const totalCount = useMemo(() => items.length, [items.length]);
  const filteredCount = useMemo(() => filteredItems.length, [filteredItems.length]);

  const locationCounts = useMemo(() => {
    const c: Record<LocationKey, number> = { fridge: 0, freezer: 0, pantry: 0, cleaning: 0, other: 0 };
    for (const it of items) c[it.location ?? "other"]++;
    return c;
  }, [items]);

  function upsertItem(updated: DetectedItem) {
    setItems((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
  }

  function removeItem(id: string) {
    setItems((prev) => prev.filter((x) => x.id !== id));
  }

  const onConfirmAddAll = useCallback(async () => {
    if (saving) return;

    if (items.length === 0) {
      Alert.alert("אין מוצרים", "אין מה להוסיף למלאי.");
      return;
    }

    const payload = items.map((x) => ({
      name: x.name.trim(),
      quantity: Number.isFinite(x.quantity) ? x.quantity : 1,
      location: storageCategoryToLocationType(x.location ?? x.storage_category ?? "other"),
    }));

    const bad = payload.find((p) => !p.name || p.quantity <= 0);
    if (bad) {
      Alert.alert("שגיאה", "ודאי שלכל מוצר יש שם וכמות חיובית.");
      return;
    }

    setSaving(true);
    try {
      const homeId = await getSelectedHomeId();
      if (!homeId) {
        Alert.alert("שגיאה", "לא נבחר בית פעיל. חזרי ובחרי בית.");
        return;
      }

      const results = await Promise.allSettled(payload.map((p) => addProduct(homeId, p)));
      const ok = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.length - ok;

      if (failed === 0) {
        Alert.alert("התווסף!", "כל המוצרים הוכנסו למלאי המרכזי.");
        router.back();
        return;
      }

      Alert.alert("נוספו חלקית", `נוספו ${ok} מוצרים, נכשלו ${failed}.`);
    } catch (e: any) {
      Alert.alert("נכשל", e?.message ?? "לא הצלחנו להוסיף למלאי. נסי שוב.");
    } finally {
      setSaving(false);
    }
  }, [items, saving]);

  const renderItem = useCallback(
    ({ item }: { item: DetectedItem }) => {
      return (
        <Pressable onPress={() => setEditItem(item)} style={styles.itemCard}>
          <View style={styles.itemIconCircle}>
            {LOCATION_ICON[item.location]({ size: 18, color: BRAND_PINK })}
          </View>

          <View style={styles.itemMid}>
            <Text style={styles.itemName} numberOfLines={1}>
              {item.name}
            </Text>

            <View style={styles.itemSubRow}>
              <LocationPill loc={item.location} />
              <View style={{ flex: 1 }} />
              <QtyBadge qty={item.quantity} unit={item.unit} />
            </View>
          </View>

          <View style={styles.itemChevron}>
            <Ionicons name="chevron-back" size={18} color={MUTED} />
          </View>
        </Pressable>
      );
    },
    [setEditItem]
  );

  const keyExtractor = useCallback((it: DetectedItem) => it.id, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
        {/* Header */}
        <View style={styles.headerWrap}>
          <View style={styles.headerTopRow}>
            <Pressable onPress={() => router.back()} style={styles.headerIconBtn}>
              <Ionicons name="chevron-forward" size={20} color={TEXT} />
            </Pressable>

            <View style={{ flex: 1 }}>
              <Text style={styles.title}>סקירת קבלה</Text>
              <Text style={styles.subtitle}>ערכי פריטים לפני הוספה למלאי</Text>
            </View>

            <Pressable onPress={() => setIsAddOpen(true)} style={styles.headerAddBtn}>
              <Ionicons name="add" size={18} color={TEXT} />
              <Text style={styles.headerAddText}>הוסף</Text>
            </Pressable>
          </View>

          {/* Chips */}
          <View style={styles.chipsRow}>
            <Chip icon="list-outline" label={`${totalCount} פריטים`} />
            <Chip icon="search-outline" label={query.trim() ? `${filteredCount} תוצאות` : "סינון"} />
            <Chip
              icon="snow-outline"
              label={`${locationCounts.fridge} מקרר`}
            />
            <Chip
              icon="cube-outline"
              label={`${locationCounts.pantry} מזווה`}
            />
          </View>

          {/* Search */}
          <View style={styles.searchWrap}>
            <Ionicons name="search-outline" size={18} color={MUTED} />
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder="חיפוש מוצר…"
              placeholderTextColor="#9CA3AF"
              style={styles.searchInput}
              textAlign="right"
            />
            {query.trim() ? (
              <Pressable onPress={() => setQuery("")} style={styles.searchClear}>
                <Ionicons name="close" size={16} color={TEXT} />
              </Pressable>
            ) : (
              <View style={{ width: 28 }} />
            )}
          </View>
        </View>

        {/* List */}
        <FlatList
          data={filteredItems}
          keyExtractor={keyExtractor}
          renderItem={renderItem}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
          ListEmptyComponent={
            !receiptObj ? (
              <EmptyState
                icon="alert-circle-outline"
                title="אין נתוני סריקה"
                subtitle="חזרי למסך הסריקה ונסי שוב."
              />
            ) : (
              <EmptyState
                icon={items.length === 0 ? "receipt-outline" : "search-outline"}
                title={items.length === 0 ? "הרשימה ריקה" : "לא נמצאו תוצאות"}
                subtitle={items.length === 0 ? "אפשר להוסיף מוצר ידנית." : "נסי מילה אחרת או נקי את החיפוש."}
                actionText={items.length === 0 ? "הוספת מוצר" : undefined}
                onAction={items.length === 0 ? () => setIsAddOpen(true) : undefined}
              />
            )
          }
        />

        {/* Footer CTA */}
        <View style={styles.footer}>
          <PrimaryButtonCompat
            title={saving ? "מוסיף למלאי..." : "אישור והוספה למלאי"}
            onPress={onConfirmAddAll}
            leftIcon={<Ionicons name="checkmark-circle-outline" size={20} color={TEXT} />}
            disabled={items.length === 0 || saving}
          />
          <Text style={styles.footerHint}>טיפ: לחצי על פריט כדי לערוך שם/כמות/מיקום</Text>
        </View>

        {/* Modals */}
        <EditItemModal
          item={editItem}
          onClose={() => setEditItem(null)}
          onSave={(updated) => {
            upsertItem(updated);
            setEditItem(null);
          }}
          onDelete={(id) => {
            removeItem(id);
            setEditItem(null);
          }}
        />

        <AddItemModal
          open={isAddOpen}
          onClose={() => setIsAddOpen(false)}
          onAdd={(newItem) => {
            setItems((prev) => [{ ...newItem, id: uuid() }, ...prev]);
            setIsAddOpen(false);
          }}
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function EditItemModal({
  item,
  onClose,
  onSave,
  onDelete,
}: {
  item: DetectedItem | null;
  onClose: () => void;
  onSave: (item: DetectedItem) => void;
  onDelete: (id: string) => void;
}) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [unit, setUnit] = useState("");
  const [location, setLocation] = useState<LocationKey>("other");

  useEffect(() => {
    if (!item) return;
    setName(item.name ?? "");
    setQuantity(String(item.quantity ?? 1));
    setUnit(item.unit ?? "");
    setLocation(item.location ?? "other");
  }, [item]);

  if (!item) return null;

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.modalOverlay} onPress={onClose}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <View style={styles.modalHeaderRow}>
            <View style={styles.modalTitleWrap}>
              <Text style={styles.modalTitle}>עריכת מוצר</Text>
              <Text style={styles.modalSubtitle}>עדכני שם / כמות / יחידה / מיקום</Text>
            </View>
            <Pressable onPress={onClose} style={styles.modalCloseBtn}>
              <Ionicons name="close" size={18} color={TEXT} />
            </Pressable>
          </View>

          <Field label="שם מוצר" value={name} onChangeText={setName} placeholder="למשל: ביצים L" />
          <Field
            label="כמות"
            value={quantity}
            onChangeText={setQuantity}
            keyboardType={Platform.OS === "ios" ? "decimal-pad" : "numeric"}
            placeholder="למשל: 2"
          />
          <Field label="יחידה (אופציונלי)" value={unit} onChangeText={setUnit} placeholder="יח׳ / ק״ג / ל׳" />

          <LocationSelector value={location} onChange={setLocation} />

          <View style={styles.modalActionsRow}>
            <Pressable style={styles.dangerBtn} onPress={() => onDelete(item.id)}>
              <Ionicons name="trash-outline" size={18} color={TEXT} />
              <Text style={styles.modalBtnText}>מחק</Text>
            </Pressable>

            <View style={{ flex: 1 }} />

            <Pressable style={styles.secondaryBtn} onPress={onClose}>
              <Text style={styles.modalBtnText}>ביטול</Text>
            </Pressable>
          </View>

          <View style={{ marginTop: 12 }}>
            <PrimaryButtonCompat
              title="שמור"
              onPress={() => {
                const q = Number(String(quantity).replace(",", "."));
                if (!name.trim() || !Number.isFinite(q) || q <= 0) {
                  Alert.alert("שגיאה", "ודאי שהשם לא ריק ושכמות חיובית.");
                  return;
                }
                onSave({
                  ...item,
                  name: name.trim(),
                  quantity: q,
                  unit: unit.trim() || undefined,
                  location,
                });
              }}
              leftIcon={<Ionicons name="save-outline" size={18} color={TEXT} />}
            />
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

function AddItemModal({
  open,
  onClose,
  onAdd,
}: {
  open: boolean;
  onClose: () => void;
  onAdd: (item: Omit<DetectedItem, "id">) => void;
}) {
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [unit, setUnit] = useState("");
  const [location, setLocation] = useState<LocationKey>("other");

  useEffect(() => {
    if (!open) return;
    setName("");
    setQuantity("1");
    setUnit("");
    setLocation("other");
  }, [open]);

  if (!open) return null;

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.modalOverlay} onPress={onClose}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <View style={styles.modalHeaderRow}>
            <View style={styles.modalTitleWrap}>
              <Text style={styles.modalTitle}>הוספת מוצר</Text>
              <Text style={styles.modalSubtitle}>הוספה ידנית לרשימה</Text>
            </View>
            <Pressable onPress={onClose} style={styles.modalCloseBtn}>
              <Ionicons name="close" size={18} color={TEXT} />
            </Pressable>
          </View>

          <Field label="שם מוצר" value={name} onChangeText={setName} placeholder="למשל: טונה" />
          <Field
            label="כמות"
            value={quantity}
            onChangeText={setQuantity}
            keyboardType={Platform.OS === "ios" ? "decimal-pad" : "numeric"}
            placeholder="למשל: 1"
          />
          <Field label="יחידה (אופציונלי)" value={unit} onChangeText={setUnit} placeholder="יח׳ / ק״ג / ל׳" />

          <LocationSelector value={location} onChange={setLocation} />

          <View style={styles.modalActionsRow}>
            <View style={{ flex: 1 }} />
            <Pressable style={styles.secondaryBtn} onPress={onClose}>
              <Text style={styles.modalBtnText}>ביטול</Text>
            </Pressable>
          </View>

          <View style={{ marginTop: 12 }}>
            <PrimaryButtonCompat
              title="הוסף"
              onPress={() => {
                const q = Number(String(quantity).replace(",", "."));
                if (!name.trim() || !Number.isFinite(q) || q <= 0) {
                  Alert.alert("שגיאה", "ודאי שהשם לא ריק ושכמות חיובית.");
                  return;
                }
                onAdd({
                  name: name.trim(),
                  quantity: q,
                  unit: unit.trim() || undefined,
                  storage_category: "other",
                  location,
                });
              }}
              leftIcon={<Ionicons name="add-circle-outline" size={18} color={TEXT} />}
            />
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

function Field(props: {
  label: string;
  value: string;
  onChangeText: (v: string) => void;
  placeholder?: string;
  keyboardType?: any;
}) {
  return (
    <View style={{ marginTop: 12 }}>
      <Text style={styles.fieldLabel}>{props.label}</Text>
      <TextInput
        value={props.value}
        onChangeText={props.onChangeText}
        placeholder={props.placeholder}
        keyboardType={props.keyboardType}
        style={styles.input}
        placeholderTextColor="#9CA3AF"
        textAlign="right"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: BRAND_BG },

  // Header
  headerWrap: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 12,
    backgroundColor: BRAND_BG,
  },
  headerTopRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  headerIconBtn: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND_BLUE_LINE,
    alignItems: "center",
    justifyContent: "center",
  },
  headerAddBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    ...SHADOW,
  },
  headerAddText: { fontSize: 12, fontWeight: "900", color: TEXT },

  title: { fontSize: 18, fontWeight: "900", color: TEXT, textAlign: "right" },
  subtitle: { fontSize: 12, color: MUTED, textAlign: "right", marginTop: 2 },

  chipsRow: {
    marginTop: 10,
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
  },
  chipText: { fontSize: 12, fontWeight: "800", color: TEXT },

  searchWrap: {
    marginTop: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    ...SHADOW,
  },
  searchInput: { flex: 1, fontSize: 14, color: TEXT, paddingVertical: 0 },
  searchClear: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND_BLUE_LINE,
    alignItems: "center",
    justifyContent: "center",
  },

  // List
  listContent: {
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 120, // space for footer
    gap: 10,
  },

  itemCard: {
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 18,
    paddingVertical: 12,
    paddingHorizontal: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 12,
    ...SHADOW,
  },
  itemIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: BRAND_PINK_SOFT,
    borderWidth: 1,
    borderColor: "#FFD0E6",
    alignItems: "center",
    justifyContent: "center",
  },
  itemMid: { flex: 1 },
  itemName: { fontSize: 14, fontWeight: "900", color: TEXT, textAlign: "right" },
  itemSubRow: { marginTop: 8, flexDirection: "row-reverse", alignItems: "center", gap: 8 },

  itemChevron: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#F3F4F6",
    borderWidth: 1,
    borderColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
  },

  qtyBadge: {
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND_BLUE_LINE,
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
  },
  qtyBadgeText: { fontSize: 12, fontWeight: "900", color: TEXT },

  locPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
    backgroundColor: "#F8FAFF",
    borderWidth: 1,
    borderColor: BRAND_BLUE_LINE,
  },
  locPillText: { fontSize: 12, fontWeight: "800", color: TEXT, textAlign: "right" },

  // Empty
  emptyCard: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 12,
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 18,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    ...SHADOW,
  },
  emptyIcon: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND_BLUE_LINE,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyTitle: { fontSize: 14, fontWeight: "900", color: TEXT, textAlign: "right" },
  emptyText: { fontSize: 12, color: MUTED, textAlign: "right", marginTop: 4 },
  inlineAction: {
    marginTop: 10,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    alignSelf: "flex-start",
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 14,
    backgroundColor: BRAND_PINK_SOFT,
    borderWidth: 1,
    borderColor: "#FFD0E6",
  },
  inlineActionText: { fontSize: 12, fontWeight: "900", color: TEXT },

  // Footer
  footer: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 14,
    backgroundColor: "rgba(245,246,248,0.96)",
    borderTopWidth: 1,
    borderTopColor: BORDER,
  },
  footerHint: { marginTop: 8, fontSize: 11, color: MUTED, textAlign: "right" },

  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.35)",
    justifyContent: "center",
    padding: 16,
  },
  modalCard: {
    backgroundColor: CARD,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: BORDER,
    ...SHADOW,
  },
  modalHeaderRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  modalTitleWrap: { flex: 1 },
  modalTitle: { fontSize: 16, fontWeight: "900", color: TEXT, textAlign: "right" },
  modalSubtitle: { fontSize: 12, color: MUTED, textAlign: "right", marginTop: 2 },
  modalCloseBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND_BLUE_LINE,
    alignItems: "center",
    justifyContent: "center",
  },

  fieldLabel: { marginTop: 2, fontSize: 12, color: MUTED, textAlign: "right" },
  input: {
    marginTop: 6,
    borderWidth: 1,
    borderColor: BORDER,
    backgroundColor: "#FAFAFA",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: TEXT,
  },

  modalActionsRow: { flexDirection: "row-reverse", alignItems: "center", gap: 8, marginTop: 16 },
  dangerBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: BRAND_PINK_SOFT,
    borderWidth: 1,
    borderColor: "#FFD0E6",
  },
  secondaryBtn: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: BRAND_BLUE_LINE,
  },
  modalBtnText: { fontSize: 13, fontWeight: "900", color: TEXT },

  // Location selector
  locRow: { flexDirection: "row-reverse", flexWrap: "wrap", gap: 8, marginTop: 10 },
  locChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 9,
    paddingHorizontal: 11,
    borderRadius: 14,
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
  },
  locChipActive: { backgroundColor: BRAND_PINK_SOFT, borderColor: "#FFD0E6" },
  locChipText: { fontSize: 12, fontWeight: "900", color: TEXT, textAlign: "right" },
});
