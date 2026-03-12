import React, { useEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  TextInput,
  TouchableOpacity,
  Modal,
  Pressable,
  Alert,
} from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

import { useShoppingList, type LocationKey } from "@/src/hooks/useShoppingList";
import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";
import {
  LOCATIONS,
  locationLabel,
  locationIcon,
} from "@/src/hooks/useBaseMode";

const BRAND = {
  BG: "#F4F4F4",
  CARD: "#FFFFFF",
  BORDER: "#E5E7EB",
  TEXT: "#111827",
  MUTED: "#6B7280",
  PRIMARY: "#0284C7",
  PRIMARY_SOFT: "#E5F3FF",
  DANGER: "#DC2626",
  SUCCESS: "#16A34A",
  NOTE_LINE: "#E8EDF5",
};

type ShoppingMode = "EDIT" | "SHOPPING";
type SectionLocation = LocationKey | "UNSORTED";

type ShoppingItem = {
  id: string;
  name?: string;
  quantity?: number;
  qty?: number;
  targetQty?: number;
  location?: LocationKey | null;
};

type GroupedSection = {
  location: SectionLocation;
  title: string;
  items: ShoppingItem[];
};

type AddShoppingItemPayload = {
  name: string;
  qty: number;
  location: LocationKey;
};

function isLocationKey(value: unknown): value is LocationKey {
  return (
    typeof value === "string" &&
    (LOCATIONS as readonly string[]).includes(value)
  );
}

function getItemQty(item: ShoppingItem) {
  if (typeof item?.quantity === "number") return item.quantity;
  if (typeof item?.qty === "number") return item.qty;
  if (typeof item?.targetQty === "number") return item.targetQty;
  return 1;
}

function getItemLocation(item: ShoppingItem): SectionLocation {
  return isLocationKey(item?.location) ? item.location : "UNSORTED";
}

function getLocationTitle(location: SectionLocation) {
  if (location === "UNSORTED") return "ללא מיקום";
  return locationLabel(location as any);
}

function getLocationIconName(location: SectionLocation) {
  if (location === "UNSORTED") return "albums-outline";
  return locationIcon(location as any);
}

function SummaryCard({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: any;
}) {
  return (
    <View style={styles.summaryCard}>
      <View style={styles.summaryIconWrap}>
        <Ionicons name={icon} size={17} color={BRAND.PRIMARY} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.summaryTitle}>{title}</Text>
        <Text style={styles.summaryValue}>{value}</Text>
      </View>
    </View>
  );
}

function ShoppingToggle({
  enabled,
  onToggle,
}: {
  enabled: boolean;
  onToggle: () => void;
}) {
  return (
    <View style={styles.toggleCard}>
      <View style={styles.toggleTextWrap}>
        <Text style={styles.toggleTitle}>מצב קנייה</Text>
        <Text style={styles.toggleSubtitle}>
          כשהמצב דלוק אפשר לסמן פריטים שנאספו
        </Text>
      </View>

      <TouchableOpacity
        activeOpacity={0.9}
        onPress={onToggle}
        style={[styles.switchRoot, enabled && styles.switchRootActive]}
      >
        <View style={[styles.switchThumb, enabled && styles.switchThumbActive]} />
      </TouchableOpacity>
    </View>
  );
}

function AddShoppingItemModal(props: {
  open: boolean;
  onClose: () => void;
  onAdd: (payload: AddShoppingItemPayload) => Promise<void> | void;
}) {
  const [name, setName] = useState("");
  const [qty, setQty] = useState("1");
  const [loc, setLoc] = useState<LocationKey>("FRIDGE");
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    const cleanName = name.trim();
    const cleanQty = Number(qty);

    if (!cleanName) {
      Alert.alert("חסר שם מוצר", "צריך להזין שם מוצר לפני ההוספה.");
      return;
    }

    if (!Number.isFinite(cleanQty) || cleanQty <= 0) {
      Alert.alert("כמות לא תקינה", "יש להזין כמות גדולה מ־0.");
      return;
    }

    try {
      setSubmitting(true);
      await props.onAdd({
        name: cleanName,
        qty: cleanQty,
        location: loc,
      });
      setName("");
      setQty("1");
      setLoc("FRIDGE");
      props.onClose();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Modal
      visible={props.open}
      transparent
      animationType="slide"
      onRequestClose={props.onClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={{ flex: 1 }}
      >
        <Pressable style={styles.modalBackdrop} onPress={props.onClose}>
          <Pressable style={styles.modalCard} onPress={(e) => e.stopPropagation()}>
            <View style={styles.modalHandle} />

            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>הוספת פריט לרשימת קניות</Text>

              <TouchableOpacity
                onPress={props.onClose}
                style={styles.iconBtn}
                disabled={submitting}
              >
                <Ionicons name="close" size={20} color={BRAND.TEXT} />
              </TouchableOpacity>
            </View>

            <Text style={styles.modalSubtitle}>
              הוסיפי פריט, כמות ומיקום כדי לשלב אותו נכון ברשימה.
            </Text>

            <View style={styles.field}>
              <Text style={styles.label}>שם מוצר</Text>
              <TextInput
                value={name}
                onChangeText={setName}
                placeholder="לדוגמה: חלב"
                placeholderTextColor={BRAND.MUTED}
                style={styles.input}
                textAlign="right"
                editable={!submitting}
              />
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>כמות</Text>
              <TextInput
                value={qty}
                onChangeText={setQty}
                keyboardType="numeric"
                style={styles.input}
                textAlign="right"
                editable={!submitting}
              />
            </View>

            <Text style={styles.label}>מיקום</Text>
            <View style={styles.locationWrap}>
              {LOCATIONS.map((location) => {
                const typedLocation = location as LocationKey;

                return (
                  <TouchableOpacity
                    key={typedLocation}
                    onPress={() => setLoc(typedLocation)}
                    style={[
                      styles.locationOption,
                      loc === typedLocation && styles.locationOptionActive,
                    ]}
                    disabled={submitting}
                    activeOpacity={0.9}
                  >
                    <Ionicons
                      name={locationIcon(typedLocation as any) as any}
                      size={16}
                      color={loc === typedLocation ? BRAND.PRIMARY : BRAND.MUTED}
                    />
                    <Text
                      style={[
                        styles.locationOptionText,
                        loc === typedLocation && styles.locationOptionTextActive,
                      ]}
                    >
                      {locationLabel(typedLocation as any)}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <TouchableOpacity
              activeOpacity={0.9}
              onPress={submit}
              disabled={submitting}
              style={[styles.primaryBtn, submitting && { opacity: 0.7 }]}
            >
              <Text style={styles.primaryBtnText}>
                {submitting ? "מוסיף..." : "הוסף פריט"}
              </Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function NotebookRow(props: {
  item: ShoppingItem;
  mode: ShoppingMode;
  isPicked: boolean;
  onToggle: () => void;
  onIncrease: () => void;
  onDecrease: () => void;
  onRemove: () => void;
}) {
  const qty = getItemQty(props.item);
  const showPickedStyle = props.isPicked;

  return (
   <View style={[styles.noteRow, showPickedStyle && styles.noteRowPicked]}>
    <View style={styles.noteActions}>
        {props.mode === "SHOPPING" ? (
        <View style={styles.noteQtyPill}>
            <Text style={styles.noteQtyText}>{qty}</Text>
        </View>
        ) : (
        <>
            <TouchableOpacity
            onPress={props.onRemove}
            style={styles.noteIconBtn}
            activeOpacity={0.85}
            >
            <Ionicons name="trash-outline" size={16} color={BRAND.DANGER} />
            </TouchableOpacity>

            <TouchableOpacity
            onPress={props.onDecrease}
            style={styles.noteIconBtn}
            activeOpacity={0.85}
            >
            <Ionicons name="remove" size={16} color={BRAND.PRIMARY} />
            </TouchableOpacity>

            <View style={styles.noteQtyPill}>
            <Text style={styles.noteQtyText}>{qty}</Text>
            </View>

            <TouchableOpacity
            onPress={props.onIncrease}
            style={styles.noteIconBtn}
            activeOpacity={0.85}
            >
            <Ionicons name="add" size={16} color={BRAND.PRIMARY} />
            </TouchableOpacity>
        </>
        )}
    </View>

    <View style={styles.noteTextWrap}>
        <View style={styles.noteTitleRow}>
        {props.mode === "SHOPPING" && (
            <TouchableOpacity
            onPress={props.onToggle}
            style={[styles.pickBtn, props.isPicked && styles.pickBtnActive]}
            activeOpacity={0.85}
            >
            <Ionicons
                name={props.isPicked ? "checkmark" : "ellipse-outline"}
                size={16}
                color={props.isPicked ? "#fff" : BRAND.PRIMARY}
            />
            </TouchableOpacity>
        )}

        <Text
            style={[styles.noteTitle, showPickedStyle && styles.noteTitlePicked]}
            numberOfLines={1}
        >
            {props.item?.name ?? "ללא שם"}
        </Text>
        </View>
    </View>
    </View>
  );
}

function SectionHeader({
  title,
  location,
}: {
  title: string;
  location: SectionLocation;
}) {
  return (
    <View style={styles.sectionBlock}>
      <View style={styles.locationHeader}>
        <View style={styles.locationHeaderLine} />
        <View style={styles.locationHeaderChip}>
          <Ionicons
            name={getLocationIconName(location) as any}
            size={15}
            color={BRAND.PRIMARY}
          />
          <Text style={styles.locationHeaderText}>{title}</Text>
        </View>
      </View>
    </View>
  );
}

export default function ShoppingListScreen() {
  const insets = useSafeAreaInsets();
  const [addOpen, setAddOpen] = useState(false);

  const { homeId, listId, listName } = useLocalSearchParams<{
    homeId?: string;
    listId?: string;
    listName?: string;
  }>();

  const {
    mode,
    setMode,
    items,
    filteredItems,
    loading,
    picked,
    togglePick,
    query,
    setQuery,
    addItem,
    removeItem,
    finishShopping,
    updateQuantity,
  } = useShoppingList({
    homeId: homeId ?? "",
    listId: listId ?? "",
  });

  useEffect(() => {
    if (mode !== "EDIT") {
      setMode("EDIT");
    }
  }, []);

  const isShoppingMode = mode === "SHOPPING";

  const pickedCount = useMemo(
    () => Object.values(picked).filter(Boolean).length,
    [picked]
  );

  const totalCount = items.length;

  const groupedSections = useMemo<GroupedSection[]>(() => {
    const groups = new Map<SectionLocation, ShoppingItem[]>();

    for (const item of filteredItems as ShoppingItem[]) {
      const location = getItemLocation(item);
      if (!groups.has(location)) groups.set(location, []);
      groups.get(location)!.push(item);
    }

    const orderedKnown: GroupedSection[] = (LOCATIONS as readonly string[])
      .filter((loc) => groups.has(loc as LocationKey))
      .map((loc) => {
        const typedLoc = loc as LocationKey;
        return {
          location: typedLoc,
          title: getLocationTitle(typedLoc),
          items: groups.get(typedLoc) ?? [],
        };
      });

    const unsorted: GroupedSection[] = groups.has("UNSORTED")
      ? [
          {
            location: "UNSORTED",
            title: getLocationTitle("UNSORTED"),
            items: groups.get("UNSORTED") ?? [],
          },
        ]
      : [];

    return [...orderedKnown, ...unsorted];
  }, [filteredItems]);

  function handleToggleShoppingMode() {
    if (isShoppingMode) {
      setMode("EDIT");
      return;
    }
    setMode("SHOPPING");
  }

  function handleShoppingDone() {
    Alert.alert(
      "סיום מצב קנייה",
      "מה תרצי לעשות עם הפריטים שסומנו?",
      [
        {
          text: "ביטול",
          style: "cancel",
        },
        {
          text: "כבה מצב קנייה",
          onPress: () => setMode("EDIT"),
        },
        {
          text: "רוקן פריטים שנקנו",
          style: "destructive",
          onPress: () => finishShopping(),
        },
      ]
    );
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />
        <ScreenHeader
          title={listName || "רשימת קניות"}
          onBack={() => router.back()}
        />
        <View style={styles.center}>
          <ActivityIndicator size="large" color={BRAND.PRIMARY} />
          <Text style={styles.loadingText}>טוען רשימת קניות...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />

        <ScreenHeader
          title={listName || "רשימת קניות"}
          onBack={() => router.back()}
        />

        <AddShoppingItemModal
          open={addOpen}
          onClose={() => setAddOpen(false)}
          onAdd={({ name, qty, location }) =>
            addItem(name, qty, "manual", location)
          }
        />

        <FlatList
          data={groupedSections}
          keyExtractor={(section) => String(section.location)}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{
            padding: 16,
            paddingBottom: 165 + insets.bottom,
          }}
          ListHeaderComponent={
            <View style={styles.topBlock}>
              <ShoppingToggle
                enabled={isShoppingMode}
                onToggle={handleToggleShoppingMode}
              />

              <View style={styles.summaryRow}>
                <SummaryCard
                  title="פריטים"
                  value={`${totalCount}`}
                  icon="list-outline"
                />
                <SummaryCard
                  title="סומנו"
                  value={`${pickedCount}`}
                  icon="checkmark-done-outline"
                />
              </View>

              <View style={styles.searchCard}>
                <Ionicons name="search" size={18} color={BRAND.MUTED} />
                <TextInput
                  value={query}
                  onChangeText={setQuery}
                  placeholder="חיפוש בכל הרשימה..."
                  placeholderTextColor={BRAND.MUTED}
                  style={styles.searchInput}
                  textAlign="right"
                />
                {!!query && (
                  <TouchableOpacity onPress={() => setQuery("")}>
                    <Ionicons
                      name="close-circle"
                      size={18}
                      color={BRAND.MUTED}
                    />
                  </TouchableOpacity>
                )}
              </View>
            </View>
          }
          renderItem={({ item: section }) => (
            <View style={styles.sectionContainer}>
              <SectionHeader
                title={section.title}
                location={section.location}
              />

              <View style={styles.notebookCard}>
                {section.items.map((item, index) => (
                  <View key={item.id}>
                    <NotebookRow
                      item={item}
                      mode={mode as ShoppingMode}
                      isPicked={!!picked[item.id]}
                      onToggle={() => togglePick(item.id)}
                      onIncrease={() => updateQuantity(item.id, 1)}
                      onDecrease={() => updateQuantity(item.id, -1)}
                      onRemove={() => removeItem(item.id)}
                    />
                    {index < section.items.length - 1 && (
                      <View style={styles.separator} />
                    )}
                  </View>
                ))}
              </View>
            </View>
          )}
          ItemSeparatorComponent={() => <View style={{ height: 14 }} />}
          ListEmptyComponent={
            <View style={styles.emptyCard}>
              <Ionicons name="basket-outline" size={24} color={BRAND.MUTED} />
              <Text style={styles.emptyTitle}>אין פריטים להצגה</Text>
              <Text style={styles.emptySubtitle}>
                אפשר להוסיף פריט חדש דרך הכפתור בתחתית המסך.
              </Text>
            </View>
          }
        />

        <View style={[styles.bottomActions, { paddingBottom: 16 + insets.bottom }]}>
          {isShoppingMode ? (
            <>
              <TouchableOpacity
                activeOpacity={0.9}
                onPress={handleShoppingDone}
                style={styles.secondaryBtn}
              >
                <Ionicons name="checkmark-done-outline" size={18} color={BRAND.TEXT} />
                <Text style={styles.secondaryBtnText}>סיום מצב קנייה</Text>
              </TouchableOpacity>

              <TouchableOpacity
                activeOpacity={0.9}
                onPress={() => setAddOpen(true)}
                style={styles.primaryBottomBtn}
              >
                <Ionicons name="add" size={18} color="#fff" />
                <Text style={styles.primaryBottomBtnText}>הוסף פריט</Text>
              </TouchableOpacity>
            </>
          ) : (
            <TouchableOpacity
              activeOpacity={0.9}
              onPress={() => setAddOpen(true)}
              style={styles.primaryBottomBtnFull}
            >
              <Ionicons name="add" size={18} color="#fff" />
              <Text style={styles.primaryBottomBtnText}>הוסף פריט</Text>
            </TouchableOpacity>
          )}
        </View>
      </SafeAreaView>

      <View style={[styles.bottomBar, { paddingBottom: 10 + insets.bottom }]}>
        <BottomNavBar activeTab="shopping-list" />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: BRAND.BG,
  },

  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },

  loadingText: {
    marginTop: 8,
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 13,
  },

  topBlock: {
    marginBottom: 14,
  },

  toggleCard: {
    backgroundColor: "rgba(255,255,255,0.92)",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 16,
    paddingHorizontal: 14,
    paddingVertical: 14,
    marginBottom: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },

  toggleTextWrap: {
    flex: 1,
    alignItems: "flex-end",
  },

  toggleTitle: {
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 14,
    textAlign: "right",
  },

  toggleSubtitle: {
    marginTop: 3,
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 11.5,
    textAlign: "right",
  },

  switchRootActive: {
    backgroundColor: BRAND.PRIMARY,
  },

switchRoot: {
  width: 54,
  height: 32,
  borderRadius: 999,
  backgroundColor: "#D1D5DB",
  justifyContent: "center",
  paddingHorizontal: 4,
  overflow: "hidden",
},

switchThumb: {
  width: 24,
  height: 24,
  borderRadius: 999,
  backgroundColor: "#FFFFFF",
  transform: [{ translateX: 0 }],
},

switchThumbActive: {
  transform: [{ translateX: 20 }],
},

  summaryRow: {
    flexDirection: "row-reverse",
    gap: 10,
  },

  summaryCard: {
    flex: 1,
    backgroundColor: BRAND.CARD,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    padding: 11,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },

  summaryIconWrap: {
    width: 34,
    height: 34,
    borderRadius: 11,
    backgroundColor: BRAND.PRIMARY_SOFT,
    alignItems: "center",
    justifyContent: "center",
  },

  summaryTitle: {
    color: BRAND.MUTED,
    fontWeight: "800",
    fontSize: 11,
    textAlign: "right",
  },

  summaryValue: {
    marginTop: 2,
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 16,
    textAlign: "right",
  },

  searchCard: {
    marginTop: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 11,
    borderRadius: 16,
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
  },

  searchInput: {
    flex: 1,
    color: BRAND.TEXT,
    fontWeight: "700",
    fontSize: 13,
  },

  sectionContainer: {
    marginBottom: 2,
  },

  sectionBlock: {
    marginBottom: 8,
  },

  locationHeader: {
    position: "relative",
    justifyContent: "center",
  },

  locationHeaderLine: {
    height: 1,
    backgroundColor: "#DCE4EF",
    width: "100%",
  },

  locationHeaderChip: {
    position: "absolute",
    alignSelf: "flex-end",
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    backgroundColor: BRAND.BG,
    paddingHorizontal: 10,
    height: 26,
    borderRadius: 999,
  },

  locationHeaderText: {
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 13,
  },

  notebookCard: {
    backgroundColor: "rgba(255,255,255,0.97)",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#E8ECF3",
    overflow: "hidden",
    paddingVertical: 2,
  },

  separator: {
    height: 1,
    backgroundColor: BRAND.NOTE_LINE,
    marginHorizontal: 1,
  },

  noteRow: {
    minHeight: 56,
    paddingRight: 14,
    paddingLeft: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },

  noteRowPicked: {
    backgroundColor: "rgba(22,163,74,0.05)",
  },

  noteActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },

  noteIconBtn: {
    width: 28,
    height: 28,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F7FAFD",
    borderWidth: 1,
    borderColor: "#E7EDF5",
  },

  pickBtn: {
    width: 30,
    height: 30,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F7FAFD",
    borderWidth: 1,
    borderColor: "#D7E7F7",
  },

  pickBtnActive: {
    backgroundColor: BRAND.SUCCESS,
    borderColor: BRAND.SUCCESS,
  },

  noteQtyPill: {
    minWidth: 30,
    height: 28,
    paddingHorizontal: 8,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F7FAFD",
    borderWidth: 1,
    borderColor: "#E7EDF5",
  },
    noteTitleRow: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    },
  noteQtyText: {
    fontSize: 12,
    fontWeight: "900",
    color: BRAND.TEXT,
  },

  noteTextWrap: {
    flex: 1,
    alignItems: "flex-end",
    marginLeft: 12,
  },

  noteTitle: {
    fontSize: 14,
    fontWeight: "800",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  noteTitlePicked: {
    textDecorationLine: "line-through",
    color: "#6B7280",
  },

  noteMeta: {
    marginTop: 2,
    fontSize: 11,
    color: BRAND.MUTED,
    fontWeight: "700",
    textAlign: "right",
  },

  emptyCard: {
    padding: 28,
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.92)",
    borderRadius: 20,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
  },

  emptyTitle: {
    marginTop: 10,
    color: BRAND.TEXT,
    fontWeight: "800",
    fontSize: 15,
  },

  emptySubtitle: {
    marginTop: 6,
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 12,
    textAlign: "center",
    lineHeight: 18,
  },

  bottomActions: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 58,
    paddingHorizontal: 16,
    paddingTop: 12,
    backgroundColor: "rgba(244,244,244,0.96)",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
    flexDirection: "row-reverse",
    gap: 10,
  },

  primaryBottomBtn: {
    flex: 1,
    height: 48,
    borderRadius: 15,
    backgroundColor: BRAND.PRIMARY,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },

  primaryBottomBtnFull: {
    width: "100%",
    height: 48,
    borderRadius: 15,
    backgroundColor: BRAND.PRIMARY,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },

  primaryBottomBtnText: {
    color: "#fff",
    fontWeight: "900",
    fontSize: 14,
  },

  secondaryBtn: {
    flex: 1,
    height: 48,
    borderRadius: 15,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },

  secondaryBtnText: {
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 14,
  },

  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "rgba(255,255,255,0.92)",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },

  modalBackdrop: {
    flex: 1,
    backgroundColor: "rgba(17,24,39,0.35)",
    justifyContent: "flex-end",
    padding: 12,
  },

  modalCard: {
    backgroundColor: BRAND.CARD,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    paddingBottom: Platform.OS === "ios" ? 30 : 16,
  },

  modalHandle: {
    alignSelf: "center",
    width: 42,
    height: 5,
    borderRadius: 999,
    backgroundColor: "#D1D5DB",
    marginBottom: 12,
  },

  modalHeader: {
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "space-between",
  },

  modalTitle: {
    fontSize: 16,
    fontWeight: "900",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  modalSubtitle: {
    marginTop: 6,
    marginBottom: 14,
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 12,
    textAlign: "right",
    lineHeight: 18,
  },

  iconBtn: {
    padding: 6,
  },

  field: {
    marginBottom: 12,
  },

  label: {
    marginBottom: 6,
    color: BRAND.MUTED,
    fontWeight: "800",
    fontSize: 11.5,
    textAlign: "right",
  },

  input: {
    backgroundColor: "#FAFBFD",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 13,
    paddingHorizontal: 12,
    paddingVertical: 11,
    color: BRAND.TEXT,
    fontWeight: "700",
    fontSize: 13,
  },

  locationWrap: {
    flexDirection: "row-reverse",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 14,
  },

  locationOption: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 11,
    paddingVertical: 9,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    backgroundColor: "#fff",
  },

  locationOptionActive: {
    backgroundColor: "#F4FBFF",
    borderColor: "rgba(2,132,199,0.35)",
  },

  locationOptionText: {
    color: BRAND.MUTED,
    fontWeight: "800",
    fontSize: 12,
  },

  locationOptionTextActive: {
    color: BRAND.TEXT,
  },

  primaryBtn: {
    marginTop: 4,
    height: 46,
    borderRadius: 14,
    backgroundColor: BRAND.PRIMARY,
    alignItems: "center",
    justifyContent: "center",
  },

  primaryBtnText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "900",
  },
});