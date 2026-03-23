import React, { useState, useEffect } from "react";
import { View, Text, StyleSheet, TextInput, TouchableOpacity, Alert, ActivityIndicator, KeyboardAvoidingView, Platform } from "react-native";
import { supabase } from "@/src/lib/supabase";
import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

export default function ResetPasswordScreen() {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState(""); 
  const [loading, setLoading] = useState(false);
  const [secure, setSecure] = useState(true);

  const canSubmit = newPassword.length >= 6 && newPassword === confirmPassword && !loading;
useEffect(() => {
    async function checkAuthStatus() {
      const { data: { session }, error } = await supabase.auth.getSession();
      
      console.log("--- בדיקת מצב חיבור במסך איפוס ---");
      if (session) {
        console.log("✅ המשתמש מזוהה! אימייל:", session.user.email);
        console.log("Session ID:", session.access_token.substring(0, 10) + "...");
      } else {
        console.log("❌ לא נמצא Session. ייתכן שהלינק לא תקין או פג תוקף.");
      }
      
      if (error) console.error("שגיאת סשן:", error.message);
    }

    checkAuthStatus();
  }, []);
  
  async function handleReset() {
    if (newPassword !== confirmPassword) {
      Alert.alert("שגיאה", "הסיסמאות אינן תואמות");
      return;
    }

    try {
      setLoading(true);
      
      const { error: updateError } = await supabase.auth.updateUser({ 
        password: newPassword 
      });
      
      if (updateError) throw updateError;

      await supabase.auth.signOut();

      Alert.alert("הצלחה!", "הסיסמה עודכנה בהצלחה. כעת ניתן להתחבר מחדש.", [
        { text: "מעולה", onPress: () => router.replace("/login") }
      ]);
    } catch (e: any) {
      console.error(e);
      Alert.alert("שגיאה", "פג תוקף הקישור או שישנה תקלה טכנית. נסה/י לבקש קישור חדש.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === "ios" ? "padding" : "height"} 
      style={styles.container}
    >
      <View style={styles.card}>
        <Ionicons name="lock-open-outline" size={48} color="#0284C7" style={{ alignSelf: 'center', marginBottom: 10 }} />
        <Text style={styles.title}>קביעת סיסמה חדשה</Text>
        <Text style={styles.subtitle}>הזינו סיסמה חדשה בת 6 תווים לפחות</Text>

        <TextInput
          placeholder="סיסמה חדשה"
          value={newPassword}
          onChangeText={setNewPassword}
          secureTextEntry={secure}
          style={styles.input}
          textAlign="right"
        />

        <TextInput
          placeholder="אימות סיסמה"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry={secure}
          style={styles.input}
          textAlign="right"
        />

        <TouchableOpacity 
          onPress={handleReset} 
          style={[styles.button, !canSubmit && styles.buttonDisabled]} 
          disabled={!canSubmit}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.buttonText}>עדכן סיסמה והתחבר</Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => router.replace("/login")} style={{ marginTop: 15 }}>
          <Text style={{ color: '#6B7280', textAlign: 'center' }}>חזרה למסך הכניסה</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 20, backgroundColor: "#F9FAFB" },
  card: { backgroundColor: '#FFF', padding: 25, borderRadius: 20, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 10, elevation: 5 },
  title: { fontSize: 22, fontWeight: "800", marginBottom: 8, textAlign: "center", color: '#111827' },
  subtitle: { fontSize: 14, color: '#6B7280', textAlign: 'center', marginBottom: 24 },
  input: { backgroundColor: "#F3F4F6", padding: 15, borderRadius: 12, marginBottom: 12, fontSize: 16 },
  button: { backgroundColor: "#0284C7", padding: 16, borderRadius: 999, alignItems: "center", marginTop: 10 },
  buttonDisabled: { backgroundColor: '#93C5FD' },
  buttonText: { color: "#FFF", fontWeight: "800", fontSize: 16 }
});