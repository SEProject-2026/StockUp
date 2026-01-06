// app/receipts/review.tsx
import React, { useMemo, useState } from "react";
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
// או למשל:
// import PrimaryButton from "@/components/PrimaryButton";
// import { PrimaryButton } from "@/components/ui/buttons";

const BRAND_BLUE_SOFT = "#F0FAFF";
const BRAND_BG = "#F4F4F4";
const TEXT_DARK = "#111827";
const TEXT_MUTED = "#6B7280";

const BRAND_PINK = "#FF4FA3";
const BRAND_PINK_SOFT = "#FFE0EF";

type DetectedItem = {
  id: string;
  name: string;
  quantity: number;
  unit?: string;
};

function uuid() {
  return Math.random().toString(16).slice(2) + Date.now().toString(16);
}

/** TODO: החליפי ל-action אמיתי אצלכם (API/Store) */
async function addManyToHomeInventoryMock(
  homeId: string,
  items: Array<{ name: string; quantity: number; unit?: string }>
) {
  await new Promise((r) => setTimeout(r, 250));
  return true;
}

/**
 * 👇 טריק תאימות:
 * אנחנו מעבירים גם `title` וגם `children`.
 * - אם ה-PrimaryButton שלכם בנוי עם title → הוא ישתמש ב-title ויתעלם מ-children.
 * - אם הוא בנוי עם children → הוא יציג את children ויתעלם מה-title.
 */
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
      {/* אם PrimaryButton תומך children – זה ייראה טוב; אם לא – לרוב יתעלם */}
      <View style={{ flexDirection: "row-reverse", alignItems: "center", gap: 8 }}>
        {leftIcon}
        <Text style={{ fontWeight: "800", color: TEXT_DARK }}>{title}</Text>
      </View>
    </Btn>
  );
}

export default function ReceiptReviewDetectedProductsScreen() {
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  const currentHomeId = String(homeId ?? "");

  const [items, setItems] = useState<DetectedItem[]>([
    { id: uuid(), name: "חלב 3%", quantity: 2, unit: "יח׳" },
    { id: uuid(), name: "לחם מלא", quantity: 1, unit: "יח׳" },
    { id: uuid(), name: "עגבניות", quantity: 1.2, unit: "ק״ג" },
  ]);

  const [editItem, setEditItem] = useState<DetectedItem | null>(null);
  const [isAddOpen, setIsAddOpen] = useState(false);

  const totalCount = useMemo(() => items.length, [items.length]);

  function upsertItem(updated: DetectedItem) {
    setItems((prev) => prev.map((x) => (x.id === updated.id ? updated : x)));
  }

  function removeItem(id: string) {
    setItems((prev) => prev.filter((x) => x.id !== id));
  }

  async function onConfirmAddAll() {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "חסר homeId כדי להוסיף למלאי.");
      return;
    }
    if (items.length === 0) {
      Alert.alert("אין מוצרים", "אין מה להוסיף למלאי.");
      return;
    }

    const payload = items.map((x) => ({
      name: x.name.trim(),
      quantity: Number.isFinite(x.quantity) ? x.quantity : 1,
      unit: x.unit?.trim() || undefined,
    }));

    const bad = payload.find((p) => !p.name || p.quantity <= 0);
    if (bad) {
      Alert.alert("שגיאה", "ודאי שלכל מוצר יש שם וכמות חיובית.");
      return;
    }

    try {
      await addManyToHomeInventoryMock(currentHomeId, payload);
      Alert.alert("התווסף!", "כל המוצרים הוכנסו למלאי המרכזי.");
      router.back();
    } catch {
      Alert.alert("נכשל", "לא הצלחנו להוסיף למלאי. נסי שוב.");
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
        {/* HEADER (כמו אצלך) */}
        <View style={styles.headerRow}>
          <View style={{ flex: 1 }}>
            <Text style={styles.appTitle}>StockUp</Text>
            <Text style={styles.appSubtitle}>סקירה ועריכה של המוצרים שזוהו מהקבלה.</Text>
          </View>

          <Pressable onPress={() => router.back()} style={styles.headerIcon}>
            <Ionicons name="chevron-forward" size={22} color={TEXT_DARK} />
          </Pressable>
        </View>

        {/* כותרת + הוסף */}
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

        {/* LIST */}
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
                  <Text style={styles.itemMeta}>
                    כמות: {item.quantity}
                    {item.unit ? ` ${item.unit}` : ""}
                  </Text>
                </View>

                <View style={styles.editBubble}>
                  <Ionicons name="create-outline" size={16} color={BRAND_PINK} />
                </View>
              </Pressable>
            ))
          )}
        </View>

        {/* ✅ CTA עם PrimaryButton של האפליקציה */}
        <PrimaryButtonCompat
          title="אישור והוספה למלאי"
          onPress={onConfirmAddAll}
          leftIcon={<Ionicons name="checkmark-circle-outline" size={20} color={TEXT_DARK} />}
          disabled={items.length === 0}
        />

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

  React.useEffect(() => {
    if (!item) return;
    setName(item.name ?? "");
    setQuantity(String(item.quantity ?? 1));
    setUnit(item.unit ?? "");
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

          {/* ✅ כפתור שמירה עם PrimaryButton */}
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

  React.useEffect(() => {
    if (!open) return;
    setName("");
    setQuantity("1");
    setUnit("");
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

          <View style={styles.modalActions}>
            <View style={{ flex: 1 }} />
            <Pressable style={styles.secondaryBtn} onPress={onClose}>
              <Text style={styles.modalBtnText}>ביטול</Text>
            </Pressable>
          </View>

          {/* ✅ הוספה עם PrimaryButton */}
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

  // “גובה”/צפיפות כמו המסך שלך: לא מוגזם, הרבה אוויר אבל לא גבוה מדי
  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 24,
    gap: 18,
  },

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

  sectionHeaderRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },
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
  itemMeta: { fontSize: 12, color: TEXT_MUTED, textAlign: "right", marginTop: 4 },

  editBubble: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: BRAND_PINK_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },

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

  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.35)",
    justifyContent: "center",
    padding: 16,
  },
  modalCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
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

  modalActions: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    marginTop: 14,
  },
  dangerBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderRadius: 14,
    backgroundColor: BRAND_PINK_SOFT,
  },
  secondaryBtn: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: BRAND_BLUE_SOFT,
  },
  modalBtnText: { fontSize: 13, fontWeight: "800", color: TEXT_DARK },
});
