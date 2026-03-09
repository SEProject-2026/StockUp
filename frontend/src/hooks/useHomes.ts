import { useState, useCallback, useMemo } from "react";
import { Alert } from "react-native";
import { getMyHomes, createHome, joinHomeByCode, type HomeDTO } from "@/src/api/homes";
import { router } from "expo-router";

export type Home = {
  id: string;
  name: string;
  pendingRequestsCount: number;
  adminId: string;
  expirationRange: number;
  updatedAt: string;
};

const mapDtoToHome = (dto: any): Home => ({
  id: String(dto.id),
  name: dto.name?.trim() || "בית ללא שם",
  pendingRequestsCount: Array.isArray(dto.join_requests) 
    ? dto.join_requests.length 
    : (dto.pendingRequestsCount ?? 0),
  adminId: String(dto.admin_id || dto.adminId || ""),
  expirationRange: typeof dto.expiration_range === "number" 
    ? dto.expiration_range 
    : (dto.expirationRange ?? 7),
  updatedAt: dto.updatedAt ?? dto.updated_at ?? new Date().toISOString(),
});

export function useHomes() {
  const [homes, setHomes] = useState<Home[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleAuthError = useCallback((msg: string) => {
    const s = (msg || "").toLowerCase();
    if (s.includes("401") || s.includes("unauthorized") || s.includes("token") || s.includes("auth")) {
      Alert.alert("צריך להתחבר", "פג תוקף החיבור, נא להתחבר מחדש.", [
        { text: "להתחברות", onPress: () => router.replace("/login") },
        { text: "ביטול", style: "cancel" }
      ]);
      return true;
    }
    return false;
  }, []);

  const loadHomes = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    try {
      mode === "initial" ? setLoading(true) : setRefreshing(true);
      const res = await getMyHomes();
      const rawData = res.data ?? [];
      setHomes(rawData.map(mapDtoToHome));
    } catch (e: any) {
      if (!handleAuthError(e.message)) {
        Alert.alert("שגיאה", "לא הצלחתי לטעון בתים");
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [handleAuthError]);

  const handleHomeAction = async (type: "create" | "join", value: string) => {
    const cleanValue = value.trim();
    if (!cleanValue) {
      Alert.alert("חסר מידע", type === "create" ? "נא להזין שם לבית" : "נא להזין קוד הצטרפות");
      return null;
    }

    setSaving(true);
    try {
      let res;
      if (type === "create") {
        res = await createHome({ name: cleanValue });
      } else {
        res = await joinHomeByCode({ home_code: cleanValue.toUpperCase() });
      }

      if (type === "join") {
        await loadHomes("refresh");
        return "joined_pending"; 
      }

      const newHome = mapDtoToHome(res.data);
      setHomes(prev => [newHome, ...prev]);
      return newHome.id;

    } catch (e: any) {
      if (!handleAuthError(e.message)) {
        Alert.alert("שגיאה", e.message || "הפעולה נכשלה");
      }
      return null;
    } finally {
      setSaving(false);
    }
  };

  const sortedHomes = useMemo(() => 
    [...homes].sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt)), 
  [homes]);

  return { 
    homes: sortedHomes, 
    loading, 
    refreshing, 
    saving, 
    loadHomes, 
    handleHomeAction 
  };
}