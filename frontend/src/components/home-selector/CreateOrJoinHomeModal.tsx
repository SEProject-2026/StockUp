import React from "react";
import {
  View,
  Text,
  StyleSheet,
  Modal,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  TextInput,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

type ModalMode = "create" | "join";

const BRAND_PRIMARY = "#0284C7";
const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";

export default function CreateOrJoinHomeModal({
  visible,
  saving,
  mode,
  onChangeMode,
  newName,
  onChangeName,
  joinCode,
  onChangeCode,
  onClose,
  onPrimary,
  primaryDisabled,
}: {
  visible: boolean;
  saving: boolean;
  mode: ModalMode;
  onChangeMode: (m: ModalMode) => void;

  newName: string;
  onChangeName: (v: string) => void;

  joinCode: string;
  onChangeCode: (v: string) => void;

  onClose: () => void;
  onPrimary: () => void;
  primaryDisabled: boolean;
}) {
  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.modalBackdrop} onPress={() => !saving && onClose()}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
            {/* Segment */}
            <View style={styles.segment}>
              <TouchableOpacity
                onPress={() => !saving && onChangeMode("create")}
                style={[styles.segmentBtn, mode === "create" && styles.segmentBtnActive]}
                disabled={saving}
              >
                <Text style={[styles.segmentText, mode === "create" && styles.segmentTextActive]}>
                  יצירת בית
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={() => !saving && onChangeMode("join")}
                style={[styles.segmentBtn, mode === "join" && styles.segmentBtnActive]}
                disabled={saving}
              >
                <Text style={[styles.segmentText, mode === "join" && styles.segmentTextActive]}>
                  הצטרפות עם קוד
                </Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.modalTitle}>
              {mode === "create" ? "בית חדש" : "הצטרפות לבית"}
            </Text>
            <Text style={styles.modalSubtitle}>
              {mode === "create"
                ? "תקבע לבית שם כדי שכולם יזהו אותו."
                : "הכנס קוד הזמנה שקיבלת כדי להצטרף לבית קיים."}
            </Text>

            {mode === "create" ? (
              <View style={styles.inputWrap}>
                <Ionicons name="pricetag-outline" size={18} color={MUTED} />
                <TextInput
                  value={newName}
                  onChangeText={onChangeName}
                  style={styles.input}
                  textAlign="right"
                  autoFocus
                  placeholder="שם הבית"
                  placeholderTextColor={MUTED}
                />
              </View>
            ) : (
              <View style={styles.inputWrap}>
                <Ionicons name="key-outline" size={18} color={MUTED} />
                <TextInput
                  value={joinCode}
                  onChangeText={onChangeCode}
                  style={styles.input}
                  textAlign="right"
                  autoFocus
                  placeholder="קוד הזמנה"
                  placeholderTextColor={MUTED}
                  autoCapitalize="characters"
                  autoCorrect={false}
                />
              </View>
            )}

            <View style={styles.modalActions}>
              <TouchableOpacity
                onPress={onClose}
                style={styles.secondaryBtn}
                activeOpacity={0.85}
                disabled={saving}
              >
                <Text style={styles.secondaryBtnText}>ביטול</Text>
              </TouchableOpacity>

              <TouchableOpacity
                onPress={onPrimary}
                style={[styles.primaryBtn, (primaryDisabled || saving) && { opacity: 0.5 }]}
                activeOpacity={0.9}
                disabled={primaryDisabled || saving}
              >
                <Text style={styles.primaryBtnText}>
                  {saving ? "מבצע..." : mode === "create" ? "יצירה" : "הצטרפות"}
                </Text>
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(17,24,39,0.35)",
    padding: 16,
    justifyContent: "center",
  },
  modalCard: {
    backgroundColor: "white",
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: BORDER,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: "900",
    color: TEXT,
    textAlign: "right",
  },
  modalSubtitle: { marginTop: 6, fontSize: 12, color: MUTED, textAlign: "right" },

  segment: {
    flexDirection: "row-reverse",
    backgroundColor: "#F3F4F6",
    borderRadius: 14,
    padding: 4,
    borderWidth: 1,
    borderColor: BORDER,
    marginBottom: 12,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  segmentBtnActive: {
    backgroundColor: "white",
    borderWidth: 1,
    borderColor: BORDER,
  },
  segmentText: { color: MUTED, fontWeight: "800", fontSize: 12 },
  segmentTextActive: { color: TEXT },

  inputWrap: {
    marginTop: 14,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 14,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  input: { flex: 1, fontSize: 14, color: TEXT, padding: 0 },

  modalActions: {
    marginTop: 14,
    flexDirection: "row-reverse",
    gap: 10,
    justifyContent: "flex-start",
  },

  primaryBtn: {
    backgroundColor: BRAND_PRIMARY,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    minWidth: 120,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryBtnText: { color: "white", fontWeight: "800", fontSize: 14 },

  secondaryBtn: {
    backgroundColor: "white",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: BORDER,
    minWidth: 120,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryBtnText: { color: TEXT, fontWeight: "800", fontSize: 14 },
});
