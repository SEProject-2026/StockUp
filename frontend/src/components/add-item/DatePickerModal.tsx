import React, { useMemo, useState } from "react";
import { Modal, Pressable, View, Text, StyleSheet, TouchableOpacity, TextInput, Platform, Alert } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND_PRIMARY = "#0284C7";
const BRAND_TEXT = "#111827";
const BRAND_MUTED = "#6B7280";
const BRAND_BORDER = "#E5E7EB";
const BRAND_BLUE_SOFT = "#F0FAFF";

type DateTimePickerType = React.ComponentType<{
  value: Date;
  mode?: "date" | "time" | "datetime";
  display?: any;
  onChange: (event: any, date?: Date) => void;
}>;

function tryGetNativePicker(): DateTimePickerType | null {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const mod = require("@react-native-community/datetimepicker");
    return (mod.default ?? mod) as DateTimePickerType;
  } catch {
    return null;
  }
}

function toISODate(d: Date) {
  return d.toISOString().slice(0, 10);
}

function parseISODate(s: string): Date | null {
  // מצפים YYYY-MM-DD
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s.trim());
  if (!m) return null;
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const da = Number(m[3]);
  if (mo < 1 || mo > 12 || da < 1 || da > 31) return null;
  const d = new Date(Date.UTC(y, mo - 1, da));
  // וידוא שלא נוצר תאריך “מתגלגל”
  if (d.getUTCFullYear() !== y || d.getUTCMonth() !== mo - 1 || d.getUTCDate() !== da) return null;
  return d;
}

export default function DatePickerModal(props: {
  open: boolean;
  value?: Date;
  onClose: () => void;
  onChange: (d: Date) => void;
  onClear: () => void;
}) {
  const NativePicker = useMemo(() => tryGetNativePicker(), []);
  const [text, setText] = useState(props.value ? toISODate(props.value) : "");

  React.useEffect(() => {
    if (!props.open) return;
    setText(props.value ? toISODate(props.value) : "");
  }, [props.open, props.value]);

  const initial = props.value ?? new Date();

  return (
    <Modal visible={props.open} animationType="fade" transparent onRequestClose={props.onClose}>
      <Pressable style={styles.backdrop} onPress={props.onClose} />
      <View style={styles.card}>
        <View style={styles.header}>
          <Text style={styles.title}>תאריך תוקף</Text>
          <TouchableOpacity onPress={props.onClose} activeOpacity={0.85}>
            <Ionicons name="close" size={20} color={BRAND_MUTED} />
          </TouchableOpacity>
        </View>

        {NativePicker ? (
          <View style={{ gap: 10 }}>
            <View style={styles.note}>
              <Ionicons name="information-circle-outline" size={16} color={BRAND_MUTED} />
              <Text style={styles.noteText}>בחר תאריך (native)</Text>
            </View>

            <View style={styles.nativeWrap}>
              <NativePicker
                value={initial}
                mode="date"
                onChange={(event, date) => {
                  // Android שולח event.type
                  if (Platform.OS === "android") {
                    if (event?.type === "dismissed") return;
                    if (date) {
                      props.onChange(date);
                      props.onClose();
                    }
                    return;
                  }
                  // iOS: נעדכן בלי לסגור מיד
                  if (date) props.onChange(date);
                }}
              />
            </View>

            {Platform.OS !== "android" && (
              <TouchableOpacity
                style={styles.primaryBtn}
                activeOpacity={0.9}
                onPress={() => {
                  if (!props.value) {
                    // אם אין value (משתמש לא שינה), ניקח initial
                    props.onChange(initial);
                  }
                  props.onClose();
                }}
              >
                <Text style={styles.primaryText}>אישור</Text>
              </TouchableOpacity>
            )}
          </View>
        ) : (
          <View style={{ gap: 10 }}>
            <View style={styles.note}>
              <Ionicons name="construct-outline" size={16} color={BRAND_MUTED} />
              <Text style={styles.noteText}>
                אין DatePicker מותקן — אפשר להקליד תאריך בפורמט YYYY-MM-DD
              </Text>
            </View>

            <View style={styles.inputRow}>
              <TextInput
                value={text}
                onChangeText={setText}
                placeholder="YYYY-MM-DD"
                placeholderTextColor="#9CA3AF"
                style={styles.input}
                textAlign="center"
                autoCapitalize="none"
              />
              <TouchableOpacity
                style={styles.primaryBtn}
                activeOpacity={0.9}
                onPress={() => {
                  const parsed = parseISODate(text);
                  if (!parsed) {
                    Alert.alert("תאריך לא תקין", "כתבי תאריך בפורמט YYYY-MM-DD, למשל 2026-01-04");
                    return;
                  }
                  // נשתמש בתאריך לוקאלי (לא UTC) לייצוג UI, אבל לשרת את כבר שולחת YYYY-MM-DD
                  props.onChange(new Date(parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate()));
                  props.onClose();
                }}
              >
                <Text style={styles.primaryText}>אישור</Text>
              </TouchableOpacity>
            </View>

            <TouchableOpacity
              style={styles.installHint}
              activeOpacity={0.9}
              onPress={() => {
                Alert.alert(
                  "רוצה DatePicker native?",
                  "התקיני: @react-native-community/datetimepicker\nואז זה יופעל אוטומטית.",
                  [{ text: "סגור", style: "cancel" }]
                );
              }}
            >
              <Text style={styles.installHintText}>איך להפעיל DatePicker native?</Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={styles.footerRow}>
          <TouchableOpacity onPress={props.onClear} activeOpacity={0.85} style={styles.secondaryBtn}>
            <Ionicons name="trash-outline" size={16} color={BRAND_TEXT} />
            <Text style={styles.secondaryText}>נקה תאריך</Text>
          </TouchableOpacity>

          <TouchableOpacity onPress={props.onClose} activeOpacity={0.85} style={[styles.secondaryBtn, { backgroundColor: BRAND_BLUE_SOFT }]}>
            <Text style={styles.secondaryText}>סגור</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.25)" },
  card: {
    position: "absolute",
    left: 16,
    right: 16,
    top: "30%",
    borderRadius: 18,
    backgroundColor: "#FFFFFF",
    padding: 12,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    gap: 10,
  },
  header: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: { fontSize: 14, fontWeight: "800", color: BRAND_TEXT, textAlign: "right" },

  note: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    padding: 10,
    borderRadius: 14,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  noteText: { flex: 1, fontSize: 12, color: BRAND_MUTED, textAlign: "right" },

  nativeWrap: {
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    borderRadius: 14,
    overflow: "hidden",
    backgroundColor: "#fff",
    padding: 6,
  },

  inputRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    backgroundColor: "#FAFAFA",
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: BRAND_TEXT,
  },

  primaryBtn: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 999,
    backgroundColor: BRAND_PRIMARY,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryText: { color: "#fff", fontWeight: "800" },

  installHint: {
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
    alignItems: "center",
  },
  installHintText: { fontSize: 12, color: BRAND_MUTED, fontWeight: "700" },

  footerRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10, marginTop: 2 },
  secondaryBtn: {
    flex: 1,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 12,
    borderRadius: 999,
    backgroundColor: "#FFECEC",
    borderWidth: 1,
    borderColor: BRAND_BORDER,
  },
  secondaryText: { color: BRAND_TEXT, fontWeight: "800" },
});
