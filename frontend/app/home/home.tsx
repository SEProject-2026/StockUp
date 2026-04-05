import React, { useState, useCallback, useMemo, useEffect } from "react";
import { View, Text, StyleSheet, FlatList, TouchableOpacity, ActivityIndicator, RefreshControl, Alert } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { useRealtimeHomesRefresh } from "@/src/hooks/realtime/useRealtimeRefresh";
import { logout } from "@/src/api/auth";

// UI Components
import HomeCard from "@/src/components/homes/HomeCard";
import AddHomeCard from "@/src/components/homes/AddHomeCard";
import SpacerCard from "@/src/components/homes/SpacerCard";
import HomesHeader from "@/src/components/home-selector/HomesHeader";
import HomesEmptyState from "@/src/components/home-selector/HomesEmptyState";
import CreateOrJoinHomeModal from "@/src/components/home-selector/CreateOrJoinHomeModal";

// Logic Hook & Types
import { useHomes, Home } from "@/src/hooks/home/useHomes";

type GridItem =
  | { kind: "home"; home: Home }
  | { kind: "add"; id: string }
  | { kind: "spacer"; id: string };

const BRAND_PRIMARY = "#0284C7";
const BRAND_BG = "#F6FAFF";
const MUTED = "#6B7280";
const DANGER = "#DC2626";

export default function HomesScreen() {
  // שימוש ב-Hook הלוגי (מכיל את ה-loading, refreshing, saving וכו')
  const { homes, loading, refreshing, saving, loadHomes, handleHomeAction } = useHomes();
  
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"create" | "join">("create");
  const [newName, setNewName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => { 
    loadHomes(); 
  }, [loadHomes]);

  useRealtimeHomesRefresh(loadHomes);
  // ארגון נתוני הגריד (כולל ה-Spacer לאיזון עמודות)
  const gridData = useMemo(() => {
    // מיון אלפביתי כפי שהופיע ב-Main
    const sorted = [...homes].sort((a, b) => a.name.localeCompare(b.name, "he"));
    
    const data: GridItem[] = [
      ...sorted.map((h) => ({ kind: "home" as const, home: h })),
      { kind: "add", id: "add-button" }
    ];
    
    if (data.length % 2 === 1) {
      data.push({ kind: "spacer", id: "spacer-item" });
    }
    return data;
  }, [homes]);

  // שליחת טופס (יצירה או הצטרפות)
  const onActionSubmit = async () => {
    const value = modalMode === "create" ? newName : joinCode;
    
    // במידה וזה הצטרפות, ב-Main הופיע Alert הצלחה ספציפי
    const homeId = await handleHomeAction(modalMode, value);
    
    if (homeId) {
      setModalOpen(false);
      setNewName(""); 
      setJoinCode("");
      
      if (modalMode === "join") {
        Alert.alert("הבקשה נשלחה", "בקשת ההצטרפות נשלחה למנהל הבית.");
      } else {
        router.push({ pathname: "/home/[homeId]", params: { homeId } });
      }
    }
  };

  // פונקציית התנתקות (מה-Main)
  const performLogout = useCallback(async () => {
    try {
      setLoggingOut(true);
      await logout();
    } catch (e) {
      Alert.alert("שגיאה", "לא הצלחתי להתנתק כרגע.");
    } finally {
      setLoggingOut(false);
    }
  }, []);

  const onLogoutPress = useCallback(() => {
    Alert.alert("התנתקות", "את בטוחה שברצונך להתנתק?", [
      { text: "ביטול", style: "cancel" },
      { text: "התנתקות", style: "destructive", onPress: performLogout },
    ]);
  }, [performLogout]);

  const renderItem = useCallback(({ item }: { item: GridItem }) => {
    switch (item.kind) {
      case "spacer":
        return <SpacerCard />;
      case "add":
        return (
          <AddHomeCard 
            onPress={() => { 
              setModalMode("create"); 
              setModalOpen(true); 
            }} 
          />
        );
      case "home":
        return (
          <HomeCard 
            home={item.home} 
            onPress={() => router.push({ 
              pathname: "/home/[homeId]", 
              params: { homeId: item.home.id } 
            })} 
          />
        );
    }
  }, []);

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      <HomesHeader title="הבתים שלי" />

      <View style={styles.body}>
        {/* כפתור התנתקות */}
        <View style={styles.headerActionsRow}>
          <TouchableOpacity
            onPress={onLogoutPress}
            style={styles.logoutButton}
            activeOpacity={0.8}
            disabled={loggingOut}
          >
            {loggingOut ? (
              <ActivityIndicator size="small" color={DANGER} />
            ) : (
              <>
                <Ionicons name="log-out-outline" size={16} color={DANGER} />
                <Text style={styles.logoutText}>התנתקות</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {loading ? (
          <View style={styles.centerLoader}>
            <ActivityIndicator size="large" color={BRAND_PRIMARY} />
            <Text style={styles.loaderText}>טוען בתים…</Text>
          </View>
        ) : homes.length === 0 ? (
          <HomesEmptyState 
            onCreate={() => { setModalMode("create"); setModalOpen(true); }} 
            onJoin={() => { setModalMode("join"); setModalOpen(true); }} 
          />
        ) : (
          <>
            <View style={styles.topRow}>
              <Text style={styles.sectionTitle}>בחר בית</Text>
              <TouchableOpacity 
                onPress={() => { setModalMode("join"); setModalOpen(true); }} 
                style={styles.joinPill}
              >
                <Ionicons name="key-outline" size={14} color={BRAND_PRIMARY} />
                <Text style={styles.joinPillText}>הצטרפות עם קוד</Text>
              </TouchableOpacity>
            </View>

            <FlatList
              data={gridData}
              keyExtractor={(item) => item.kind + (item.kind === 'home' ? item.home.id : item.id)}
              renderItem={renderItem}
              numColumns={2}
              columnWrapperStyle={{ gap: 12 }}
              contentContainerStyle={{
                paddingTop: 8,
                paddingBottom: 24,
                gap: 12,
              }}
              showsVerticalScrollIndicator={false}
              refreshControl={
                <RefreshControl
                  refreshing={refreshing}
                  onRefresh={() => loadHomes("refresh")}
                />
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
        onClose={() => !saving && setModalOpen(false)}
        onPrimary={onActionSubmit}
        primaryDisabled={
          modalMode === "create" 
            ? newName.trim().length < 2 
            : joinCode.trim().length < 8 // שינוי ל-8 תווים כפי שמוגדר ב-Main
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: BRAND_BG },
  body: { flex: 1, paddingHorizontal: 16, paddingTop: 8 },
  headerActionsRow: {
    flexDirection: "row-reverse",
    justifyContent: "flex-start",
    marginBottom: 12,
  },
  logoutButton: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: "rgba(220,38,38,0.08)",
    borderWidth: 1,
    borderColor: "rgba(220,38,38,0.18)",
  },
  logoutText: { color: DANGER, fontWeight: "800", fontSize: 12 },
  centerLoader: { flex: 1, alignItems: "center", justifyContent: "center", gap: 10 },
  loaderText: { color: MUTED, fontWeight: "700", marginTop: 8 },
  topRow: { flexDirection: "row-reverse", alignItems: "center", justifyContent: "space-between", marginBottom: 6 },
  sectionTitle: { fontSize: 12, fontWeight: "700", color: MUTED, textAlign: "right" },
  joinPill: { 
    flexDirection: "row-reverse", 
    alignItems: "center", 
    gap: 6, 
    paddingVertical: 8, 
    paddingHorizontal: 10, 
    borderRadius: 999, 
    borderWidth: 1, 
    borderColor: "rgba(2,132,199,0.25)", 
    backgroundColor: "rgba(2,132,199,0.08)" 
  },
  joinPillText: { color: BRAND_PRIMARY, fontWeight: "900", fontSize: 12 },
});