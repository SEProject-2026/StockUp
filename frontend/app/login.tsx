import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
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

export default function LoginScreen() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [secure, setSecure] = useState(true);
  const [loading, setLoading] = useState(false);

  const canSubmit = useMemo(() => {
    const u = username.trim();
    return u.length > 3 && password.length >= 6 && !loading;
  }, [username, password, loading]);

  async function onLogin() {
    if (!canSubmit) return;

    try {
      setLoading(true);

      // backend

      await new Promise((r) => setTimeout(r, 650));

      router.replace("/home"); 
    } catch (e: any) {
      Alert.alert("התחברות נכשלה", e?.message ?? "בדוק אימייל/סיסמה ונסה שוב");
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

      <ScreenHeader title="התחברות" onBack={() => router.back()} />

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView style={styles.content}>
          <View style={styles.hero}>
            <View style={styles.iconCircle}>
              <Ionicons name="lock-closed-outline" size={20} color="#0284C7" />
            </View>
            <Text style={styles.heroTitle}>ברוך שובך</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.label}>שם משתמש</Text>
            <View style={styles.inputWrap}>
              <Ionicons name="person-outline" size={18} color="#6B7280" />
              <TextInput
                value={username}
                onChangeText={setUsername}
                placeholderTextColor="#9CA3AF"
                keyboardType="default"
                autoCapitalize="none"
                autoCorrect={false}
                textAlign="right"
                style={styles.input}
              />
            </View>

            <Text style={[styles.label, { marginTop: 12 }]}>סיסמה</Text>
            <View style={styles.inputWrap}>
              <TouchableOpacity
                onPress={() => setSecure((p) => !p)}
                style={styles.eyeBtn}
                accessibilityLabel="toggle password visibility"
              >
                <Ionicons
                  name={secure ? "eye-outline" : "eye-off-outline"}
                  size={18}
                  color="#6B7280"
                />
              </TouchableOpacity>

              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="••••••••"
                placeholderTextColor="#9CA3AF"
                secureTextEntry={secure}
                autoCapitalize="none"
                autoCorrect={false}
                textAlign="right"
                style={styles.input}
              />

              <Ionicons name="key-outline" size={18} color="#6B7280" />
            </View>

            <TouchableOpacity
              onPress={() => Alert.alert("איפוס סיסמה", "TODO: מסך/בקשה לאיפוס")}
              style={styles.forgotRow}
            >
              <Text style={styles.forgotText}>שכחת סיסמה?</Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={onLogin}
              disabled={!canSubmit}
              style={[styles.primaryBtn, !canSubmit && styles.primaryBtnDisabled]}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <>
                  <Ionicons name="log-in-outline" size={18} color="#FFFFFF" />
                  <Text style={styles.primaryBtnText}>התחבר/י</Text>
                </>
              )}
            </TouchableOpacity>

            <View style={styles.dividerRow}>
              <View style={styles.divider} />
              <Text style={styles.dividerText}>או</Text>
              <View style={styles.divider} />
            </View>

            <TouchableOpacity
              onPress={() => router.push("./signup")}
              style={styles.secondaryBtn}
            >
              <Text style={styles.secondaryBtnText}>אין לך חשבון? הרשמה</Text>
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
  label: { fontSize: 12, fontWeight: "700", color: "#111827", textAlign: "right" },

  inputWrap: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    backgroundColor: "#F9FAFB",
    borderRadius: 14,
    paddingHorizontal: 12,
    height: 46,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  input: { flex: 1, fontSize: 14, color: "#111827" },
  eyeBtn: { padding: 4 },

  forgotRow: { marginTop: 10, alignSelf: "flex-start" },
  forgotText: { fontSize: 12, color: "#0284C7", fontWeight: "600" },

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
