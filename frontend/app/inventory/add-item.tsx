import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Alert,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Modal,
  Pressable,
  TouchableOpacity,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";

import { CameraView, useCameraPermissions, BarcodeScanningResult } from "expo-camera";

import type { Category } from "@/src/context/inventory-context";
import ScreenHeader from "@/src/layout/ScreenHeader";
import ItemForm from "@/src/components/add-item/ItemForm";
import PrimaryButton from "@/src/ui/PrimaryButton";
import { addProduct } from "@/src/api/stock";

const BRAND_PRIMARY = "#0284C7";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";

const CATEGORY_OPTIONS: Array<{
  key: Category;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
}> = [
  { key: "fridge", label: "מקרר", icon: "snow-outline" },
  { key: "freezer", label: "מקפיא", icon: "cube-outline" },
  { key: "pantry", label: "מזווה", icon: "restaurant-outline" },
  { key: "cleaning supplies", label: "חומרי ניקוי", icon: "water-outline" },
  { key: "other", label: "אחר", icon: "ellipsis-horizontal-outline" },
];

function routeToCategory(param?: string | null): Category {
  const raw = (param ?? "").trim();
  const normalized = raw
    .replace(/_/g, "-")
    .replace(/\s+/g, "-")
    .toLowerCase();

  switch (normalized) {
    case "fridge":
      return "fridge";
    case "freezer":
      return "freezer";
    case "pantry":
      return "pantry";
    case "cleaning-supplies":
    case "cleaningsupplies":
      return "cleaning supplies";
    case "other":
      return "other";
    default:
      return "fridge";
  }
}

export default function AddItemScreen() {
  const { homeId, category: categoryParam } = useLocalSearchParams<{
    homeId?: string;
    category?: string;
  }>();

  const currentHomeId = homeId ? String(homeId) : "";

  const initialCategory = useMemo<Category>(
    () => routeToCategory(categoryParam),
    [categoryParam]
  );

  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [category, setCategory] = useState<Category>(initialCategory);

  const [expiresAt, setExpiresAt] = useState<Date | undefined>(undefined);
  const [showDatePicker, setShowDatePicker] = useState(false);

  // Category modal
  const [catOpen, setCatOpen] = useState(false);

  // Barcode scan modal (auto fill)
  const [scanOpen, setScanOpen] = useState(false);
  const [scanned, setScanned] = useState(false);
  const [permission, requestPermission] = useCameraPermissions();

  const openScanner = async () => {
    if (!permission?.granted) {
      const res = await requestPermission();
      if (!res.granted) {
        Alert.alert("אין הרשאת מצלמה", "כדי לסרוק ברקוד צריך לאשר הרשאת מצלמה.");
        return;
      }
    }
    setScanned(false); // reset debounce
    setScanOpen(true);
  };

  const onBarcodeScanned = (result: BarcodeScanningResult) => {
    if (scanned) return; // block repeats
    setScanned(true);

    const value = String(result.data ?? "").trim();
    if (!value) {
      setScanned(false);
      return;
    }

    setBarcode(value);   // fill immediately
    setScanOpen(false);  // close camera
  };

  const onOpenDatePicker = () => setShowDatePicker(true);

  const onChangeDate = (event: any, selectedDate?: Date) => {
    if (Platform.OS === "android") {
      if (event.type === "set" && selectedDate) setExpiresAt(selectedDate);
      setShowDatePicker(false);
    } else {
      if (selectedDate) setExpiresAt(selectedDate);
    }
  };

  const locationMap: Record<
    Category,
    "FRIDGE" | "FREEZER" | "PANTRY" | "CLEANING_SUPPLIES" | "OTHER"
  > = {
    fridge: "FRIDGE",
    freezer: "FREEZER",
    pantry: "PANTRY",
    "cleaning supplies": "CLEANING_SUPPLIES",
    other: "OTHER",
  };

  const canSave = name.trim().length > 0 && Number(quantity) > 0;

  const onAdd = async () => {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "חסר בית פעיל. חזור למסך הבתים ובחר בית מחדש.");
      return;
    }
    if (!name.trim()) {
      Alert.alert("שגיאה", "חייב להיות שם מוצר");
      return;
    }
    const qty = parseInt(quantity, 10);
    if (Number.isNaN(qty) || qty <= 0) {
      Alert.alert("שגיאה", "כמות חייבת להיות מספר חיובי");
      return;
    }

    const formattedExpires = expiresAt ? expiresAt.toISOString().slice(0, 10) : undefined;

    try {
      const res = await addProduct(currentHomeId, {
        name: name.trim(),
        quantity: qty,
        barcode: barcode.trim() ? barcode.trim() : null,
        expiration_date: formattedExpires,
        location: locationMap[category],
        nickname: null,
      });

      if (res.status !== "success") {
        Alert.alert("שגיאה", res.message ?? "הוספה נכשלה");
        return;
      }

      router.back();
    } catch (e: any) {
      Alert.alert("שגיאה", e?.message ?? "הוספה נכשלה");
    }
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 8 : 0}
    >
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient
          colors={["#E5F3FF", "#F4F4F4"]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        />

        <ScreenHeader title="הוספת מוצר" onBack={() => router.back()} />

        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <ItemForm
            category={category}
            onChangeCategory={setCategory}
            onOpenCategoryPicker={() => setCatOpen(true)}
            onOpenBarcodeScanner={openScanner}
            expiresAt={expiresAt}
            showDatePicker={showDatePicker}
            onOpenDatePicker={onOpenDatePicker}
            onChangeDate={onChangeDate}
            barcode={barcode}
            name={name}
            quantity={quantity}
            onChangeBarcode={setBarcode}
            onChangeName={setName}
            onChangeQuantity={setQuantity}
          />
        </ScrollView>

        <View style={styles.bottomBar}>
          <PrimaryButton
            title="שמירה למלאי"
            onPress={onAdd}
            disabled={!canSave}
            style={[styles.saveButton, !canSave && styles.saveButtonDisabled]}
          />
        </View>

        {/* Category modal */}
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
              <TouchableOpacity onPress={() => setCatOpen(false)} activeOpacity={0.85}>
                <Ionicons name="close" size={20} color={BRAND_MUTED} />
              </TouchableOpacity>
            </View>

            {CATEGORY_OPTIONS.map((opt) => {
              const active = opt.key === category;
              return (
                <TouchableOpacity
                  key={opt.key}
                  style={[styles.sheetRow, active && styles.sheetRowActive]}
                  onPress={() => {
                    setCategory(opt.key);
                    setCatOpen(false);
                  }}
                  activeOpacity={0.85}
                >
                  <View style={styles.sheetRowRight}>
                    <View style={styles.sheetRowLabelWrap}>
                      <Text style={[styles.sheetRowText, active && styles.sheetRowTextActive]}>
                        {opt.label}
                      </Text>
                      {active && <Ionicons name="checkmark" size={18} color={BRAND_PRIMARY} />}
                    </View>

                    <Ionicons
                      name={opt.icon}
                      size={18}
                      color={active ? BRAND_PRIMARY : BRAND_MUTED}
                    />
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        </Modal>

        {/* Barcode scanner modal (auto) */}
        <Modal
          visible={scanOpen}
          animationType="slide"
          onRequestClose={() => setScanOpen(false)}
        >
          <SafeAreaView style={{ flex: 1, backgroundColor: "#000" }}>
            <View style={styles.scanHeader}>
              <TouchableOpacity onPress={() => setScanOpen(false)} activeOpacity={0.85}>
                <Ionicons name="close" size={24} color="#fff" />
              </TouchableOpacity>
              <Text style={styles.scanTitle}>סריקת ברקוד</Text>
              <View style={{ width: 24 }} />
            </View>

            <CameraView
              style={{ flex: 1 }}
              facing="back"
              onBarcodeScanned={scanned ? undefined : onBarcodeScanned}
            />

            <View style={styles.scanHintWrap}>
              <Text style={styles.scanHint}>כווני את המצלמה אל הברקוד כדי לסרוק</Text>

              <TouchableOpacity
                onPress={() => setScanned(false)}
                activeOpacity={0.85}
                style={styles.scanAgainBtn}
              >
                <Ionicons name="refresh" size={18} color="#fff" />
                <Text style={styles.scanAgainText}>סריקה מחדש</Text>
              </TouchableOpacity>
            </View>
          </SafeAreaView>
        </Modal>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F4F4F4" },
  content: { padding: 16, paddingBottom: 120, gap: 12 },

  bottomBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 16,
    backgroundColor: "rgba(244,244,244,0.92)",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  saveButton: {
    backgroundColor: BRAND_PRIMARY,
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  saveButtonDisabled: { opacity: 0.55 },

  // Category Modal
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.25)" },
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
  sheetRowActive: { backgroundColor: "#F0FAFF" },
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
  sheetRowText: { fontSize: 14, color: BRAND_TEXT, textAlign: "right" },
  sheetRowTextActive: { fontWeight: "700", color: BRAND_PRIMARY },

  scanHeader: {
    height: 56,
    paddingHorizontal: 16,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "rgba(0,0,0,0.4)",
  },
  scanTitle: { color: "#fff", fontSize: 16, fontWeight: "700" },
  scanHintWrap: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 24,
    padding: 12,
    borderRadius: 14,
    backgroundColor: "rgba(0,0,0,0.55)",
    gap: 10,
  },
  scanHint: { color: "#fff", textAlign: "center", fontSize: 13 },
  scanAgainBtn: {
    alignSelf: "center",
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.35)",
  },
  scanAgainText: { color: "#fff", fontWeight: "700" },
});
