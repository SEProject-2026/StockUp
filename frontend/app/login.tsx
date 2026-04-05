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
import { Ionicons, FontAwesome } from "@expo/vector-icons"; 
import { router } from "expo-router";
import ScreenHeader from "@/src/layout/ScreenHeader";
import { registerForPushNotificationsAsync } from '../src/api/notifications';
import { supabase } from "@/src/config/supabase";
import { registerBackend } from "@/src/api/auth";

import * as WebBrowser from 'expo-web-browser';
import { makeRedirectUri } from "expo-auth-session";

WebBrowser.maybeCompleteAuthSession();

export default function LoginScreen() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [secure, setSecure] = useState(true);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const canSubmit = useMemo(() => {
    return password.length >= 6 && !loading;
  }, [email, password, loading]);

  async function onLogin() {
    if (!canSubmit) return;
    try {
      setLoading(true);
      const { error } = await supabase.auth.signInWithPassword({
        email: email.trim().toLowerCase(),
        password: password,
      });
      if (error) throw error;
      
      registerForPushNotificationsAsync().catch(console.error);
      router.replace("/home/home"); 
    } catch (e: any) {
      Alert.alert("התחברות נכשלה", "אימייל או סיסמה שגויים, נסה/י שוב");
    } finally {
      setLoading(false);
    }
  }

  async function onGoogleLogin() {
    try {
      setGoogleLoading(true);
      const redirectTo = makeRedirectUri({ scheme: "stockup", path: "auth" });
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo, skipBrowserRedirect: true },
      });

      if (error) throw error;

      if (data?.url) {
        const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
        if (result.type === 'success' && result.url) {
          const urlParts = result.url.split('#');
          const hash = urlParts.length > 1 ? urlParts[1] : '';
          const params: Record<string, string> = {};
          hash.split('&').forEach(part => {
            const [key, value] = part.split('=');
            if (key && value) params[key] = value;
          });

          const accessToken = params["access_token"];
          const refreshToken = params["refresh_token"];

          if (accessToken && refreshToken) {
            const { data: { session }, error: sessionError } = await supabase.auth.setSession({
              access_token: accessToken,
              refresh_token: refreshToken,
            });

            if (sessionError) throw sessionError;
            if (session) {
              try {
                await registerBackend({
                  user_id: session.user.id,
                  email: session.user.email || "",
                  name: session.user.user_metadata?.full_name || session.user.user_metadata?.name || "משתמש גוגל",
                }, accessToken); 
              } catch (backendErr) {}
              registerForPushNotificationsAsync().catch(console.error);
              router.replace("/home/home");
            }
          }
        }
      }
    } catch (e: any) {
      Alert.alert("שגיאה", "ההתחברות עם גוגל נכשלה");
    } finally {
      setGoogleLoading(false);
    }
  }

  async function onForgotPassword() {
    if (!email) {
      Alert.alert("שגיאה", "אנא הזן/י אימייל כדי לקבל קישור לאיפוס");
      return;
    }
    try {
      setLoading(true);
      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: 'stockup://reset-password',
      });
      if (error) throw error;
      Alert.alert("נשלח!", "בדוק/י את תיבת המייל שלך (כולל ספאם)");
    } catch (e: any) {
      Alert.alert("שגיאה", "לא הצלחנו לשלוח מייל איפוס");
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <LinearGradient colors={["#E5F3FF", "#F9FAFB"]} style={styles.gradient} />
      <ScreenHeader title="התחברות" />

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView style={styles.content}>
          <View style={styles.hero}>
            <View style={styles.iconCircle}>
              <Ionicons name="lock-closed-outline" size={20} color="#0284C7" />
            </View>
            <Text style={styles.heroTitle}>ברוך שובך</Text>
          </View>

          <View style={styles.card}>
            <Text style={styles.label}>אימייל</Text>
            <View style={styles.inputWrap}>
              <Ionicons name="mail-outline" size={18} color="#6B7280" />
              <TextInput
                value={email}
                onChangeText={setEmail}
                placeholderTextColor="#9CA3AF"
                placeholder="example@example.com"
                keyboardType="email-address"
                autoCapitalize="none"
                textAlign="right"
                style={styles.input}
              />
            </View>

            <Text style={[styles.label, { marginTop: 12 }]}>סיסמה</Text>
            <View style={styles.inputWrap}>
              <TouchableOpacity onPress={() => setSecure((p) => !p)} style={styles.eyeBtn}>
                <Ionicons name={secure ? "eye-outline" : "eye-off-outline"} size={18} color="#6B7280" />
              </TouchableOpacity>
              <TextInput
                value={password}
                onChangeText={setPassword}
                placeholder="••••••••"
                secureTextEntry={secure}
                autoCapitalize="none"
                textAlign="right"
                style={styles.input}
              />
              <Ionicons name="key-outline" size={18} color="#6B7280" />
            </View>

            {/* כפתור שכחתי סיסמה */}
            <TouchableOpacity onPress={onForgotPassword} style={styles.forgotBtn} disabled={loading}>
              <Text style={styles.forgotText}>שכחת סיסמה?</Text>
            </TouchableOpacity>

            <TouchableOpacity
              onPress={onLogin}
              disabled={!canSubmit || loading}
              style={[styles.primaryBtn, !canSubmit && styles.primaryBtnDisabled]}
            >
              {loading ? <ActivityIndicator size="small" color="#FFFFFF" /> : (
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

            <TouchableOpacity onPress={onGoogleLogin} disabled={googleLoading} style={styles.googleBtn}>
              {googleLoading ? <ActivityIndicator size="small" color="#111827" /> : (
                <>
                  <FontAwesome name="google" size={18} color="#EA4335" />
                  <Text style={styles.googleBtnText}>התחברות עם Google</Text>
                </>
              )}
            </TouchableOpacity>

            <TouchableOpacity onPress={() => router.push("./signup")} style={[styles.secondaryBtn, { marginTop: 16 }]}>
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
  content: { flex: 1, paddingHorizontal: 20, paddingTop: 16 },
  hero: { alignItems: "flex-end", gap: 6, marginBottom: 4 },
  iconCircle: { width: 36, height: 36, borderRadius: 999, backgroundColor: "#E0F2FE", alignItems: "center", justifyContent: "center", alignSelf: "flex-end" },
  heroTitle: { fontSize: 18, fontWeight: "800", color: "#111827", textAlign: "right" },
  card: { backgroundColor: "#FFFFFF", borderRadius: 18, padding: 14, shadowColor: "#000", shadowOpacity: 0.06, shadowRadius: 10, elevation: 2 },
  label: { fontSize: 12, fontWeight: "700", color: "#111827", textAlign: "right" },
  inputWrap: { marginTop: 8, borderWidth: 1, borderColor: "#E5E7EB", backgroundColor: "#F9FAFB", borderRadius: 14, paddingHorizontal: 12, height: 46, flexDirection: "row", alignItems: "center", gap: 10 },
  input: { flex: 1, fontSize: 14, color: "#111827" },
  eyeBtn: { padding: 4 },
  forgotBtn: { marginTop: 10, alignSelf: "flex-start" },
  forgotText: { fontSize: 12, color: "#0284C7", fontWeight: "600" },
  primaryBtn: { marginTop: 14, height: 46, borderRadius: 999, backgroundColor: "#0284C7", flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8 },
  primaryBtnDisabled: { opacity: 0.5 },
  primaryBtnText: { color: "#FFFFFF", fontSize: 14, fontWeight: "800" },
  dividerRow: { flexDirection: "row", alignItems: "center", gap: 10, marginVertical: 12 },
  divider: { flex: 1, height: 1, backgroundColor: "#E5E7EB" },
  dividerText: { fontSize: 12, color: "#6B7280" },
  secondaryBtn: { height: 44, borderRadius: 999, backgroundColor: "#EEF2FF", alignItems: "center", justifyContent: "center" },
  secondaryBtnText: { color: "#1D4ED8", fontSize: 13, fontWeight: "800" },
  googleBtn: { height: 46, borderRadius: 999, backgroundColor: "#FFFFFF", borderWidth: 1, borderColor: "#E5E7EB", flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10 },
  googleBtnText: { color: "#111827", fontSize: 14, fontWeight: "700" },
});