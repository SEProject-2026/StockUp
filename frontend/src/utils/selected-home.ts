import AsyncStorage from "@react-native-async-storage/async-storage";

const SELECTED_HOME_KEY = "@stockup:selected_home_id";

/**
 * Saving the ID of the selected home in the device's memory
 */
export const setSelectedHomeId = async (homeId: string | null): Promise<void> => {
  try {
    if (!homeId) {
      await AsyncStorage.removeItem(SELECTED_HOME_KEY);
    } else {
      await AsyncStorage.setItem(SELECTED_HOME_KEY, homeId);
    }
  } catch (error) {
    console.error("Error saving selected home ID:", error);
  }
};

/**
 * Retrieving the ID of the selected home from memory
 */
export const getSelectedHomeId = async (): Promise<string | null> => {
  try {
    return await AsyncStorage.getItem(SELECTED_HOME_KEY);
  } catch (error) {
    console.error("Error retrieving selected home ID:", error);
    return null;
  }
};

export const hasSelectedHome = async (): Promise<boolean> => {
  const id = await getSelectedHomeId();
  return !!id;
};