// frontend/app/processing.tsx
import React from "react";
import {
  View,
  Text,
  StyleSheet,
  Image,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import InfoBox from "@/src/ui/InfoBox";
import ScreenHeader from "@/src/layout/ScreenHeader";

export default function ReceiptProcessingScreen() {
  const { imageUri } = useLocalSearchParams<{ imageUri?: string }>();

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={["#E5F3FF", "#F9FAFB"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={styles.gradient}
      />

      {/* HEADER */}
      <ScreenHeader title="מעבד את הקבלה" onBack={() => router.back()} />

      <View style={styles.content}>
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color="#0284C7" />
          <Text style={styles.loadingText}>
            קורא את הקבלה ומזהה את הפריטים...
          </Text>
        </View>

        {imageUri && (
          <View style={styles.previewBox}>
            <Text style={styles.previewTitle}>תמונה שעובדה:</Text>
            <Image 
              source={{ uri: imageUri }} 
              style={styles.previewImage} />
          </View>
        )}

        <InfoBox
          icon="bulb-outline"
          text="בשלב הבא תוכל לראות אילו פריטים זוהו מהקבלה, לאשר או לערוך לפני עדכון המלאי."
        />
      </View>
    </SafeAreaView>
  );
}
// ---------- Styles ---------- 
const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  gradient: {
    ...StyleSheet.absoluteFillObject,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 16,
  },
  loadingRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    marginBottom: 16,
  },
  loadingText: {
    fontSize: 13,
    color: "#4B5563",
    textAlign: "right",
  },
  previewBox: {
    marginTop: 8,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    padding: 12,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  previewTitle: {
    fontSize: 12,
    fontWeight: "600",
    color: "#111827",
    textAlign: "right",
    marginBottom: 8,
  },
  previewImage: {
    width: "100%",
    height: 500,
    borderRadius: 12,
    backgroundColor: "#E5E7EB",
  },
  primaryButton: {
    marginTop: 24,
    alignSelf: "center",
    backgroundColor: "#0284C7",
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 999,
  },
  primaryButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
});
