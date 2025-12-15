import { Platform } from "react-native";

const DEV_HOST =
  Platform.OS === "android"
    ? "10.0.2.2"   // אנדרואיד אמולטור
    : "localhost"; // iOS סימולטור

export const API_BASE_URL = "http://10.100.102.25:8000";
