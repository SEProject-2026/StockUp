import React from "react";
import { View, Text, TextInput, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { styles, BRAND } from "./styles";

type Props = {
  isShoppingMode: boolean;
  onToggleMode: () => void;
  modeSubmitting: boolean;
  totalCount: number;
  pickedCount: number;
  query: string;
  setQuery: (q: string) => void;
};

export const ShoppingHeader = ({ isShoppingMode, onToggleMode, modeSubmitting, totalCount, pickedCount, query, setQuery }: Props) => {
  return (
    <View style={styles.topBlock}>
      <View style={styles.toggleCard}>
        <View style={styles.toggleTextWrap}>
          <Text style={styles.toggleTitle}>מצב קנייה</Text>
          <Text style={styles.toggleSubtitle}>כשהמצב דלוק אפשר לסמן פריטים שנאספו</Text>
        </View>
        <TouchableOpacity 
          onPress={onToggleMode} 
          disabled={modeSubmitting} 
          style={[styles.switchRoot, isShoppingMode && styles.switchRootActive]}
        >
          <View style={[styles.switchThumb, isShoppingMode && styles.switchThumbActive]} />
        </TouchableOpacity>
      </View>

      <View style={styles.summaryRow}>
        <SummaryCard title="פריטים" value={`${totalCount}`} icon="list-outline" />
        <SummaryCard title="סומנו" value={`${pickedCount}`} icon="checkmark-done-outline" />
      </View>

      <View style={styles.searchCard}>
        <Ionicons name="search" size={18} color={BRAND.MUTED} />
        <TextInput value={query} onChangeText={setQuery} placeholder="חיפוש בכל הרשימה..." placeholderTextColor={BRAND.MUTED} style={styles.searchInput} textAlign="right" />
        {!!query && (
          <TouchableOpacity onPress={() => setQuery("")}>
            <Ionicons name="close-circle" size={18} color={BRAND.MUTED} />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const SummaryCard = ({ title, value, icon }: any) => (
  <View style={styles.summaryCard}>
    <View style={styles.summaryIconWrap}><Ionicons name={icon} size={17} color={BRAND.PRIMARY} /></View>
    <View style={{ flex: 1 }}>
      <Text style={styles.summaryTitle}>{title}</Text>
      <Text style={styles.summaryValue}>{value}</Text>
    </View>
  </View>
);