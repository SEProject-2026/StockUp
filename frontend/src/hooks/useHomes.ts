import { useState, useCallback, useMemo, useEffect } from "react";
import { Alert } from "react-native";
import { getMyHomes, createHome, joinHomeByCode } from "@/src/api/homes";
import { router } from "expo-router";

export type Home = {
  id: string;
  name: string;
  membersCount: number;
  updatedAt: string;
};

//normalizing data from the API
const mapDtoToHome = (dto: any) => ({
  id: String(dto.id),
  name: dto.name,
  membersCount: dto.membersCount ?? 1,
  updatedAt: dto.updatedAt ?? dto.updated_at ?? new Date().toISOString(),
});

export function useHomes() {
  const [homes, setHomes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);

  // Loading houses
  const loadHomes = useCallback(async (mode: "initial" | "refresh" = "initial") => {
    try {
      mode === "initial" ? setLoading(true) : setRefreshing(true);
      const res = await getMyHomes();
      setHomes((res.data ?? []).map(mapDtoToHome));
    } catch (e: any) {
      handleAuthError(e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // create/join home
  const handleHomeAction = async (type: "create" | "join", value: string) => {
    if (!value.trim()) return Alert.alert("שגיאה", "נא להזין ערך תקין");
    
    setSaving(true);
    try {
      const res = type === "create" 
        ? await createHome({ name: value }) 
        : await joinHomeByCode({ code: value });

      const newHome = mapDtoToHome(res.data);
      setHomes(prev => [newHome, ...prev]);
      return newHome.id; // Return the ID so we can navigate to it
    } catch (e: any) {
      handleAuthError(e.message);
      return null;
    } finally {
      setSaving(false);
    }
  };

  const handleAuthError = (msg: string) => {
    const s = msg.toLowerCase();
    if (s.includes("401") || s.includes("unauthorized") || s.includes("token")) {
      Alert.alert("צריך להתחבר", "פג תוקף החיבור, נא להתחבר מחדש.", [
        { text: "להתחברות", onPress: () => router.replace("/login") }
      ]);
    } else {
      Alert.alert("שגיאה", msg || "פעולה נכשלה");
    }
  };

  const sortedHomes = useMemo(() => 
    [...homes].sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt)), 
  [homes]);

  return { homes: sortedHomes, loading, refreshing, saving, loadHomes, handleHomeAction };
}