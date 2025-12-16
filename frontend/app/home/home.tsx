import React, { useCallback, useMemo, useState } from "react";
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

import HomeCard from "@/src/components/homes/HomeCard";
import AddHomeCard from "@/src/components/homes/AddHomeCard";
import SpacerCard from "@/src/components/homes/SpacerCard";

type Home = {
  id: string;
  name: string;
  membersCount: number;
  updatedAt: string; // ISO
};

type GridItem =
  | { kind: "home"; home: Home }
  | { kind: "add"; id: "add-home" }
  | { kind: "spacer"; id: "spacer" };

const BRAND_PRIMARY = "#0284C7";
const BRAND_BG = "#F6FAFF";
const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";

export default function HomesScreen() {
  const [homes, setHomes] = useState<Home[]>([]);
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [saving, setSaving] = useState(false);

  const sortedHomes = useMemo(() => {
    return [...homes].sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt));
  }, [homes]);

  const gridData: GridItem[] = useMemo(() => {
    const data: GridItem[] = [
      ...sortedHomes.map((h) => ({ kind: "home", home: h } as const)),
      { kind: "add", id: "add-home" } as const,
    ];

    if (data.length % 2 === 1) data.push({ kind: "spacer", id: "spacer" } as const);
    return data;
  }, [sortedHomes]);

  const openHome = useCallback((homeId: string) => {
    router.push({ pathname: "../home/[homeId]", params: { homeId } });
  }, []);

  const onCreateHome = useCallback(async () => {
    const name = newName.trim();
    if (!name) return Alert.alert("חסר שם", "כתבי שם לבית החדש.");
    if (name.length < 2) return Alert.alert("שם קצר מדי", "שם הבית צריך להיות לפחות 2 תווים.");

    try {
      setSaving(true);

      const created: Home = {
        id: String(Date.now()),
        name,
        membersCount: 1,
        updatedAt: new Date().toISOString(),
      };

      setHomes((prev) => [created, ...prev]);
      setNewName("");
      setCreateOpen(false);
      openHome(created.id);
    } catch {
      Alert.alert("שגיאה", "לא הצלחתי ליצור בית כרגע.");
    } finally {
      setSaving(false);
    }
  }, [newName, openHome]);

  const renderItem = useCallback(
    ({ item }: { item: GridItem }) => {
      if (item.kind === "spacer") return <SpacerCard />;

      if (item.kind === "add") {
        return <AddHomeCard onPress={() => setCreateOpen(true)} />;
      }

      return <HomeCard home={item.home} onPress={() => openHome(item.home.id)} />;
    },
    [openHome]
  );

  const isValid = newName.trim().length >= 2;

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={{ width: 40 }} />
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
              <Ionicons name="add" size={18} color="white" />
              <Text style={styles.primaryBtnText}>הוסף בית חדש</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <Text style={styles.sectionTitle}>בחר בית</Text>

            <FlatList
              data={gridData}
              keyExtractor={(i) => (i.kind === "home" ? i.home.id : i.id)}
              renderItem={renderItem}
              numColumns={2}
              columnWrapperStyle={{ gap: 12 }}
              contentContainerStyle={{ paddingTop: 8, paddingBottom: 24, gap: 12 }}
              showsVerticalScrollIndicator={false}
            />
          </>
        )}
      </View>

      {/* Create Home Modal */}
      <Modal
        visible={createOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setCreateOpen(false)}
      >
        <Pressable style={styles.modalBackdrop} onPress={() => setCreateOpen(false)}>
          <Pressable style={styles.modalCard} onPress={() => {}}>
            <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined}>
              <Text style={styles.modalTitle}>בית חדש</Text>
              <Text style={styles.modalSubtitle}>תקבע לבית שם כדי שכולם יזהו אותו.</Text>

              <View style={styles.inputWrap}>
                <Ionicons name="pricetag-outline" size={18} color={MUTED} />
                <TextInput
                  value={newName}
                  onChangeText={setNewName}
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
                  style={[
                    styles.primaryBtn,
                    (!isValid || saving) && { opacity: 0.5 },
                  ]}
                  activeOpacity={0.9}
                  disabled={!isValid || saving}
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

  body: { flex: 1, paddingHorizontal: 16, paddingTop: 8 },

  sectionTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: MUTED,
    textAlign: "right",
    marginBottom: 6,
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
