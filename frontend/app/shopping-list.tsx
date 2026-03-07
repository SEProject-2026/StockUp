// frontend/app/shopping-list.tsx
import React, { useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Modal,
  Pressable,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { SafeAreaView, useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";

import ScreenHeader from "@/src/layout/ScreenHeader";
import PrimaryButton from "@/src/components/ui/buttons/PrimaryButton";
import BottomNavBar from "@/src/layout/BottomNavBar";

const BRAND = {
  BG: "#F4F4F4",
  CARD: "#FFFFFF",
  BORDER: "#E5E7EB",
  TEXT: "#111827",
  MUTED: "#6B7280",
  PRIMARY: "#0284C7",
  PRIMARY_SOFT: "#E5F3FF",
  SUCCESS: "#16A34A",
  SUCCESS_SOFT: "#ECFDF3",
  DANGER: "#DC2626",
  NOTE_LINE: "#E8EDF5",
};

type Mode = "EDIT" | "SHOPPING";

type ShoppingItem = {
  id: string;
  name: string;
  quantity?: number;
  source?: "manual" | "suggestion" | "baseline_sync";
};

type SuggestionItem = {
  id: string;
  name: string;
  reason?: string;
};

function normalizeName(s: string) {
  return s.trim().toLowerCase();
}

function makeId(prefix = "id") {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`;
}

function sourceLabel(source?: ShoppingItem["source"]) {
  switch (source) {
    case "manual":
      return "נוסף ידנית";
    case "suggestion":
      return "מהמלצות";
    case "baseline_sync":
      return "מסנכרון";
    default:
      return "";
  }
}

// ------------------------------
// API placeholders
// ------------------------------
async function apiGetShoppingList(): Promise<ShoppingItem[]> {
  return [
    { id: "1", name: "חלב 3%", quantity: 2, source: "manual" },
    { id: "2", name: "לחם", quantity: 1, source: "manual" },
  ];
}

async function apiGetSuggestions(): Promise<SuggestionItem[]> {
  return [
    { id: "s1", name: "ביצים", reason: "נרכש לעיתים קרובות" },
    { id: "s2", name: "גבינה צהובה", reason: "חסר לפי הרגלי צריכה" },
    { id: "s3", name: "נייר טואלט", reason: "מלאי נמוך" },
  ];
}

async function apiSyncBaseline(): Promise<{
  toAdd: { name: string; quantity?: number }[];
}> {
  return { toAdd: [{ name: "אורז", quantity: 1 }] };
}

async function apiCompleteShopping(purchasedIds: string[]): Promise<void> {
  return;
}

// ------------------------------
// Small UI pieces
// ------------------------------
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

function RowSeparator() {
  return <View style={{ height: 10 }} />;
}

// ------------------------------
// Suggestions Modal
// ------------------------------
function SuggestionsModal(props: {
  open: boolean;
  onClose: () => void;
  suggestions: SuggestionItem[];
  existingNamesSet: Set<string>;
  onAdd: (name: string) => void;
}) {
  const [q, setQ] = useState("");

  const filtered = useMemo(() => {
    const query = normalizeName(q);
    const base = props.suggestions.filter(
      (s) => !props.existingNamesSet.has(normalizeName(s.name))
    );
    if (!query) return base;
    return base.filter((s) => normalizeName(s.name).includes(query));
  }, [q, props.suggestions, props.existingNamesSet]);

  return (
    <Modal
      visible={props.open}
      transparent
      animationType="fade"
      onRequestClose={props.onClose}
    >
      <Pressable style={styles.modalBackdrop} onPress={props.onClose}>
        <Pressable style={styles.modalCard} onPress={() => {}}>
          <View style={styles.modalHandle} />

          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>המלצות למוצרים</Text>

            <TouchableOpacity onPress={props.onClose} style={styles.iconBtn}>
              <Ionicons name="close" size={20} color={BRAND.TEXT} />
            </TouchableOpacity>
          </View>

          <Text style={styles.modalSubtitle}>
            אפשר להוסיף במהירות מוצרים שמבוססים על הרגלי שימוש ומלאי חסר.
          </Text>

          <View style={styles.searchCard}>
            <Ionicons name="search" size={18} color={BRAND.MUTED} />

            <TextInput
              value={q}
              onChangeText={setQ}
              placeholder="חיפוש בהמלצות..."
              placeholderTextColor={BRAND.MUTED}
              style={styles.searchInput}
              textAlign="right"
            />

            {!!q && (
              <TouchableOpacity onPress={() => setQ("")}>
                <Ionicons name="close-circle" size={18} color={BRAND.MUTED} />
              </TouchableOpacity>
            )}
          </View>

          {filtered.length === 0 ? (
            <View style={styles.emptyCard}>
              <Ionicons name="sparkles-outline" size={22} color={BRAND.MUTED} />
              <Text style={styles.emptyTitle}>אין המלצות זמינות</Text>
              <Text style={styles.emptyText}>
                או שכל ההמלצות כבר נוספו לרשימה.
              </Text>
            </View>
          ) : (
            <FlatList
              data={filtered}
              keyExtractor={(x) => x.id}
              ItemSeparatorComponent={RowSeparator}
              showsVerticalScrollIndicator={false}
              keyboardShouldPersistTaps="handled"
              renderItem={({ item: s }) => (
                <View style={styles.suggestionRow}>
                  <TouchableOpacity
                    onPress={() => props.onAdd(s.name)}
                    style={styles.addMiniBtn}
                  >
                    <Ionicons name="add" size={15} color={BRAND.PRIMARY} />
                    <Text style={styles.addMiniText}>הוסף</Text>
                  </TouchableOpacity>

                  <View style={styles.suggestionTextWrap}>
                    <Text style={styles.suggestionName}>{s.name}</Text>
                    {!!s.reason && (
                      <Text style={styles.suggestionReason}>{s.reason}</Text>
                    )}
                  </View>
                </View>
              )}
            />
          )}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

// ------------------------------
// Add card
// ------------------------------
function QuickAddCard(props: {
  newName: string;
  setNewName: (v: string) => void;
  newQty: string;
  setNewQty: (v: string) => void;
  onAdd: () => void;
}) {
  return (
    <View style={styles.quickAddCard}>
      <Text style={styles.cardTitle}>הוספה לרשימה</Text>
      <Text style={styles.cardSubtitle}>
        הוסיפי מוצר חדש באופן ידני עם כמות רצויה.
      </Text>

      <View style={styles.addRow}>
        <View style={styles.qtyWrap}>
          <Text style={styles.label}>כמות</Text>
          <TextInput
            value={props.newQty}
            onChangeText={props.setNewQty}
            placeholder="1"
            placeholderTextColor={BRAND.MUTED}
            keyboardType="numeric"
            style={styles.input}
            textAlign="right"
          />
        </View>

        <View style={styles.nameWrap}>
          <Text style={styles.label}>שם מוצר</Text>
          <TextInput
            value={props.newName}
            onChangeText={props.setNewName}
            placeholder="לדוגמה: עגבניות"
            placeholderTextColor={BRAND.MUTED}
            style={styles.input}
            textAlign="right"
            onSubmitEditing={props.onAdd}
            returnKeyType="done"
          />
        </View>
      </View>

      <View style={{ marginTop: 14 }}>
        <PrimaryButton title="הוסף לרשימה" onPress={props.onAdd} />
      </View>
    </View>
  );
}

// ------------------------------
// Item row
// ------------------------------
function ShoppingRow(props: {
  item: ShoppingItem;
  mode: Mode;
  picked: boolean;
  onTogglePick: () => void;
  onRemove: () => void;
}) {
  const { item, mode, picked, onTogglePick, onRemove } = props;

  return (
    <View style={[styles.noteRow, picked && mode === "SHOPPING" && { opacity: 0.62 }]}>
      <View style={styles.noteActions}>
        {mode === "SHOPPING" ? (
          <TouchableOpacity
            onPress={onTogglePick}
            style={[styles.checkBtn, picked && styles.checkBtnActive]}
          >
            {picked ? (
              <Ionicons name="checkmark" size={16} color="#fff" />
            ) : null}
          </TouchableOpacity>
        ) : (
          <TouchableOpacity onPress={onRemove} style={styles.noteIconBtn}>
            <Ionicons name="trash-outline" size={16} color={BRAND.DANGER} />
          </TouchableOpacity>
        )}

        {!!item.quantity && (
          <View style={styles.noteQtyPill}>
            <Text style={styles.noteQtyText}>{item.quantity}</Text>
          </View>
        )}
      </View>

      <View style={styles.noteTextWrap}>
        <Text
          style={[
            styles.noteTitle,
            picked && mode === "SHOPPING" && styles.noteTitlePicked,
          ]}
        >
          {item.name}
        </Text>

        <View style={styles.noteMetaRow}>
          {!!item.quantity && <Text style={styles.noteMeta}>יח׳</Text>}
          {!!item.source && mode === "EDIT" && (
            <Text style={styles.noteSource}>{sourceLabel(item.source)}</Text>
          )}
        </View>
      </View>
    </View>
  );
}

// ------------------------------
// Screen
// ------------------------------
export default function ShoppingListScreen() {
  const insets = useSafeAreaInsets();

  const [mode, setMode] = useState<Mode>("EDIT");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [finishing, setFinishing] = useState(false);

  const [items, setItems] = useState<ShoppingItem[]>([]);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [picked, setPicked] = useState<Record<string, boolean>>({});

  const [newName, setNewName] = useState("");
  const [newQty, setNewQty] = useState("");
  const [query, setQuery] = useState("");
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);

  React.useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [list, sugg] = await Promise.all([
          apiGetShoppingList(),
          apiGetSuggestions(),
        ]);
        setItems(list);
        setSuggestions(sugg);
      } catch {
        Alert.alert("שגיאה", "לא הצלחתי לטעון את רשימת הקניות.");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const existingNamesSet = useMemo(() => {
    const set = new Set<string>();
    for (const it of items) {
      set.add(normalizeName(it.name));
    }
    return set;
  }, [items]);

  const filteredItems = useMemo(() => {
    const q = normalizeName(query);
    if (!q) return items;
    return items.filter((it) => normalizeName(it.name).includes(q));
  }, [items, query]);

  const pickedCount = useMemo(
    () => Object.values(picked).filter(Boolean).length,
    [picked]
  );

  function addItem(payload: {
    name: string;
    quantity?: number;
    source?: ShoppingItem["source"];
  }) {
    const name = payload.name.trim();
    if (!name) return;

    const key = normalizeName(name);
    if (existingNamesSet.has(key)) {
      Alert.alert("כבר קיים", "המוצר כבר נמצא ברשימה.");
      return;
    }

    setItems((prev) => [
      {
        id: makeId("item"),
        name,
        quantity: payload.quantity,
        source: payload.source ?? "manual",
      },
      ...prev,
    ]);
  }

  function onAddManual() {
    const name = newName.trim();
    if (!name) return;

    const rawQty = newQty.trim();

    if (rawQty) {
      const parsedQty = Number(rawQty);

      if (Number.isNaN(parsedQty) || parsedQty <= 0) {
        Alert.alert("כמות לא תקינה", "אנא הזיני מספר חיובי.");
        return;
      }

      addItem({
        name,
        quantity: parsedQty,
        source: "manual",
      });
    } else {
      addItem({
        name,
        source: "manual",
      });
    }

    setNewName("");
    setNewQty("");
  }

  function removeItem(id: string) {
    setItems((prev) => prev.filter((x) => x.id !== id));
    setPicked((prev) => {
      if (!prev[id]) return prev;
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
  }

  async function onSyncBaseline() {
    try {
      setSyncing(true);
      const res = await apiSyncBaseline();

      let added = 0;
      const currentNames = new Set(items.map((i) => normalizeName(i.name)));
      const newItems: ShoppingItem[] = [];

      for (const p of res.toAdd) {
        const key = normalizeName(p.name);
        if (currentNames.has(key)) continue;

        currentNames.add(key);
        added++;

        newItems.push({
          id: makeId("item"),
          name: p.name,
          quantity: p.quantity,
          source: "baseline_sync",
        });
      }

      if (newItems.length > 0) {
        setItems((prev) => [...newItems, ...prev]);
      }

      Alert.alert(
        "סנכרון הושלם",
        added > 0
          ? `נוספו ${added} מוצרים לרשימה.`
          : "לא נמצאו מוצרים חדשים להוספה."
      );
    } catch {
      Alert.alert("שגיאה", "הסנכרון נכשל. נסי שוב.");
    } finally {
      setSyncing(false);
    }
  }

  function enterShoppingMode() {
    setMode("SHOPPING");
    setPicked({});
    setSuggestionsOpen(false);
  }

  function exitShoppingMode() {
    setMode("EDIT");
    setPicked({});
  }

  function togglePick(id: string) {
    setPicked((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function finishShopping() {
    const purchasedIds = Object.keys(picked).filter((id) => picked[id]);

    if (purchasedIds.length === 0) {
      Alert.alert("אין סימון", "סמני מוצרים שנקנו ואז לחצי על סיום קנייה.");
      return;
    }

    Alert.alert(
      "סיום קנייה",
      `למחוק ${purchasedIds.length} מוצרים שסומנו?`,
      [
        { text: "ביטול", style: "cancel" },
        {
          text: "מחק",
          style: "destructive",
          onPress: async () => {
            try {
              setFinishing(true);
              await apiCompleteShopping(purchasedIds);
              setItems((prev) =>
                prev.filter((it) => !purchasedIds.includes(it.id))
              );
              setPicked({});
              setMode("EDIT");
            } catch {
              Alert.alert("שגיאה", "לא הצלחתי לסיים קנייה. נסו שוב.");
            } finally {
              setFinishing(false);
            }
          },
        },
      ],
      { cancelable: true }
    );
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <LinearGradient colors={["#E5F3FF", BRAND.BG]} style={StyleSheet.absoluteFill} />
        <ScreenHeader title="רשימת קניות" onBack={() => router.back()} />
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

        <ScreenHeader title="רשימת קניות" onBack={() => router.back()} />

        <SuggestionsModal
          open={suggestionsOpen}
          onClose={() => setSuggestionsOpen(false)}
          suggestions={suggestions}
          existingNamesSet={existingNamesSet}
          onAdd={(name) => addItem({ name, source: "suggestion" })}
        />

        <FlatList
          data={filteredItems}
          keyExtractor={(x) => x.id}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{
            padding: 16,
            paddingBottom: 210 + insets.bottom,
          }}
          ListHeaderComponent={
            <>
              <View style={styles.heroCard}>
                <Text style={styles.heroTitle}>
                  {mode === "EDIT" ? "הקניות של הבית" : "מצב קנייה פעיל"}
                </Text>

                <Text style={styles.heroSubtitle}>
                  {mode === "EDIT"
                    ? "כאן מנהלים את כל המוצרים שצריך לקנות, מוסיפים ידנית, מסנכרנים ומקבלים המלצות."
                    : "סמני מוצרים שנקנו, וכשתסיימי אפשר לנקות אותם מהרשימה."}
                </Text>

                <View style={styles.summaryRow}>
                  <SummaryCard
                    title="פריטים"
                    value={`${items.length}`}
                    icon="list-outline"
                  />
                  <SummaryCard
                    title={mode === "EDIT" ? "המלצות" : "סומנו"}
                    value={mode === "EDIT" ? `${suggestions.length}` : `${pickedCount}`}
                    icon={mode === "EDIT" ? "sparkles-outline" : "checkmark-done-outline"}
                  />
                </View>
              </View>

              <View style={styles.actionsCard}>
                {mode === "EDIT" ? (
                  <View style={styles.actionsWrap}>
                    <TouchableOpacity
                      onPress={enterShoppingMode}
                      style={styles.primaryPillBtn}
                    >
                      <Ionicons name="cart-outline" size={16} color="#fff" />
                      <Text style={styles.primaryPillBtnText}>מצב קנייה</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      onPress={() => setSuggestionsOpen(true)}
                      style={styles.secondaryPillBtn}
                    >
                      <Ionicons
                        name="sparkles-outline"
                        size={16}
                        color={BRAND.TEXT}
                      />
                      <Text style={styles.secondaryPillBtnText}>המלצות</Text>
                    </TouchableOpacity>

                    <TouchableOpacity
                      onPress={onSyncBaseline}
                      disabled={syncing}
                      style={[styles.secondaryPillBtn, syncing && { opacity: 0.7 }]}
                    >
                      {syncing ? (
                        <ActivityIndicator size="small" color={BRAND.PRIMARY} />
                      ) : (
                        <>
                          <Ionicons
                            name="refresh-outline"
                            size={16}
                            color={BRAND.TEXT}
                          />
                          <Text style={styles.secondaryPillBtnText}>סנכרון</Text>
                        </>
                      )}
                    </TouchableOpacity>
                  </View>
                ) : (
                  <View style={styles.actionsWrap}>
                    <TouchableOpacity
                      onPress={finishShopping}
                      disabled={finishing}
                      style={[styles.finishPillBtn, finishing && { opacity: 0.7 }]}
                    >
                      {finishing ? (
                        <ActivityIndicator size="small" color="#fff" />
                      ) : (
                        <>
                          <Ionicons
                            name="checkmark-done-outline"
                            size={16}
                            color="#fff"
                          />
                          <Text style={styles.finishPillBtnText}>סיום קנייה</Text>
                        </>
                      )}
                    </TouchableOpacity>

                    <TouchableOpacity
                      onPress={exitShoppingMode}
                      style={styles.secondaryPillBtn}
                    >
                      <Ionicons name="close-outline" size={16} color={BRAND.TEXT} />
                      <Text style={styles.secondaryPillBtnText}>יציאה</Text>
                    </TouchableOpacity>

                    <View style={styles.modeBadge}>
                      <Text style={styles.modeBadgeText}>
                        {pickedCount}/{items.length}
                      </Text>
                    </View>
                  </View>
                )}
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
                    <Ionicons name="close-circle" size={18} color={BRAND.MUTED} />
                  </TouchableOpacity>
                )}
              </View>

              {mode === "EDIT" ? (
                <QuickAddCard
                  newName={newName}
                  setNewName={setNewName}
                  newQty={newQty}
                  setNewQty={setNewQty}
                  onAdd={onAddManual}
                />
              ) : null}

              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>
                  {mode === "EDIT" ? "פריטים לקנייה" : "הרשימה שלך"}
                </Text>
              </View>
            </>
          }
          renderItem={({ item }) => (
            <View style={styles.notebookCard}>
              <ShoppingRow
                item={item}
                mode={mode}
                picked={!!picked[item.id]}
                onTogglePick={() => togglePick(item.id)}
                onRemove={() => removeItem(item.id)}
              />
            </View>
          )}
          ItemSeparatorComponent={RowSeparator}
          ListEmptyComponent={
            <View style={styles.emptyCard}>
              <Ionicons name="basket-outline" size={24} color={BRAND.MUTED} />
              <Text style={styles.emptyTitle}>אין פריטים להצגה</Text>
              <Text style={styles.emptyText}>
                אפשר להוסיף מוצר חדש או לשנות את החיפוש.
              </Text>
            </View>
          }
        />

        <View style={[styles.bottomBar, { paddingBottom: 10 + insets.bottom }]}>
          <BottomNavBar activeTab="shopping-list" />
        </View>
      </SafeAreaView>
    </KeyboardAvoidingView>
  );
}

// ------------------------------
// Styles
// ------------------------------
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

  heroCard: {
    backgroundColor: "rgba(255,255,255,0.92)",
    borderRadius: 22,
    padding: 15,
    borderWidth: 1,
    borderColor: "#E8ECF3",
    marginBottom: 12,
  },

  heroTitle: {
    fontSize: 18,
    fontWeight: "900",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  heroSubtitle: {
    marginTop: 6,
    color: BRAND.MUTED,
    fontWeight: "700",
    lineHeight: 18,
    fontSize: 12.5,
    textAlign: "right",
  },

  summaryRow: {
    flexDirection: "row-reverse",
    gap: 10,
    marginTop: 12,
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

  actionsCard: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    padding: 12,
    marginBottom: 12,
  },

  actionsWrap: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
    flexWrap: "wrap",
  },

  primaryPillBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: BRAND.PRIMARY,
  },

  primaryPillBtnText: {
    color: "#fff",
    fontWeight: "800",
    fontSize: 12,
  },

  finishPillBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: BRAND.SUCCESS,
  },

  finishPillBtnText: {
    color: "#fff",
    fontWeight: "800",
    fontSize: 12,
  },

  secondaryPillBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 11,
    paddingVertical: 9,
    borderRadius: 999,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
  },

  secondaryPillBtnText: {
    color: BRAND.TEXT,
    fontWeight: "800",
    fontSize: 12,
  },

  modeBadge: {
    paddingHorizontal: 11,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: "#F3F4F6",
  },

  modeBadgeText: {
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 12,
  },

  searchCard: {
    marginBottom: 12,
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

  quickAddCard: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    marginBottom: 14,
  },

  cardTitle: {
    fontSize: 15,
    fontWeight: "900",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  cardSubtitle: {
    marginTop: 4,
    marginBottom: 12,
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 12,
    lineHeight: 18,
    textAlign: "right",
  },

  addRow: {
    flexDirection: "row-reverse",
    gap: 8,
    alignItems: "flex-end",
  },

  qtyWrap: {
    width: 90,
  },

  nameWrap: {
    flex: 1,
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

  sectionHeader: {
    marginBottom: 8,
  },

  sectionTitle: {
    fontSize: 15,
    fontWeight: "900",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  notebookCard: {
    backgroundColor: "rgba(255,255,255,0.97)",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#E8ECF3",
    overflow: "hidden",
  },

  noteRow: {
    minHeight: 58,
    borderBottomWidth: 1,
    borderBottomColor: BRAND.NOTE_LINE,
    paddingRight: 14,
    paddingLeft: 14,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "transparent",
  },

  noteActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },

  noteIconBtn: {
    width: 30,
    height: 30,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F7FAFD",
    borderWidth: 1,
    borderColor: "#E7EDF5",
  },

  checkBtn: {
    width: 28,
    height: 28,
    borderRadius: 9,
    borderWidth: 1.5,
    borderColor: BRAND.PRIMARY,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#fff",
  },

  checkBtnActive: {
    backgroundColor: BRAND.PRIMARY,
    borderColor: BRAND.PRIMARY,
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
    color: BRAND.MUTED,
  },

  noteMetaRow: {
    marginTop: 3,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 8,
  },

  noteMeta: {
    fontSize: 11,
    color: BRAND.MUTED,
    fontWeight: "700",
    textAlign: "right",
  },

  noteSource: {
    fontSize: 11,
    color: BRAND.PRIMARY,
    fontWeight: "800",
    textAlign: "right",
  },

  emptyCard: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 16,
    paddingVertical: 24,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },

  emptyTitle: {
    color: BRAND.TEXT,
    fontWeight: "900",
    fontSize: 14,
  },

  emptyText: {
    color: BRAND.MUTED,
    fontWeight: "700",
    fontSize: 12,
    textAlign: "center",
  },

  bottomBar: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    paddingHorizontal: 10,
    backgroundColor: "rgba(244,244,244,0.96)",
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
    maxHeight: "82%",
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

  suggestionRow: {
    backgroundColor: "rgba(255,255,255,0.96)",
    borderWidth: 1,
    borderColor: BRAND.BORDER,
    borderRadius: 16,
    paddingVertical: 11,
    paddingHorizontal: 12,
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },

  suggestionTextWrap: {
    flex: 1,
    alignItems: "flex-end",
  },

  suggestionName: {
    fontSize: 14,
    fontWeight: "800",
    color: BRAND.TEXT,
    textAlign: "right",
  },

  suggestionReason: {
    marginTop: 2,
    fontSize: 11.5,
    color: BRAND.MUTED,
    fontWeight: "700",
    textAlign: "right",
  },

  addMiniBtn: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: BRAND.PRIMARY_SOFT,
  },

  addMiniText: {
    color: BRAND.PRIMARY,
    fontWeight: "800",
    fontSize: 12,
  },
});