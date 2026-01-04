import Constants from "expo-constants";
import { Platform } from "react-native";

function getDevServerHost() {
  // Android emulator only
  if (Platform.OS === "android" && !Constants.expoConfig?.hostUri) {
    return "10.0.2.2";
  }

  const hostUri =
    Constants.expoConfig?.hostUri ??
    (Constants as any).manifest2?.extra?.expoClient?.hostUri ??
    (Constants as any).manifest?.debuggerHost;

  const host = typeof hostUri === "string" ? hostUri.split(":")[0] : "localhost";
  return host;
}

export const API_BASE_URL = `http://${getDevServerHost()}:8000`;
