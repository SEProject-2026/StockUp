import React, { useState } from "react";
import { Modal, SafeAreaView, View, Text, StyleSheet, TouchableOpacity, Alert } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { CameraView, useCameraPermissions, BarcodeScanningResult } from "expo-camera";

export default function BarcodeScannerModal(props: {
  open: boolean;
  onClose: () => void;
  onScanned: (value: string) => void;
}) {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);

  async function ensurePermission() {
    if (permission?.granted) return true;
    const res = await requestPermission();
    return !!res.granted;
  }

  const onBarcodeScanned = (result: BarcodeScanningResult) => {
    if (scanned) return;
    setScanned(true);

    const value = String(result.data ?? "").trim();
    if (!value) {
      setScanned(false);
      return;
    }

    props.onScanned(value);
    props.onClose();
  };

  return (
    <Modal visible={props.open} animationType="slide" onRequestClose={props.onClose}>
      <SafeAreaView style={{ flex: 1, backgroundColor: "#000" }}>
        <View style={styles.header}>
          <TouchableOpacity onPress={props.onClose} activeOpacity={0.85}>
            <Ionicons name="close" size={24} color="#fff" />
          </TouchableOpacity>
          <Text style={styles.title}>סריקת ברקוד</Text>
          <View style={{ width: 24 }} />
        </View>

        <CameraGate ensurePermission={ensurePermission} />

        <CameraView
          style={{ flex: 1 }}
          facing="back"
          onBarcodeScanned={scanned ? undefined : onBarcodeScanned}
        />

        <View style={styles.hintWrap}>
          <Text style={styles.hint}>כווני את המצלמה אל הברקוד כדי לסרוק</Text>
          <TouchableOpacity onPress={() => setScanned(false)} activeOpacity={0.85} style={styles.againBtn}>
            <Ionicons name="refresh" size={18} color="#fff" />
            <Text style={styles.againText}>סריקה מחדש</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </Modal>
  );
}

function CameraGate({ ensurePermission }: { ensurePermission: () => Promise<boolean> }) {
  React.useEffect(() => {
    (async () => {
      const ok = await ensurePermission();
      if (!ok) {
        Alert.alert("אין הרשאת מצלמה", "כדי לסרוק ברקוד צריך לאשר הרשאת מצלמה.");
      }
    })();
  }, [ensurePermission]);
  return null;
}

const styles = StyleSheet.create({
  header: {
    height: 56,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "rgba(0,0,0,0.4)",
  },
  title: { color: "#fff", fontSize: 16, fontWeight: "700" },
  hintWrap: {
    position: "absolute",
    left: 16,
    right: 16,
    bottom: 24,
    padding: 12,
    borderRadius: 14,
    backgroundColor: "rgba(0,0,0,0.55)",
    gap: 10,
  },
  hint: { color: "#fff", textAlign: "center", fontSize: 13 },
  againBtn: {
    alignSelf: "center",
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.35)",
  },
  againText: { color: "#fff", fontWeight: "700" },
});
