// frontend/app/receipts/review.tsx
import React, { useMemo, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Modal,
  TextInput,
  Alert,
  Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";

import PrimaryButton from "@/src/ui/PrimaryButton";
import { getSelectedHomeId } from "../home/selected-home";
import { addProduct } from "@/src/api/stock";
import { consumeLastScannedReceipt } from "@/src/context/receipt-scan-store";

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_BG = "#F4F4F4";
const TEXT_DARK = "#111827";
const TEXT_MUTED = "#6B7280";

const BRAND_PINK = "#FF4FA3";
const BRAND_PINK_SOFT = "#FFE0EF";

// --------------------
// Locations (UI-level)
// --------------------
type LocationKey = "fridge" | "freezer" | "pantry" | "cleaning" | "other";
type StorageCategory = LocationKey;

const LOCATION_LABEL: Record<LocationKey, string> = {
  fridge: "מקרר",
  freezer: "מקפיא",
  pantry: "מזווה",
  cleaning: "ניקיון",
  other: "אחר",
};

const LOCATION_ICON: Record<LocationKey, keyof typeof Ionicons.glyphMap> = {
  fridge: "snow-outline",
  freezer: "ice-cream-outline",
  pantry: "cube-outline",
  cleaning: "sparkles-outline",
  other: "help-circle-outline",
};

function normalizeCategory(v: any): StorageCategory {
  const s = String(v ?? "").trim().toLowerCase();
  if (s === "fridge" || s === "freezer" || s === "pantry" || s === "cleaning" || s === "other") return s;
  return "other";
}

function categoryToDefaultLocation(cat?: any): LocationKey {
  // כרגע מיפוי 1:1. אם בעתיד תרצי closet לניקיון, תשני כאן.
  return normalizeCategory(cat);
}

type DetectedItem = {
  id: string;
  barcode?: string; // שימושי להמשך
  name: string;
  quantity: number;
  unit?: string;

  storage_category?: StorageCategory; // מגיע מהשרת
  location: LocationKey; // מיקום נבחר/מוצע (editable)
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
      <View style={{ flexDirection: "row-reverse", alignItems: "center", gap: 8 }}>
        {leftIcon}
        <Text style={{ fontWeight: "800", color: TEXT_DARK }}>{title}</Text>
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

  // תומך גם ב-GeneralResponse עטוף
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

function LocationPill({ loc }: { loc: LocationKey }) {
  return (
    <View style={styles.locPill}>
      <Ionicons name={LOCATION_ICON[loc]} size={14} color={TEXT_DARK} />
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
    <View style={{ marginTop: 10 }}>
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
              <Ionicons name={LOCATION_ICON[opt]} size={16} color={TEXT_DARK} />
              <Text style={styles.locChipText}>{LOCATION_LABEL[opt]}</Text>
            </Pressable>
          );
        })}
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

  useEffect(() => {
    setItems(mapReceiptToDetectedItems(receiptObj));
  }, [receiptObj]);

  const totalCount = useMemo(() => items.length, [items.length]);

  function upsertItem(updated: DetectedItem) {
    setItems((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
  }

  function removeItem(id: string) {
    setItems((prev) => prev.filter((x) => x.id !== id));
  }

  async function onConfirmAddAll() {
    if (saving) return;

    if (items.length === 0) {
      Alert.alert("אין מוצרים", "אין מה להוסיף למלאי.");
      return;
    }

    // ⚠️ כרגע addProduct אצלך כנראה מקבל רק name+quantity.
    // אם ה-API תומך גם במיקום, הוסיפי כאן location.
    const payload = items.map((x) => ({
      name: x.name.trim(),
      quantity: Number.isFinite(x.quantity) ? x.quantity : 1,
      // location: x.location, // ← להפעיל אחרי שתתמכי בזה בשרת
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
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.appTitle}>StockUp</Text>
            <Text style={styles.appSubtitle}>סקירה ועריכה של המוצרים שזוהו מהקבלה.</Text>
          </View>

          <Pressable onPress={() => router.back()} style={styles.headerIcon}>
            <Ionicons name="chevron-forward" size={22} color={TEXT_DARK} />
          </Pressable>
        </View>

        <View style={styles.sectionHeaderRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.sectionTitle}>מוצרים שזוהו</Text>
            <Text style={styles.sectionSubtitle}>{totalCount} מוצרים • לחצי על מוצר כדי לערוך</Text>
          </View>

          <Pressable onPress={() => setIsAddOpen(true)} style={styles.smallActionBtn}>
            <Ionicons name="add" size={18} color={TEXT_DARK} />
            <Text style={styles.smallActionText}>הוסף</Text>
          </Pressable>
        </View>

        {!receiptObj && (
          <View style={styles.emptyCard}>
            <View style={styles.emptyIcon}>
              <Ionicons name="alert-circle-outline" size={22} color={TEXT_MUTED} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.emptyTitle}>אין נתוני סריקה</Text>
              <Text style={styles.emptyText}>חזרי למסך ההעלאה ונסי שוב.</Text>
            </View>
          </View>
        )}

        <View style={{ gap: 10 }}>
          {items.length === 0 ? (
            <View style={styles.emptyCard}>
              <View style={styles.emptyIcon}>
                <Ionicons name="receipt-outline" size={22} color={TEXT_MUTED} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.emptyTitle}>הרשימה ריקה</Text>
                <Text style={styles.emptyText}>אפשר להוסיף מוצר ידנית עם “הוסף”.</Text>
              </View>
            </View>
          ) : (
            items.map((item) => (
              <Pressable key={item.id} onPress={() => setEditItem(item)} style={styles.itemCard}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.itemName} numberOfLines={1}>
                    {item.name}
                  </Text>

                  <View style={{ flexDirection: "row-reverse", alignItems: "center", gap: 8, marginTop: 6 }}>
                    <Text style={styles.itemMeta}>
                      כמות: {item.quantity}
                      {item.unit ? ` ${item.unit}` : ""}
                    </Text>

                    <LocationPill loc={item.location} />
                  </View>
                </View>

                <View style={styles.editBubble}>
                  <Ionicons name="create-outline" size={16} color={BRAND_PINK} />
                </View>
              </Pressable>
            ))
          )}
        </View>

        <PrimaryButtonCompat
          title={saving ? "מוסיף למלאי..." : "אישור והוספה למלאי"}
          onPress={onConfirmAddAll}
          leftIcon={<Ionicons name="checkmark-circle-outline" size={20} color={TEXT_DARK} />}
          disabled={items.length === 0 || saving}
        />

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
      </ScrollView>
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

  React.useEffect(() => {
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
          <Text style={styles.modalTitle}>עריכת מוצר</Text>

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

          <View style={styles.modalActions}>
            <Pressable style={styles.dangerBtn} onPress={() => onDelete(item.id)}>
              <Ionicons name="trash-outline" size={18} color={TEXT_DARK} />
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
                const q = Number(quantity.replace(",", "."));
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
              leftIcon={<Ionicons name="save-outline" size={18} color={TEXT_DARK} />}
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

  React.useEffect(() => {
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
          <Text style={styles.modalTitle}>הוספת מוצר</Text>

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

          <View style={styles.modalActions}>
            <View style={{ flex: 1 }} />
            <Pressable style={styles.secondaryBtn} onPress={onClose}>
              <Text style={styles.modalBtnText}>ביטול</Text>
            </Pressable>
          </View>

          <View style={{ marginTop: 12 }}>
            <PrimaryButtonCompat
              title="הוסף"
              onPress={() => {
                const q = Number(quantity.replace(",", "."));
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
              leftIcon={<Ionicons name="add-circle-outline" size={18} color={TEXT_DARK} />}
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
    <View style={{ marginTop: 10 }}>
      <Text style={styles.fieldLabel}>{props.label}</Text>
      <TextInput
        value={props.value}
        onChangeText={props.onChangeText}
        placeholder={props.placeholder}
        keyboardType={props.keyboardType}
        style={styles.input}
        placeholderTextColor="#9CA3AF"
      />
    </View>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: BRAND_BG },
  container: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 24, gap: 18 },

  headerRow: { flexDirection: "row-reverse", alignItems: "center" },
  appTitle: { fontSize: 22, fontWeight: "700", color: TEXT_DARK, textAlign: "right" },
  appSubtitle: { fontSize: 12, color: TEXT_MUTED, textAlign: "right", marginTop: 4 },

  headerIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
    marginLeft: 10,
  },

  sectionHeaderRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: TEXT_DARK, textAlign: "right" },
  sectionSubtitle: { fontSize: 12, color: TEXT_MUTED, textAlign: "right", marginTop: 4 },

  smallActionBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 14,
    backgroundColor: BRAND_BLUE_SOFT,
  },
  smallActionText: { fontSize: 12, fontWeight: "700", color: TEXT_DARK, textAlign: "right" },

  itemCard: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  itemName: { fontSize: 14, fontWeight: "700", color: TEXT_DARK, textAlign: "right" },
  itemMeta: { fontSize: 12, color: TEXT_MUTED, textAlign: "right" },

  editBubble: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: BRAND_PINK_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },

  locPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 999,
    backgroundColor: BRAND_BLUE_SOFT,
    borderWidth: 1,
    borderColor: "#DCEBFA",
  },
  locPillText: { fontSize: 12, fontWeight: "800", color: TEXT_DARK, textAlign: "right" },

  locRow: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 8,
  },
  locChip: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 14,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  locChipActive: {
    backgroundColor: BRAND_BLUE_SOFT,
    borderColor: "#BFDDF6",
  },
  locChipText: { fontSize: 12, fontWeight: "800", color: TEXT_DARK, textAlign: "right" },

  emptyCard: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  emptyIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: BRAND_BLUE_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyTitle: { fontSize: 14, fontWeight: "700", color: TEXT_DARK, textAlign: "right" },
  emptyText: { fontSize: 12, color: TEXT_MUTED, textAlign: "right", marginTop: 4 },

  modalOverlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.35)", justifyContent: "center", padding: 16 },
  modalCard: { backgroundColor: "#FFFFFF", borderRadius: 20, padding: 16, borderWidth: 1, borderColor: "#E5E7EB" },
  modalTitle: { fontSize: 16, fontWeight: "800", color: TEXT_DARK, textAlign: "right" },

  fieldLabel: { marginTop: 2, fontSize: 12, color: TEXT_MUTED, textAlign: "right" },
  input: {
    marginTop: 6,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    backgroundColor: "#FAFAFA",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    textAlign: "right",
    fontSize: 14,
    color: TEXT_DARK,
  },

  modalActions: { flexDirection: "row-reverse", alignItems: "center", gap: 8, marginTop: 14 },
  dangerBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 14,
    backgroundColor: BRAND_PINK_SOFT,
  },
  secondaryBtn: { paddingVertical: 10, paddingHorizontal: 12, borderRadius: 14, backgroundColor: BRAND_BLUE_SOFT },
  modalBtnText: { fontSize: 13, fontWeight: "800", color: TEXT_DARK },
});
