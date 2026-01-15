import React from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import UploadCard from "@/src/components/receipts/UploadCard";
import InfoBox from "@/src/components/ui/InfoBox";
import ScreenHeader from "@/src/layout/ScreenHeader";

export default function ReceiptUploadScreen() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={["#E5F3FF", "#F9FAFB"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={styles.gradient}
      />

      <ScrollView contentContainerStyle={styles.container}>

        {/* Header */}
        <ScreenHeader title="העלאת קבלה" onBack={() => router.back()} />

        {/* Subtitle */}
        <Text style={styles.subtitle}>
         בחרי האם לצלם קבלה חדשה או להעלות קובץ קבלה דיגיטלי מהמכשיר.
        </Text>

        {/* Main Actions */}
        <View style={styles.actionRow}>
          <UploadCard
            icon="camera-outline"
            title="צילום קבלה"
            description="צלם תמונה חדה וברורה"
            onPress={() => router.push("./camera")}
          />

          <UploadCard
            icon="image-outline"
            title="בחירת קובץ"
            description="בחר מסמך מהמכשיר"
            onPress={() => router.push("./picker")}
          />
        </View>

        <InfoBox
          text="חשוב לוודא שהקבלה מצולמת בתאורה טובה ושכל הפריטים קריאים."
        />

      </ScrollView>
    </SafeAreaView>
  );
}

/* ---------- Styles ---------- */

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  gradient: {
    ...StyleSheet.absoluteFillObject,
  },
  container: {
    padding: 20,
    paddingBottom: 60,
  },
  subtitle: {
    fontSize: 13,
    color: "#6B7280",
    textAlign: "right",
    marginBottom: 20,
  },

  // Action Cards
  actionRow: {
    flexDirection: "row-reverse",
    justifyContent: "space-between",
    gap: 12,
  },
});

