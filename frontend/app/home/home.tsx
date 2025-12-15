// app/homes.tsx
import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Modal,
  TextInput,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";

// אם יש לך את זה אצלך בפרויקט, אפשר להחליף את ההדר למרכיב שלך:
// import ScreenHeader from "@/src/layout/ScreenHeader";

type Home = {
  id: string;
  name: string;
  membersCount: number;
  updatedAt: string; // ISO
};

const BRAND_PRIMARY = "#0284C7";
const BRAND_BG = "#F6FAFF";
const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";
const CARD = "#FFFFFF";

export default function HomesScreen() {
  // TODO: להחליף בהמשך ל-data מהשרת / context (multi-household)
  const [homes, setHomes] = useState<Home[]>([]);

  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [saving, setSaving] = useState(false);

  const sortedHomes = useMemo(() => {
    return [...homes].sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt));
  }, [homes]);

  const openHome = (homeId: string) => {
    // יעד מומלץ: app/home/[homeId].tsx
    router.push({ pathname: "../home/[homeId]", params: { homeId } });
  };

  const onCreateHome = async () => {
    const name = newName.trim();
    if (!name) {
      Alert.alert("חסר שם", "כתבי שם לבית החדש.");
      return;
    }
    if (name.length < 2) {
      Alert.alert("שם קצר מדי", "שם הבית צריך להיות לפחות 2 תווים.");
      return;
    }

    try {
      setSaving(true);

      // TODO: כאן יהיה POST לשרת (create household/home)
      const created: Home = {
        id: String(Date.now()),
        name,
        membersCount: 1,
        updatedAt: new Date().toISOString(),
      };

      setHomes((prev) => [created, ...prev]);
      setNewName("");
      setCreateOpen(false);

      // אופציונלי: להיכנס ישר לבית החדש
      openHome(created.id);
    } catch (e) {
      Alert.alert("שגיאה", "לא הצלחתי ליצור בית כרגע.");
    } finally {
      setSaving(false);
    }
  };

  const renderHome = ({ item }: { item: Home }) => {
    return (
      <TouchableOpacity
        onPress={() => openHome(item.id)}
        activeOpacity={0.85}
        style={styles.card}
      >
        <View style={styles.cardIcon}>
          <Ionicons name="home-outline" size={18} color={BRAND_PRIMARY} />
        </View>

        <View style={{ flex: 1 }}>
          <Text style={styles.cardTitle} numberOfLines={1}>
            {item.name}
          </Text>
          <Text style={styles.cardSubtitle}>
            {item.membersCount} {item.membersCount === 1 ? "חבר/ה" : "חברים"} · עודכן לאחרונה{" "}
            {formatRelativeDate(item.updatedAt)}
          </Text>
        </View>

        <Ionicons name="chevron-back" size={20} color={MUTED} />
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => setCreateOpen(true)}
          style={styles.headerAction}
          activeOpacity={0.85}
        >
          <Ionicons name="add" size={20} color={TEXT} />
        </TouchableOpacity>

        <Text style={styles.headerTitle}>הבתים שלי</Text>

        <View style={{ width: 40 }} />
      </View>

      {/* Body */}
      <View style={styles.body}>
        {sortedHomes.length === 0 ? (
          <View style={styles.empty}>
            <View style={styles.emptyIcon}>
              <Ionicons name="home" size={22} color={BRAND_PRIMARY} />
            </View>
            <Text style={styles.emptyTitle}>אין לך עדיין בתים</Text>
            <Text style={styles.emptySubtitle}>
              הוסיפי בית חדש כדי להתחיל לנהל מלאי משותף.
            </Text>

            <TouchableOpacity
              onPress={() => setCreateOpen(true)}
              style={styles.primaryBtn}
              activeOpacity={0.9}
            >
              <Ionicons name="add-circle-outline" size={18} color="white" />
              <Text style={styles.primaryBtnText}>הוסף בית חדש</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <Text style={styles.sectionTitle}>בחרי בית</Text>

            <FlatList
              data={sortedHomes}
              keyExtractor={(h) => h.id}
              renderItem={renderHome}
              contentContainerStyle={{ paddingBottom: 24 }}
              showsVerticalScrollIndicator={false}
            />

            <TouchableOpacity
              onPress={() => setCreateOpen(true)}
              style={styles.fab}
              activeOpacity={0.9}
            >
              <Ionicons name="add" size={24} color="white" />
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Create Home Modal */}
      <Modal visible={createOpen} transparent animationType="fade" onRequestClose={() => setCreateOpen(false)}>
        <Pressable style={styles.modalBackdrop} onPress={() => setCreateOpen(false)}>
          <Pressable style={styles.modalCard} onPress={() => {}}>
            <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
              <Text style={styles.modalTitle}>בית חדש</Text>
              <Text style={styles.modalSubtitle}>תני לבית שם כדי שכולם יזהו אותו.</Text>

              <View style={styles.inputWrap}>
                <Ionicons name="pricetag-outline" size={18} color={MUTED} />
                <TextInput
                  value={newName}
                  onChangeText={setNewName}
                  placeholder="למשל: הבית של אדן"
                  placeholderTextColor="#9CA3AF"
                  style={styles.input}
                  textAlign="right"
                  autoFocus
                />
              </View>

              <View style={styles.modalActions}>
                <TouchableOpacity
                  onPress={() => setCreateOpen(false)}
                  style={styles.secondaryBtn}
                  activeOpacity={0.85}
                  disabled={saving}
                >
                  <Text style={styles.secondaryBtnText}>ביטול</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  onPress={onCreateHome}
                  style={[styles.primaryBtn, saving && { opacity: 0.7 }]}
                  activeOpacity={0.9}
                  disabled={saving}
                >
                  <Text style={styles.primaryBtnText}>{saving ? "יוצר..." : "יצירה"}</Text>
                </TouchableOpacity>
              </View>
            </KeyboardAvoidingView>
          </Pressable>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
}

function formatRelativeDate(iso: string) {
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 2) return "עכשיו";
  if (minutes < 60) return `${minutes} דק׳`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} ש׳`;
  const days = Math.floor(hours / 24);
  return `${days} ימים`;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BRAND_BG },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 6,
    paddingBottom: 10,
  },
  headerTitle: {
    flex: 1,
    textAlign: "center",
    fontSize: 18,
    fontWeight: "800",
    color: TEXT,
  },
  headerAction: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.9)",
    borderWidth: 1,
    borderColor: BORDER,
    alignItems: "center",
    justifyContent: "center",
  },
  body: { flex: 1, paddingHorizontal: 16, paddingTop: 8 },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: MUTED,
    textAlign: "right",
    marginBottom: 10,
  },
  card: {
    backgroundColor: CARD,
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 16,
    padding: 14,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 12,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.06,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
  },
  cardIcon: {
    width: 34,
    height: 34,
    borderRadius: 12,
    backgroundColor: "rgba(2,132,199,0.10)",
    alignItems: "center",
    justifyContent: "center",
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "800",
    color: TEXT,
    textAlign: "right",
  },
  cardSubtitle: {
    marginTop: 4,
    fontSize: 12,
    color: MUTED,
    textAlign: "right",
  },
  empty: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 18,
    gap: 10,
  },
  emptyIcon: {
    width: 56,
    height: 56,
    borderRadius: 18,
    backgroundColor: "rgba(2,132,199,0.10)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.16)",
  },
  emptyTitle: { fontSize: 18, fontWeight: "900", color: TEXT },
  emptySubtitle: {
    fontSize: 13,
    color: MUTED,
    textAlign: "center",
    lineHeight: 18,
    marginBottom: 6,
  },
  primaryBtn: {
    backgroundColor: BRAND_PRIMARY,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    minWidth: 180,
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
  fab: {
    position: "absolute",
    right: 16,
    bottom: 20,
    width: 54,
    height: 54,
    borderRadius: 18,
    backgroundColor: BRAND_PRIMARY,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOpacity: 0.18,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 10 },
  },
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
  modalTitle: { fontSize: 16, fontWeight: "900", color: TEXT, textAlign: "right" },
  modalSubtitle: { marginTop: 6, fontSize: 12, color: MUTED, textAlign: "right" },
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
});
