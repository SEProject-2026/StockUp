// src/home/selected-home.ts
import AsyncStorage from "@react-native-async-storage/async-storage";

const KEY = "stockup:selected_home_id";

export async function setSelectedHomeId(homeId: string | null) {
  if (!homeId) {
    await AsyncStorage.removeItem(KEY);
    return;
  }
  await AsyncStorage.setItem(KEY, homeId);
}

export async function getSelectedHomeId(): Promise<string | null> {
  const v = await AsyncStorage.getItem(KEY);
  return v ? v : null;
}
