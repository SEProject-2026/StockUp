import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams, usePathname } from "expo-router";

type TabKey = "home" | "inventory" | "shopping-list" | "settings";

interface BottomNavBarProps {
  activeTab?: TabKey;
}

export default function BottomNavBar({ activeTab }: BottomNavBarProps) {
  const pathname = usePathname();
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  const currentHomeId = homeId ? String(homeId) : undefined;
  
  // Auto-guess based on URL if activeTab is not manually passed
  const current: TabKey =
    activeTab ??
    (pathname.startsWith("/inventory")
      ? "inventory"
      : pathname.startsWith("/shoppingList")
      ? "shopping-list"
      : pathname.startsWith("/settings")
      ? "settings"
      : "home");

  const handlePress = (tab: TabKey) => {
    if (tab === current) return;

    switch (tab) {
      case "home":
        if (currentHomeId) {
          router.replace({
            pathname: "/home/[homeId]",
            params: { homeId: currentHomeId },
          });
        } else {
          router.replace("/home/home"); // מסך רשימת הבתים
        }
        break;

      case "inventory":
        if (currentHomeId) {
          router.replace({
            pathname: "/inventory/inventory",
            params: { homeId: currentHomeId },
          });
        } else {
          router.replace("/inventory/inventory"); // או "/homes" אם מלאי חייב בית
        }
        break;
      case "shopping-list":
        //router.replace("/ShoppingListScreen");
        break;
      case "settings":
        if (currentHomeId) {
          router.replace({
            pathname: "/settings",
            params: { homeId: currentHomeId },
          });
        } else {
          router.replace("/settings"); // או "/homes" אם מלאי חייב בית
        }
        break;
    }
  };

  return (
    <View style={styles.bottomNav}>
      <NavItem
        label="בית"
        icon="home-outline"
        isActive={current === "home"}
        onPress={() => handlePress("home")}
      />
      <NavItem
        label="מלאי"
        icon="grid-outline"
        isActive={current === "inventory"}
        onPress={() => handlePress("inventory")}
      />
      <NavItem
        label="רשימת קניות"
        icon="list-outline"
        isActive={current === "shopping-list"}
        onPress={() => handlePress("shopping-list")}
      />
      <NavItem
        label="הגדרות"
        icon="settings-outline"
        isActive={current === "settings"}
        onPress={() => handlePress("settings")}
      />
    </View>
  );
}

function NavItem({
  label,
  icon,
  isActive,
  onPress,
}: {
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  isActive?: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity style={styles.bottomNavItem} onPress={onPress}>
      <Ionicons
        name={icon}
        size={22}
        color={isActive ? "#111827" : "#9CA3AF"}
      />
      <Text
        style={[
          styles.bottomNavLabel,
          isActive && styles.bottomNavLabelActive,
        ]}
      >
        {label}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  bottomNav: {
    flexDirection: "row-reverse",
    justifyContent: "space-around",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingTop: 8,
    paddingBottom: 10,
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
    backgroundColor: "#FFFFFF",
  },
  bottomNavItem: {
    flex: 1,
    alignItems: "center",
    gap: 2,
  },
  bottomNavLabel: {
    fontSize: 11,
    color: "#9CA3AF",
  },
  bottomNavLabelActive: {
    color: "#111827",
    fontWeight: "600",
  },
});
