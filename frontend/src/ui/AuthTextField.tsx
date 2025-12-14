import React from "react";
import { View, Text, TextInput, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";

type Props = {
  label: string;
  value: string;
  onChangeText: (t: string) => void;
  placeholder?: string;

  leftIcon: keyof typeof Ionicons.glyphMap;

  secureTextEntry?: boolean;
  onToggleSecure?: () => void;

  autoCapitalize?: "none" | "sentences" | "words" | "characters";
  keyboardType?: "default" | "email-address" | "numeric" | "phone-pad";
  helperText?: string;
  errorText?: string;
};

export default function AuthTextField({
  label,
  value,
  onChangeText,
  placeholder,
  leftIcon,
  secureTextEntry,
  onToggleSecure,
  autoCapitalize = "none",
  keyboardType = "default",
  helperText,
  errorText,
}: Props) {
  const showEye = typeof secureTextEntry === "boolean" && !!onToggleSecure;

  return (
    <View style={{ gap: 6 }}>
      <Text style={[styles.label, {marginTop: 12}]}>{label}</Text>

      <View style={[styles.inputWrap, !!errorText && styles.inputWrapError]}>
        {/* show eye button if this is a password field */}
        {showEye ? (
          <TouchableOpacity onPress={onToggleSecure} style={styles.eyeBtn}>
            <Ionicons
              name={secureTextEntry ? "eye-outline" : "eye-off-outline"}
              size={18}
              color="#6B7280"
            />
          </TouchableOpacity>
        ) : null}

        <TextInput
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor="#9CA3AF"
          secureTextEntry={secureTextEntry}
          autoCapitalize={autoCapitalize}
          autoCorrect={false}
          keyboardType={keyboardType}
          textAlign="right"
          style={styles.input}
        />

        <Ionicons name={leftIcon} size={18} color="#6B7280" />
      </View>

      {errorText ? (
        <Text style={styles.error}>{errorText}</Text>
      ) : helperText ? (
        <Text style={styles.helper}>{helperText}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  label: { fontSize: 12, fontWeight: "700", color: "#111827", textAlign: "right" },
  inputWrap: {
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
  inputWrapError: {
    borderColor: "#FCA5A5",
    backgroundColor: "#FEF2F2",
  },
  input: { flex: 1, fontSize: 14, color: "#111827" },
  eyeBtn: { padding: 4 },
  helper: { fontSize: 11, color: "#6B7280", textAlign: "right" },
  error: { fontSize: 11, color: "#EF4444", fontWeight: "700", textAlign: "right" },
});
