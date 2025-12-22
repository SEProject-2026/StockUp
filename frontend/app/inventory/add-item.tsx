import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { useInventory, Category } from "../../src/context/inventory-context";
import { LinearGradient } from "expo-linear-gradient";

import ItemForm from "@/src/components/add-item/ItemForm";
import PrimaryButton from "@/src/ui/PrimaryButton";
import ScreenHeader from "@/src/layout/ScreenHeader";
import { addProduct } from "@/src/api/stock";

const BRAND_PRIMARY = "#0284C7";
const BRAND_TEXT = "#111827";

export default function AddItemScreen() {
  const { addItem } = useInventory();
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  const currentHomeId = homeId ? String(homeId) : "";

  const [barcode, setBarcode] = useState("");
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [category, setCategory] = useState<Category>("fridge");
  const [expiresAt, setExpiresAt] = useState<Date | undefined>(undefined);
  const [showDatePicker, setShowDatePicker] = useState(false);

  const onChangeDate = (event: any, selectedDate?: Date) => {
    // On Android: close only when the user presses "OK"
    if (Platform.OS === "android") {
      if (event.type === "set" && selectedDate) {
        setExpiresAt(selectedDate);
      }
      setShowDatePicker(false);
    } else {
      if (selectedDate) {
        setExpiresAt(selectedDate);
      }
    }
  };
  const locationMap: Record<string, "FRIDGE" | "FREEZER" | "PANTRY"> = {
    fridge: "FRIDGE",
    freezer: "FREEZER",
    pantry: "PANTRY",
  };


   const onAdd = async () => {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "חסר בית פעיל. חזרי למסך הבתים ובחרי בית מחדש.");
      return;
    }

    if (!name.trim()) {
      Alert.alert("שגיאה", "חייב להיות שם מוצר");
      return;
    }
    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      Alert.alert("שגיאה", "כמות חייבת להיות מספר חיובי");
      return;
    }

    const formattedExpires = expiresAt
      ? expiresAt.toISOString().slice(0, 10)
      : undefined;

   console.log("ADD homeId:", currentHomeId);


    const res = await addProduct(currentHomeId, {
        name: name.trim(),
        quantity: qty,
        barcode: barcode.trim() ? barcode.trim() : null,
        expiration_date: formattedExpires,
        location: locationMap[category],
        nickname: null,
      });
    console.log("ADD sent location:", locationMap[category]);
    console.log("ADD response location:", (res as any)?.data?.location);

      if (res.status !== "success") {
        Alert.alert("שגיאה", res.message ?? "הוספה נכשלה");
        return;
      }

      router.back();
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 80 : 0}
    >
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient
          colors={["#E5F3FF", "#F4F4F4"]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={styles.gradientBackground}
          pointerEvents="none"
        />

        {/* Header */}
        <ScreenHeader
          title="הוספת מוצר"
          onBack={() => router.back()}
        />

        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          <ItemForm
            category={category}
            onChangeCategory={setCategory}
            expiresAt={expiresAt}
            showDatePicker={showDatePicker}
            onOpenDatePicker={() => setShowDatePicker(true)}
            onChangeDate={onChangeDate}
            barcode={barcode}
            name={name}
            quantity={quantity}
            onChangeBarcode={setBarcode}
            onChangeName={setName}
            onChangeQuantity={setQuantity}
          />
        </ScrollView>

        {/* save button */}
      <PrimaryButton title="שמירה למלאי" onPress={onAdd} style={styles.addButton} />

      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

/* ---------- STYLES  ---------- */

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F4F4F4",
  },
  gradientBackground: {
    ...StyleSheet.absoluteFillObject,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 4,
    justifyContent: "space-between",
  },
  headerIconButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 2,
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: BRAND_TEXT,
  },
  container: {
    padding: 16,
    paddingBottom: 90,
    gap: 12,
  },
  addButton: {
    //position: "absolute",
    left: 16,
    right: 16,
    bottom: 16,
    backgroundColor: BRAND_PRIMARY,
    paddingVertical: 14,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
    gap: 8,
    shadowColor: "#000",
    shadowOpacity: 0.16,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 4,
  },
  addButtonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
});
