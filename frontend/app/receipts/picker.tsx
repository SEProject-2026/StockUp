import React, { useState } from "react";
import { View, Text, StyleSheet, Image } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import * as DocumentPicker from "expo-document-picker";

import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";

export default function ReceiptPickerScreen() {
  const [fileUri, setFileUri] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [mimeType, setMimeType] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handlePickFile = async () => {
    setLoading(true);
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ["image/*", "application/pdf"],
        copyToCacheDirectory: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];

        const uri = asset.uri;
        const name = asset.name ?? "receipt";
        const type = asset.mimeType ?? "application/octet-stream";

        setFileUri(uri);
        setFileName(name);
        setMimeType(type);

        router.push({
          pathname: "./processing",
          params: {
            imageUri: uri,
            fileName: name,
            mimeType: type,
          },
        });
      }
    } catch (e) {
      console.warn("File pick failed:", e);
    } finally {
      setLoading(false);
    }
  };

  const isImage = mimeType?.startsWith("image/");

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={["#E5F3FF", "#F9FAFB"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={styles.gradient}
      />

      <ScreenHeader title="בחירת קובץ מהמכשיר" onBack={() => router.back()} />

      <View style={styles.content}>
        <Text style={styles.subtitle}>
          בחר קובץ קבלה מהמכשיר (תמונה או PDF). נזהה ממנו את הפריטים ונעדכן את
          המלאי.
        </Text>

        <PrimaryButton
          title={loading ? "טוען..." : "בחר קובץ"}
          onPress={handlePickFile}
          disabled={loading}
        />

        {fileUri && (
          <View style={styles.previewBox}>
            <Text style={styles.previewTitle}>תצוגה מקדימה / פרטי קובץ:</Text>

            {isImage ? (
              <Image source={{ uri: fileUri }} style={styles.previewImage} />
            ) : (
              <View style={styles.fileRow}>
                <View style={styles.fileIconCircle}>
                  <Ionicons name="document-outline" size={20} color="#0F172A" />
                </View>

                <View style={{ flex: 1 }}>
                  <Text style={styles.fileName} numberOfLines={1}>
                    {fileName}
                  </Text>
                  {mimeType && <Text style={styles.fileMeta}>{mimeType}</Text>}
                </View>
              </View>
            )}
          </View>
        )}
      </View>
    </SafeAreaView>
  );
}

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
  subtitle: {
    fontSize: 13,
    color: "#6B7280",
    textAlign: "right",
    marginBottom: 20,
  },
  previewBox: {
    marginTop: 24,
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
    height: 220,
    borderRadius: 12,
    backgroundColor: "#E5E7EB",
  },
  fileRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },
  fileIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#E5F3FF",
    alignItems: "center",
    justifyContent: "center",
  },
  fileName: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111827",
    textAlign: "right",
  },
  fileMeta: {
    fontSize: 11,
    color: "#6B7280",
    textAlign: "right",
    marginTop: 2,
  },
});
