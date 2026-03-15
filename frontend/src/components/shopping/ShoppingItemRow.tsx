import React from "react";
import { View, Text, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { styles, BRAND } from "./styles";
import { type ShoppingItem } from "@/src/hooks/useShoppingList";

type Props = {
  item: ShoppingItem;
  mode: "EDIT" | "SHOPPING";
  isPicked: boolean;
  onToggle: () => void;
  onIncrease: () => void;
  onDecrease: () => void;
  onRemove: () => void;
};

export const ShoppingItemRow = React.memo(({ item, mode, isPicked, onToggle, onIncrease, onDecrease, onRemove }: Props) => {
  const qty = item.quantity ?? 1;

  return (
    <View style={[styles.noteRow, isPicked && styles.noteRowPicked]}>
      <View style={styles.noteActions}>
        {mode === "SHOPPING" ? (
          <View style={styles.noteQtyPill}><Text style={styles.noteQtyText}>{qty}</Text></View>
        ) : (
          <>
            <TouchableOpacity onPress={onRemove} style={styles.noteIconBtn}>
              <Ionicons name="trash-outline" size={16} color={BRAND.DANGER} />
            </TouchableOpacity>
            <TouchableOpacity onPress={onDecrease} style={styles.noteIconBtn}>
              <Ionicons name="remove" size={16} color={BRAND.PRIMARY} />
            </TouchableOpacity>
            <View style={styles.noteQtyPill}><Text style={styles.noteQtyText}>{qty}</Text></View>
            <TouchableOpacity onPress={onIncrease} style={styles.noteIconBtn}>
              <Ionicons name="add" size={16} color={BRAND.PRIMARY} />
            </TouchableOpacity>
          </>
        )}
      </View>

      <View style={styles.noteTextWrap}>
        <View style={styles.noteTitleRow}>
          {mode === "SHOPPING" && (
            <TouchableOpacity onPress={onToggle} style={[styles.pickBtn, isPicked && styles.pickBtnActive]}>
              <Ionicons name={isPicked ? "checkmark" : "ellipse-outline"} size={16} color={isPicked ? "#fff" : BRAND.PRIMARY} />
            </TouchableOpacity>
          )}
          <Text style={[styles.noteTitle, isPicked && styles.noteTitlePicked]} numberOfLines={1}>
            {item?.name}
          </Text>
        </View>
      </View>
    </View>
  );
});