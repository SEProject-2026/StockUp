import React, { useRef, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Image,
  Dimensions,
  Alert,
} from "react-native";
import * as ImageManipulator from 'expo-image-manipulator';
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { Camera, CameraView } from "expo-camera";
import * as ScreenOrientation from "expo-screen-orientation";
import ScreenHeader from "@/src/layout/ScreenHeader";

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const ASPECT_RATIO = 4 / 3;
const CAMERA_WIDTH = SCREEN_WIDTH - 24;
const FULL_CAMERA_HEIGHT = CAMERA_WIDTH * ASPECT_RATIO;
const ONION_SKIN_HEIGHT = 80;

export default function ReceiptCameraScreen() {
  const cameraRef = useRef<any>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [isRotating, setIsRotating] = useState<string | null>(null);
  const [torchOn, setTorchOn] = useState(false);
  const [images, setImages] = useState<string[]>([]); // נשמר בסדר: [ראשון, שני, שלישי...]

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === "granted");
      await ScreenOrientation.lockAsync(ScreenOrientation.OrientationLock.PORTRAIT_UP);
    })();
    return () => { ScreenOrientation.unlockAsync(); };
  }, []);

  const handleCapture = async () => {
    if (!cameraRef.current || isCapturing) return;
    try {
      setIsCapturing(true);
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        skipMetadata: true,
      });

      if (photo?.uri) {
        setImages((prev) => [...prev, photo.uri]);
      }
    } catch (e) {
      console.warn("Capture error:", e);
    } finally {
      setIsCapturing(false);
    }
  };

  const rotateImage = async (uri: string) => {
    try {
      setIsRotating(uri);
      const result = await ImageManipulator.manipulateAsync(
        uri,
        [{ rotate: 90 }],
        { compress: 0.8, format: ImageManipulator.SaveFormat.JPEG }
      );
      setImages((prev) => prev.map(img => img === uri ? result.uri : img));
    } catch (e) {
      Alert.alert("שגיאה", "לא ניתן לסובב את התמונה");
    } finally {
      setIsRotating(null);
    }
  };

  if (hasPermission === null) return <SafeAreaView style={styles.safeArea} />;

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient colors={["#E5F3FF", "#F9FAFB"]} style={styles.gradient} />
      <ScreenHeader title="צילום קבלה" onBack={() => router.back()} />

      <View style={[styles.cameraContainer, { height: FULL_CAMERA_HEIGHT }]}>
        
        {/* Onion Skin - מציג את התמונה האחרונה שצולמה */}
        {images.length > 0 && (
          <View style={[styles.onionSkinStatic, { height: ONION_SKIN_HEIGHT }]}>
            <Image 
              source={{ uri: images[images.length - 1] }} 
              style={[styles.onionSkinImage, { height: FULL_CAMERA_HEIGHT }]} 
              resizeMode="stretch" 
            />
            <View style={styles.onionLabelTop}>
              <Ionicons name="link-outline" size={10} color="#FFF" style={{ marginRight: 4 }} />
              <Text style={styles.onionText}>סוף חלק קודם</Text>
            </View>
            <View style={styles.dividerLine} />
          </View>
        )}

        <View style={{ flex: 1, backgroundColor: '#000' }}>
          <CameraView
            ref={cameraRef}
            style={StyleSheet.absoluteFill}
            facing="back"
            ratio="4:3"
            enableTorch={torchOn}
          />
        </View>

        <View style={styles.cameraOverlay}>
          <TouchableOpacity style={styles.pill} onPress={() => setTorchOn(!torchOn)}>
            <Ionicons name={torchOn ? "flash" : "flash-outline"} size={16} color={torchOn ? "#FCD34D" : "#FFF"} />
          </TouchableOpacity>
          <View style={styles.pill}>
            <Text style={styles.pillText}>{images.length} תמונות</Text>
          </View>
        </View>
      </View>

      {/* Preview Section - מציג ויזואלית הפוך (החדשה ראשונה), אבל המערך עצמו נשאר מסודר */}
      <View style={styles.thumbnailSection}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.thumbScroll}>
          {[...images].reverse().map((uri) => (
            <View key={uri} style={[styles.thumbWrapper, { width: 70, height: 70 * ASPECT_RATIO }]}>
              <Image source={{ uri }} style={styles.thumb} resizeMode="cover" />
              
              <TouchableOpacity style={styles.removeBtn} onPress={() => setImages(prev => prev.filter(u => u !== uri))}>
                <Ionicons name="close-circle" size={20} color="#EF4444" />
              </TouchableOpacity>

              <TouchableOpacity 
                style={styles.rotateBtn} 
                onPress={() => rotateImage(uri)}
                disabled={isRotating === uri}
              >
                {isRotating === uri ? (
                  <ActivityIndicator size="small" color="#0284C7" />
                ) : (
                  <Ionicons name="refresh-circle" size={22} color="#0284C7" />
                )}
              </TouchableOpacity>
            </View>
          ))}
        </ScrollView>
      </View>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.mainAction, images.length === 0 && styles.disabledBtn]}
          onPress={() => {
            // כאן המערך 'images' נשלח בסדר הכרונולוגי המקורי שלו
            router.push({ pathname: "./processing", params: { imageUris: JSON.stringify(images) } });
          }}
          disabled={images.length === 0}
        >
          <Text style={styles.mainActionText}>המשך ({images.length})</Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.captureBtn} onPress={handleCapture} disabled={isCapturing}>
          <View style={styles.captureInner}>
            {isCapturing ? <ActivityIndicator color="#FFF" /> : <Ionicons name="camera" size={28} color="#FFF" />}
          </View>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F9FAFB" },
  gradient: { ...StyleSheet.absoluteFillObject },
  cameraContainer: { marginHorizontal: 12, marginTop: 10, borderRadius: 24, overflow: 'hidden', backgroundColor: '#000', flexDirection: 'column' },
  onionSkinStatic: { width: '100%', overflow: 'hidden', zIndex: 10, position: 'relative' },
  onionSkinImage: { width: '100%', position: 'absolute', bottom: 0, opacity: 0.8 },
  dividerLine: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, backgroundColor: '#0284C7' },
  onionLabelTop: { position: 'absolute', top: 6, left: 8, backgroundColor: 'rgba(2, 132, 199, 0.85)', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 6, flexDirection: 'row', alignItems: 'center', zIndex: 11 },
  onionText: { color: '#FFF', fontSize: 9, fontWeight: '700' },
  cameraOverlay: { position: 'absolute', bottom: 15, left: 15, right: 15, flexDirection: 'row', justifyContent: 'space-between' },
  pill: { backgroundColor: 'rgba(0,0,0,0.5)', padding: 8, borderRadius: 20, flexDirection: 'row', alignItems: 'center', gap: 5 },
  pillText: { color: '#FFF', fontSize: 11, fontWeight: 'bold' },
  thumbnailSection: { height: 120, marginTop: 15 },
  thumbScroll: { paddingHorizontal: 15, gap: 12 },
  thumbWrapper: { borderRadius: 10, overflow: 'hidden', backgroundColor: '#000', position: 'relative' },
  thumb: { width: '100%', height: '100%' },
  removeBtn: { position: 'absolute', top: 0, right: 0, zIndex: 10 },
  rotateBtn: { position: 'absolute', bottom: 2, right: 2, zIndex: 10, backgroundColor: 'rgba(255,255,255,0.9)', borderRadius: 12 },
  footer: { flexDirection: 'row', padding: 20, alignItems: 'center', gap: 15, paddingBottom: 40 },
  mainAction: { flex: 1, height: 55, backgroundColor: '#0284C7', borderRadius: 15, justifyContent: 'center', alignItems: 'center' },
  mainActionText: { color: '#FFF', fontWeight: 'bold', fontSize: 16 },
  disabledBtn: { opacity: 0.5 },
  captureBtn: { width: 70, height: 70, borderRadius: 35, borderWidth: 4, borderColor: '#0284C7', justifyContent: 'center', alignItems: 'center' },
  captureInner: { width: 55, height: 55, borderRadius: 27.5, backgroundColor: '#0284C7', justifyContent: 'center', alignItems: 'center' }
});