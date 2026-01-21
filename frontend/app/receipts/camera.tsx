import React, { useRef, useState, useEffect, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Image,
  Alert,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { Camera, CameraView } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import ScreenHeader from "@/src/layout/ScreenHeader";

export default function ReceiptCameraScreen() {
  const CameraViewAny = CameraView as any;
  const cameraRef = useRef<any>(null);

  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isRequestingPermission, setIsRequestingPermission] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);

  const [zoom, setZoom] = useState(0);
  const [torchOn, setTorchOn] = useState(false);

  // NEW: selected images list
  const [images, setImages] = useState<string[]>([]);

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === "granted");
    })();
  }, []);

  const imageCount = images.length;

  const canContinue = useMemo(() => imageCount > 0, [imageCount]);

  const handleRequestPermission = async () => {
    setIsRequestingPermission(true);
    try {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === "granted");
    } finally {
      setIsRequestingPermission(false);
    }
  };

  const dedupeAppend = (uris: string[]) => {
    setImages((prev) => {
      const s = new Set(prev);
      for (const u of uris) s.add(u);
      return Array.from(s);
    });
  };

  const handlePickFromGallery = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.8,
        allowsMultipleSelection: true,
        selectionLimit: 10,
      });

      if (!result.canceled && result.assets?.length) {
        const pickedUris = result.assets.map((a) => a.uri);
        dedupeAppend(pickedUris);
      }
    } catch (e) {
      console.warn("Failed to pick image:", e);
    }
  };

  const handleCapture = async () => {
    if (!cameraRef.current || isCapturing) return;
    try {
      setIsCapturing(true);
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.7,
      });

      if (photo?.uri) {
        // add to list (top)
        setImages((prev) => {
          if (prev.includes(photo.uri)) return prev;
          return [photo.uri, ...prev];
        });
      }
    } catch (e) {
      console.warn("Failed to capture:", e);
    } finally {
      setIsCapturing(false);
    }
  };

  const handleToggleTorch = () => {
    setTorchOn((prev) => !prev);
  };

  const changeZoom = (delta: number) => {
    setZoom((prev) => {
      const next = Math.min(1, Math.max(0, prev + delta));
      return Number(next.toFixed(3));
    });
  };

  const removeImage = (uri: string) => {
    setImages((prev) => prev.filter((u) => u !== uri));
  };

  const clearAll = () => {
    if (images.length === 0) return;
    Alert.alert("נקה הכל?", "למחוק את כל התמונות שנבחרו?", [
      { text: "ביטול", style: "cancel" },
      { text: "נקה", style: "destructive", onPress: () => setImages([]) },
    ]);
  };

  const goToProcessing = () => {
    if (!canContinue) return;

    // Option: pass as JSON string
    router.push({
      pathname: "./processing",
      params: {
        imageUris: JSON.stringify(images),
      },
    });
  };

  // permission state
  if (hasPermission === null) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient
          colors={["#E5F3FF", "#F9FAFB"]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={styles.gradient}
        />
        <View style={styles.permissionContainer}>
          <ActivityIndicator color="#0284C7" />
          <Text style={[styles.permissionText, { marginTop: 12 }]}>
            בודק הרשאות מצלמה...
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!hasPermission) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient
          colors={["#E5F3FF", "#F9FAFB"]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 1 }}
          style={styles.gradient}
        />
        <View style={styles.permissionContainer}>
          <Text style={styles.permissionTitle}>גישה למצלמה חסומה</Text>
          <Text style={styles.permissionText}>
            כדי לצלם קבלה, יש לאשר גישה למצלמה בהגדרות המכשיר.
          </Text>
          <TouchableOpacity
            style={styles.permissionButton}
            onPress={handleRequestPermission}
            disabled={isRequestingPermission}
          >
            {isRequestingPermission ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.permissionButtonText}>אישור גישה</Text>
            )}
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={["#E5F3FF", "#F9FAFB"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={styles.gradient}
      />

      {/* HEADER */}
      <ScreenHeader title="צילום קבלה" onBack={() => router.back()} />

      {/* CAMERA + OVERLAY */}
      <View style={styles.cameraWrapper}>
        <CameraViewAny
          ref={cameraRef}
          style={styles.camera}
          facing={"back"}
          zoom={zoom}
          enableTorch={torchOn}
          autofocus="on"
          mode="picture"
        />

        {/* gallery */}
        <TouchableOpacity style={styles.galleryButton} onPress={handlePickFromGallery}>
          <Ionicons name="images-outline" size={22} color="#111827" />
        </TouchableOpacity>

        {/* camera overlay */}
        <View style={styles.cameraOverlayTop}>
          <TouchableOpacity style={styles.iconPill} onPress={handleToggleTorch}>
            <Ionicons
              name={torchOn ? "flash" : "flash-outline"}
              size={18}
              color={torchOn ? "#FCD34D" : "#E5E7EB"}
            />
            <Text style={styles.iconPillText}>
              {torchOn ? "פלאש דולק" : "פלאש כבוי"}
            </Text>
          </TouchableOpacity>

          {/* counter + clear */}
          <View style={styles.rightPills}>
            <View style={styles.countPill}>
              <Ionicons name="images" size={16} color="#E5E7EB" />
              <Text style={styles.countPillText}>{imageCount}</Text>
            </View>

            <TouchableOpacity
              style={[styles.clearPill, images.length === 0 && { opacity: 0.5 }]}
              onPress={clearAll}
              disabled={images.length === 0}
            >
              <Ionicons name="trash-outline" size={16} color="#E5E7EB" />
            </TouchableOpacity>
          </View>
        </View>

        {/* zoom */}
        <View style={styles.zoomControls}>
          <TouchableOpacity style={styles.zoomButton} onPress={() => changeZoom(0.1)}>
            <Ionicons name="add" size={18} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.zoomLabel}>{Math.round(zoom * 10) / 10 + 1}x</Text>
          <TouchableOpacity style={styles.zoomButton} onPress={() => changeZoom(-0.1)}>
            <Ionicons name="remove" size={18} color="#111827" />
          </TouchableOpacity>
        </View>

        {/* thumbnails */}
        {images.length > 0 && (
          <View style={styles.thumbBarWrap}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.thumbBar}>
              {images.map((uri) => (
                <View key={uri} style={styles.thumbItem}>
                  <Image source={{ uri }} style={styles.thumbImg} />
                  <TouchableOpacity style={styles.thumbRemove} onPress={() => removeImage(uri)}>
                    <Ionicons name="close" size={14} color="#111827" />
                  </TouchableOpacity>
                </View>
              ))}
            </ScrollView>
          </View>
        )}
      </View>

      {/* HINT */}
      <Text style={styles.hintText}>
        אפשר לצלם כמה תמונות. ודא שכל הקבלה בתוך המסגרת, בתאורה טובה וללא השתקפויות.
      </Text>

      {/* ACTIONS */}
      <View style={styles.bottomRow}>
        <TouchableOpacity
          style={[styles.continueButton, !canContinue && { opacity: 0.5 }]}
          onPress={goToProcessing}
          disabled={!canContinue}
        >
          <Ionicons name="arrow-forward" size={18} color="#FFFFFF" />
          <Text style={styles.continueButtonText}>המשך לעיבוד</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.captureButtonOuter}
          onPress={handleCapture}
          disabled={isCapturing}
        >
          <View style={styles.captureButtonInner}>
            {isCapturing ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Ionicons name="camera-outline" size={22} color="#FFFFFF" />
            )}
          </View>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F9FAFB" },
  gradient: { ...StyleSheet.absoluteFillObject },

  cameraWrapper: {
    flex: 1,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: "#111827",
  },
  camera: { flex: 1 },

  cameraOverlayTop: {
    position: "absolute",
    top: 10,
    left: 10,
    right: 10,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },

  iconPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    backgroundColor: "rgba(15,23,42,0.7)",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    gap: 6,
  },
  iconPillText: { fontSize: 11, color: "#E5E7EB" },

  rightPills: { flexDirection: "row", gap: 8, alignItems: "center" },
  countPill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: "rgba(15,23,42,0.7)",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  countPillText: { fontSize: 12, fontWeight: "700", color: "#E5E7EB" },

  clearPill: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: "rgba(15,23,42,0.7)",
    alignItems: "center",
    justifyContent: "center",
  },

  zoomControls: {
    position: "absolute",
    right: 10,
    top: "40%",
    alignItems: "center",
    gap: 6,
    backgroundColor: "rgba(248,250,252,0.9)",
    paddingVertical: 8,
    paddingHorizontal: 6,
    borderRadius: 999,
  },
  zoomButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
  },
  zoomLabel: { fontSize: 11, fontWeight: "600", color: "#111827" },

  hintText: {
    textAlign: "center",
    fontSize: 12,
    color: "#6B7280",
    marginTop: 10,
    paddingHorizontal: 24,
  },

  bottomRow: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },

  continueButton: {
    flex: 1,
    height: 50,
    borderRadius: 14,
    backgroundColor: "#0284C7",
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  continueButtonText: { color: "#FFFFFF", fontWeight: "700", fontSize: 14 },

  captureButtonOuter: {
    width: 66,
    height: 66,
    borderRadius: 33,
    borderWidth: 3,
    borderColor: "#BFDBFE",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#EFF6FF",
  },
  captureButtonInner: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "#0284C7",
    alignItems: "center",
    justifyContent: "center",
  },

  galleryButton: {
    position: "absolute",
    bottom: 30,
    left: 30,
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: "#F8FAFC",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOpacity: 0.15,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
  },

  // thumbnail bar
  thumbBarWrap: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingBottom: 10,
    paddingTop: 10,
    backgroundColor: "rgba(17,24,39,0.45)",
  },
  thumbBar: {
    paddingHorizontal: 10,
    gap: 10,
    alignItems: "center",
  },
  thumbItem: {
    width: 58,
    height: 74,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "rgba(255,255,255,0.08)",
  },
  thumbImg: { width: "100%", height: "100%" },
  thumbRemove: {
    position: "absolute",
    top: 6,
    right: 6,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: "rgba(248,250,252,0.95)",
    alignItems: "center",
    justifyContent: "center",
  },

  // permission
  permissionContainer: {
    flex: 1,
    padding: 24,
    justifyContent: "center",
    alignItems: "center",
  },
  permissionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
  },
  permissionText: {
    fontSize: 13,
    color: "#6B7280",
    textAlign: "center",
    marginBottom: 16,
  },
  permissionButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: "#0284C7",
  },
  permissionButtonText: { color: "#FFFFFF", fontWeight: "600", fontSize: 14 },
});
