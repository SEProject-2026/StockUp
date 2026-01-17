// frontend/app/processing.tsx
import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, Image, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useLocalSearchParams, useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";

import InfoBox from "@/src/components/ui/InfoBox";
import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";

import { getSelectedHomeId } from "../home/selected-home";
import { scanReceipt } from "@/src/api/stock";
import { setLastScannedReceipt } from "@/src/context/receipt-scan-store";

import * as FileSystem from "expo-file-system";

export default function ReceiptProcessingScreen() {
  const router = useRouter();

  const { imageUri, fileName, mimeType } = useLocalSearchParams<{
    imageUri?: string;
    fileName?: string;
    mimeType?: string;
  }>();

  const [homeId, setHomeId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [started, setStarted] = useState(false);

async function ensureFileUri(uri: string): Promise<string> {
  if (!uri) return uri;

  if (uri.startsWith("file://")) return uri;

  if (uri.startsWith("content://")) {
    const clean = uri.split("?")[0].split("#")[0];
    const extMatch = clean.match(/\.([a-zA-Z0-9]+)$/);
    const ext = (extMatch?.[1] ?? "jpg").toLowerCase();

    const baseDir =
      ((FileSystem as any).cacheDirectory as string | null) ??
      ((FileSystem as any).documentDirectory as string | null) ??
      null;

    if (!baseDir) {
      throw new Error("No writable directory (cache/document) available");
    }

    const dest = `${baseDir}upload_${Date.now()}.${ext}`;

    await FileSystem.copyAsync({ from: uri, to: dest });
    return dest; 
  }

  return uri;
}

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const id = await getSelectedHomeId();
        if (!id) throw new Error("לא נבחר בית פעיל. חזרי למסך הבית ובחרי בית.");
        if (mounted) setHomeId(id);
      } catch (e: any) {
        if (mounted) setError(e?.message ?? "שגיאה בטעינת בית נבחר");
      }
    })();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (!homeId || !imageUri) return;

    let isMounted = true;

    (async () => {
      try {
        const safeUri = await ensureFileUri(imageUri);

        const res = await scanReceipt(homeId, {
          fileUri: safeUri,
          fileName: fileName ?? null,
          mimeType: mimeType ?? null,
        });

        if (!isMounted) return;

        const payload = res?.data;
        if (!payload) throw new Error("scanReceipt returned empty payload");

        setLastScannedReceipt(payload);
        router.replace("/receipts/review");
      } catch (e: any) {
        if (!isMounted) return;
        setError(e?.message ?? "Scanning failed");
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [homeId, imageUri]);

  const onRetry = () => {
    setError(null);
    setStarted(false);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={["#E5F3FF", "#F9FAFB"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={styles.gradient}
      />

      <ScreenHeader title="מעבד את הקבלה" onBack={() => router.back()} />

      <View style={styles.content}>
        {!error ? (
          <>
            <View style={styles.loadingRow}>
              <ActivityIndicator size="small" color="#0284C7" />
              <Text style={styles.loadingText}>קורא את הקבלה ומזהה את הפריטים...</Text>
            </View>

            {imageUri && (
              <View style={styles.previewBox}>
                <Text style={styles.previewTitle}>תמונה שעובדה:</Text>
                <Image source={{ uri: imageUri }} style={styles.previewImage} />
              </View>
            )}

            <InfoBox
              icon="bulb-outline"
              text="בשלב הבא תוכל לראות אילו פריטים זוהו מהקבלה, לאשר או לערוך לפני עדכון המלאי."
            />
          </>
        ) : (
          <>
            <InfoBox icon="warning-outline" text={`שגיאה בסריקה: ${error}`} />
            <View style={{ marginTop: 16 }}>
              <PrimaryButton title="נסה שוב" onPress={onRetry} />
            </View>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F9FAFB" },
  gradient: { ...StyleSheet.absoluteFillObject },
  content: { flex: 1, paddingHorizontal: 20, paddingTop: 16 },
  loadingRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    marginBottom: 16,
  },
  loadingText: { fontSize: 13, color: "#4B5563", textAlign: "right" },
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
});
