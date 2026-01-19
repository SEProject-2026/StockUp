import React, { useCallback, useMemo, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";

import HomeCard from "@/src/components/homes/HomeCard";
import AddHomeCard from "@/src/components/homes/AddHomeCard";
import SpacerCard from "@/src/components/homes/SpacerCard";

import HomesHeader from "@/src/components/home-selector/HomesHeader";
import HomesEmptyState from "@/src/components/home-selector/HomesEmptyState";
import CreateOrJoinHomeModal from "@/src/components/home-selector/CreateOrJoinHomeModal";

import { createHome, getMyHomes, joinHomeByCode } from "@/src/api/homes";

type Home = {
  id: string;
  name: string;
  membersCount: number;
  updatedAt: string;
};

type GridItem =
  | { kind: "home"; home: Home }
  | { kind: "add"; id: "add-home" }
  | { kind: "spacer"; id: "spacer" };

type ModalMode = "create" | "join";

const BRAND_PRIMARY = "#0284C7";
const BRAND_BG = "#F6FAFF";
const TEXT = "#111827";
const MUTED = "#6B7280";

function isAuthErrorMessage(msg?: string) {
  if (!msg) return false;
  const s = msg.toLowerCase();
  return (
    s.includes("401") ||
    s.includes("not authenticated") ||
    s.includes("unauthorized") ||
    s.includes("token")
  );
}

export default function HomesScreen() {
  const [homes, setHomes] = useState<Home[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>("create");

  const [newName, setNewName] = useState("");
  const [joinCode, setJoinCode] = useState("");

  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const sortedHomes = useMemo(() => {
    return [...homes].sort(
      (a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt)
    );
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
    router.push({ pathname: "/home/[homeId]", params: { homeId } });
  }, []);

  const mapDtoToHome = useCallback((dto: any): Home => {
    return {
      id: String(dto.id ?? dto.home_id ?? dto.uuid),
      name: dto.name ?? dto.home_name ?? dto.homeName ?? "בית ללא שם",
      membersCount: dto.membersCount ?? dto.members_count ?? 1,
      updatedAt: dto.updatedAt ?? dto.updated_at ?? new Date().toISOString(),
    };
  }, []);

  const loadHomes = useCallback(
    async (mode: "initial" | "refresh" = "initial") => {
      try {
        if (mode === "initial") setLoading(true);
        else setRefreshing(true);

        const res = await getMyHomes();
        const list = (res.data ?? []).map(mapDtoToHome);
        setHomes(list);
      } catch (e: any) {
        const msg = e?.message ?? "לא הצלחתי לטעון בתים";
        if (isAuthErrorMessage(msg)) {
          Alert.alert("צריך להתחבר", "כדי לראות/ליצור/להצטרף לבתים צריך להתחבר.", [
            { text: "להתחברות", onPress: () => router.replace("/login") },
            { text: "ביטול", style: "cancel" },
          ]);
          return;
        }
        Alert.alert("שגיאה", msg);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [mapDtoToHome]
  );

  useEffect(() => {
    loadHomes("initial");
  }, [loadHomes]);

  const openCreate = useCallback(() => {
    setModalMode("create");
    setModalOpen(true);
  }, []);

  const openJoin = useCallback(() => {
    setModalMode("join");
    setModalOpen(true);
  }, []);

  const closeModal = useCallback(() => {
    if (saving) return;
    setModalOpen(false);
  }, [saving]);

  const onCreateHome = useCallback(async () => {
    const name = newName.trim();
    if (!name) return Alert.alert("חסר שם", "בחר שם לבית החדש.");
    if (name.length < 2) return Alert.alert("שם קצר מדי", "שם הבית צריך להיות לפחות 2 תווים.");

    try {
      setSaving(true);
      const res = await createHome({ name });
      const dto = res.data;

      if (!dto?.id) throw new Error(res.message || "Create home failed");

      const created = mapDtoToHome(dto);
      setHomes((prev) => [created, ...prev]);

      setNewName("");
      setJoinCode("");
      setModalOpen(false);
      openHome(created.id);
    } catch (e: any) {
      const msg = e?.message ?? "לא הצלחתי ליצור בית כרגע.";
      if (isAuthErrorMessage(msg)) {
        Alert.alert("צריך להתחבר", "כדי ליצור בית צריך להתחבר.", [
          { text: "להתחברות", onPress: () => router.replace("/login") },
          { text: "ביטול", style: "cancel" },
        ]);
        return;
      }
      Alert.alert("שגיאה", msg);
    } finally {
      setSaving(false);
    }
  }, [newName, openHome, mapDtoToHome]);

  const onJoinHome = useCallback(async () => {
    const code = joinCode.trim();
    if (!code) return Alert.alert("חסר קוד", "הכניסי קוד הזמנה כדי להצטרף לבית.");
    if (code.length < 4) return Alert.alert("קוד קצר מדי", "בדקי את הקוד ונסה שוב.");

    try {
      setSaving(true);
      const res = await joinHomeByCode({ code });
      const dto = res.data;

      const joined = mapDtoToHome(dto);

      setHomes((prev) => {
        const exists = prev.some((h) => h.id === joined.id);
        return exists ? prev : [joined, ...prev];
      });

      setNewName("");
      setJoinCode("");
      setModalOpen(false);
      openHome(joined.id);
    } catch (e: any) {
      const msg = e?.message ?? "לא הצלחתי להצטרף לבית כרגע.";
      if (isAuthErrorMessage(msg)) {
        Alert.alert("צריך להתחבר", "כדי להצטרף לבית צריך להתחבר.", [
          { text: "להתחברות", onPress: () => router.replace("/login") },
          { text: "ביטול", style: "cancel" },
        ]);
        return;
      }
      Alert.alert("שגיאה", msg);
    } finally {
      setSaving(false);
    }
  }, [joinCode, openHome, mapDtoToHome]);

  const renderItem = useCallback(
    ({ item }: { item: GridItem }) => {
      if (item.kind === "spacer") return <SpacerCard />;
      if (item.kind === "add") return <AddHomeCard onPress={openCreate} />;
      return <HomeCard home={item.home} onPress={() => openHome(item.home.id)} />;
    },
    [openHome, openCreate]
  );

  const isValid = modalMode === "create"
    ? newName.trim().length >= 2
    : joinCode.trim().length >= 4;

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <HomesHeader title="הבתים שלי" />

      <View style={styles.body}>
        {loading ? (
          <View style={styles.centerLoader}>
            <ActivityIndicator size="large" color={BRAND_PRIMARY} />
            <Text style={styles.loaderText}>טוען בתים…</Text>
          </View>
        ) : sortedHomes.length === 0 ? (
          <HomesEmptyState onCreate={openCreate} onJoin={openJoin} />
        ) : (
          <>
            <View style={styles.topRow}>
              <Text style={styles.sectionTitle}>בחר בית</Text>

              <TouchableOpacity onPress={openJoin} style={styles.joinPill} activeOpacity={0.9}>
                <Ionicons name="key-outline" size={14} color={BRAND_PRIMARY} />
                <Text style={styles.joinPillText}>הצטרפות עם קוד</Text>
              </TouchableOpacity>
            </View>

            <FlatList
              data={gridData}
              keyExtractor={(i) => (i.kind === "home" ? i.home.id : i.id)}
              renderItem={renderItem}
              numColumns={2}
              columnWrapperStyle={{ gap: 12 }}
              contentContainerStyle={{ paddingTop: 8, paddingBottom: 24, gap: 12 }}
              showsVerticalScrollIndicator={false}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={() => loadHomes("refresh")} />
              }
            />
          </>
        )}
      </View>

      <CreateOrJoinHomeModal
        visible={modalOpen}
        saving={saving}
        mode={modalMode}
        onChangeMode={setModalMode}
        newName={newName}
        onChangeName={setNewName}
        joinCode={joinCode}
        onChangeCode={setJoinCode}
        onClose={closeModal}
        onPrimary={modalMode === "create" ? onCreateHome : onJoinHome}
        primaryDisabled={!isValid}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BRAND_BG },

  body: { flex: 1, paddingHorizontal: 16, paddingTop: 8 },

  centerLoader: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  loaderText: { color: MUTED, fontWeight: "700" },

  topRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 6,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "700",
    color: MUTED,
    textAlign: "right",
  },

  joinPill: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 10,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.25)",
    backgroundColor: "rgba(2,132,199,0.08)",
  },
  joinPillText: { color: BRAND_PRIMARY, fontWeight: "900", fontSize: 12 },
});
