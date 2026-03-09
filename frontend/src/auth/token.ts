import AsyncStorage from "@react-native-async-storage/async-storage";

const TOKEN_KEY = "access_token";
const CURRENT_USER_ID_KEY = "current_user_id";

export async function setAccessToken(token: string) {
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

export async function getAccessToken() {
  return await AsyncStorage.getItem(TOKEN_KEY);
}

export async function clearAccessToken() {
  await AsyncStorage.removeItem(TOKEN_KEY);
}

export async function setCurrentUserId(userId: string) {
  await AsyncStorage.setItem(CURRENT_USER_ID_KEY, userId);
}

export async function getCurrentUserId() {
  return AsyncStorage.getItem(CURRENT_USER_ID_KEY);
}

export async function clearCurrentUserId() {
  await AsyncStorage.removeItem(CURRENT_USER_ID_KEY);
}