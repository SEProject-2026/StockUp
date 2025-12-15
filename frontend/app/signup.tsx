// frontend/app/signup.tsx
import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import ScreenHeader from "@/src/layout/ScreenHeader";
import InfoBox from "@/src/ui/InfoBox";
import AuthTextField from "@/src/ui/AuthTextField";

export default function SignupScreen() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [secure1, setSecure1] = useState(true);
  const [secure2, setSecure2] = useState(true);
  const [loading, setLoading] = useState(false);

  const validation = useMemo(() => {
    const passOk = password.length >= 8;
    const matchOk = password === confirm && confirm.length > 0;

    return {
      canSubmit: passOk && matchOk && !loading,
    };
  }, [name, email, password, confirm, loading]);

  async function onSignup() {
    if (!validation.canSubmit) {
      return;
    }

    try {
      setLoading(true);

      // TODO: כאן תחברי ל-backend (FastAPI) / auth service
      // await authApi.signup({ fullName, email, password });

      await new Promise((r) => setTimeout(r, 700));

      Alert.alert("נרשמת בהצלחה", "אפשר להתחבר עכשיו", [
        { text: "להתחברות", onPress: () => router.replace("/login") },
      ]);
    } catch (e: any) {
      Alert.alert("הרשמה נכשלה", e?.message ?? "נסה/י שוב");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient
        colors={["#E5F3FF", "#F9FAFB"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={styles.gradient}
      />

      <ScreenHeader title="הרשמה" onBack={() => router.back()} />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView style={styles.content}>
          <View style={styles.hero}>
            <View style={styles.iconCircle}>
              <Ionicons name="person-add-outline" size={20} color="#0284C7" />
            </View>
            <Text style={styles.heroTitle}>בואו נתחיל</Text>
            <Text style={styles.heroSubtitle}>
              צרו חשבון כדי להתחיל לנהל את מלאי הבית שלכם ולצרוך בצורה נבונה
            </Text>
          </View>

          <View style={styles.card}>

            <AuthTextField
              label="שם"
              value={name}
              onChangeText={setName}
              leftIcon="person-circle-outline"
              autoCapitalize="none"
            />

            <AuthTextField
              label="אימייל"
              value={email}
              onChangeText={setEmail}
              placeholder="example@example.com"
              leftIcon="mail-outline"
              autoCapitalize="none"
            />
            <AuthTextField
              label="סיסמה"
              value={password}
              onChangeText={setPassword}
              placeholder="לפחות 8 תווים"
              leftIcon="key-outline"
              secureTextEntry={secure1}
              onToggleSecure={() => setSecure1((p) => !p)}
              autoCapitalize="none"
            />

            <AuthTextField 
              label="אימות סיסמה"
              value={confirm}
              onChangeText={setConfirm}
              placeholder="חזרה על הסיסמה"
              leftIcon="checkmark-circle-outline"
              secureTextEntry={secure2}
              onToggleSecure={() => setSecure2((p) => !p)}
              autoCapitalize="none"
            />

            <TouchableOpacity
              onPress={onSignup}
              disabled={!validation.canSubmit}
              style={[
                styles.primaryBtn,
                !validation.canSubmit && styles.primaryBtnDisabled,
              ]}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <>
                  <Ionicons name="create-outline" size={18} color="#FFFFFF" />
                  <Text style={styles.primaryBtnText}>צרו חשבון</Text>
                </>
              )}
            </TouchableOpacity>

            <View style={styles.dividerRow}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>כבר יש לך חשבון?</Text>
              <View style={styles.divider} />
            </View>

            <TouchableOpacity
              onPress={() => router.replace("/login")}
              style={styles.secondaryBtn}
            >
              <Text style={styles.secondaryBtnText}>להתחברות</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F9FAFB" },
  gradient: { ...StyleSheet.absoluteFillObject },
  content: { flex: 1, paddingHorizontal: 20, paddingTop: 16, gap: 12 },

  hero: { alignItems: "flex-end", gap: 6, marginBottom: 4 },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 999,
    backgroundColor: "#E0F2FE",
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "flex-end",
  },
  heroTitle: { fontSize: 18, fontWeight: "800", color: "#111827", textAlign: "right" },
  heroSubtitle: { fontSize: 13, color: "#6B7280", textAlign: "right", lineHeight: 18 },

  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 18,
    padding: 14,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },

  hint: {
    marginTop: 10,
    fontSize: 12,
    color: "#EF4444",
    textAlign: "right",
    fontWeight: "600",
  },

  primaryBtn: {
    marginTop: 14,
    height: 46,
    borderRadius: 999,
    backgroundColor: "#0284C7",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  primaryBtnDisabled: { opacity: 0.5 },
  primaryBtnText: { color: "#FFFFFF", fontSize: 14, fontWeight: "800" },

  dividerRow: { flexDirection: "row", alignItems: "center", gap: 10, marginVertical: 12 },
  divider: { flex: 1, height: 1, backgroundColor: "#E5E7EB" },
  dividerText: { fontSize: 12, color: "#6B7280" },

  secondaryBtn: {
    height: 44,
    borderRadius: 999,
    backgroundColor: "#EEF2FF",
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryBtnText: { color: "#1D4ED8", fontSize: 13, fontWeight: "800" },
});
