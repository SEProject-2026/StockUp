import React, { useRef, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
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

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === "granted");
    })();
  }, []);

  const handleRequestPermission = async () => {
    setIsRequestingPermission(true);
    try {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === "granted");
    } finally {
      setIsRequestingPermission(false);
    }
  };

  const handlePickFromGallery = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const pickedUri = result.assets[0].uri;
        router.push({
          pathname: "./processing",
          params: { imageUri: pickedUri },
        });
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
        router.push({
          pathname: "./processing",
          params: { imageUri: photo.uri },
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

        <TouchableOpacity
        style={styles.galleryButton}
        onPress={handlePickFromGallery}
        >
        <Ionicons name="images-outline" size={22} color="#111827" />
        </TouchableOpacity>

        {/* camera overlay */}
        <View style={styles.cameraOverlayTop}>
          {/* flash */}
          <TouchableOpacity
            style={styles.iconPill}
            onPress={handleToggleTorch}
          >
            <Ionicons
              name={torchOn ? "flash" : "flash-outline"}
              size={18}
              color={torchOn ? "#FCD34D" : "#E5E7EB"}
            />
            <Text style={styles.iconPillText}>
              {torchOn ? "פלאש דולק" : "פלאש כבוי"}
            </Text>
          </TouchableOpacity>
        </View>

        {/*zoom*/}
        <View style={styles.zoomControls}>
          <TouchableOpacity
            style={styles.zoomButton}
            onPress={() => changeZoom(0.1)}
          >
            <Ionicons name="add" size={18} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.zoomLabel}>
            {Math.round(zoom * 10) / 10 + 1}x
          </Text>
          <TouchableOpacity
            style={styles.zoomButton}
            onPress={() => changeZoom(-0.1)}
          >
            <Ionicons name="remove" size={18} color="#111827" />
          </TouchableOpacity>
        </View>
      </View>

      {/* HINT */}
      <Text style={styles.hintText}>
        ודא שכל הקבלה בתוך המסגרת, בתאורה טובה וללא השתקפויות.
      </Text>

      {/* CAPTURE BUTTON */}
      <View style={styles.captureRow}>
        <View style={{ flex: 1 }} />
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
        <View style={{ flex: 1 }} />
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
  cameraWrapper: {
    flex: 1,
    marginHorizontal: 16,
    marginTop: 8,
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: "#111827",
  },
  camera: {
    flex: 1,
  },

  // camera overlay
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
  iconPillText: {
    fontSize: 11,
    color: "#E5E7EB",
  },
  roundIconButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
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
  zoomLabel: {
    fontSize: 11,
    fontWeight: "600",
    color: "#111827",
  },

  hintText: {
    textAlign: "center",
    fontSize: 12,
    color: "#6B7280",
    marginTop: 10,
    paddingHorizontal: 24,
  },
  captureRow: {
    paddingVertical: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  captureButtonOuter: {
    width: 76,
    height: 76,
    borderRadius: 38,
    borderWidth: 3,
    borderColor: "#BFDBFE",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#EFF6FF",
  },
  captureButtonInner: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: "#0284C7",
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
  permissionButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
    fontSize: 14,
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

});
