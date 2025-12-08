// app/components/InventoryItemRow.tsx
import React from "react";
import { View, Text, Pressable } from "react-native";
import { Swipeable } from "react-native-gesture-handler";
import type { InventoryItem } from "../inventory-store";

type InventoryItemRowProps = {
  item: InventoryItem;
  variant: "warning" | "neutral";
  styles: any;
  onPress: () => void;
  onIncrement: () => void;
  onDecrement: () => void;
  onDelete?: () => void;
};

export function InventoryItemRow({
  item,
  variant,
  styles,
  onPress,
  onIncrement,
  onDecrement,
  onDelete,
}: InventoryItemRowProps) {
  const categoryLabel =
    item.category === "fridge"
      ? "מקרר"
      : item.category === "freezer"
      ? "מקפיא"
      : "מזווה";

  const renderRightActions = () => (
    <Pressable
      onPress={onDelete}
      style={styles.deleteAction}
    >
      <Text style={styles.deleteActionText}>מחק</Text>
    </Pressable>
  );

  return (
    <Swipeable renderRightActions={onDelete ? renderRightActions : undefined}>
      <Pressable
        style={[
          styles.homeItemRow,
          variant === "warning" && styles.homeItemRowWarning,
        ]}
        onPress={onPress}
      >
        <View style={styles.homeItemLeftStrip} />

        <View style={styles.homeItemMain}>
          <View style={styles.homeItemHeaderRow}>
            <Text style={styles.homeItemName}>{item.name}</Text>

            {/* אזור הפלוס/מינוס + הכמות */}
            <View style={styles.qtyControlsRow}>
              <Pressable
                onPress={onDecrement}
                style={styles.qtyButton}
              >
                <Text style={styles.qtyButtonText}>-</Text>
              </Pressable>

              <View style={styles.homeItemQtyChip}>
                <Text style={styles.homeItemQtyText}>x{item.quantity}</Text>
              </View>

              <Pressable
                onPress={onIncrement}
                style={styles.qtyButton}
              >
                <Text style={styles.qtyButtonText}>+</Text>
              </Pressable>
            </View>
          </View>

          <View style={styles.homeItemMetaRow}>
            <Text style={styles.homeItemMetaText}>
              {categoryLabel}
              {item.expiresAt ? ` · תוקף ${item.expiresAt}` : ""}
            </Text>
          </View>
        </View>
      </Pressable>
    </Swipeable>
  );
}
