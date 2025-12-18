import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Switch,
  ScrollView,
  Alert,
  TextInput,
  Modal,
  Pressable,
} from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import * as Clipboard from "expo-clipboard";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";

const TEXT = "#111827";
const MUTED = "#6B7280";
const BORDER = "#E5E7EB";
const CARD = "#FFFFFF";
const BRAND_PRIMARY = "#0284C7";

type RowProps = {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  onPress?: () => void;
  danger?: boolean;
};

function SettingsRow({ icon, title, subtitle, right, onPress, danger }: RowProps) {
  const content = (
    <View style={styles.row}>
      <View style={[styles.rowIcon, danger && styles.rowIconDanger]}>
        <Ionicons name={icon} size={18} color={danger ? "#B91C1C" : BRAND_PRIMARY} />
      </View>

      <View style={styles.rowText}>
        <Text style={[styles.rowTitle, danger && { color: "#B91C1C" }]}>{title}</Text>
        {!!subtitle && <Text style={styles.rowSubtitle}>{subtitle}</Text>}
      </View>

      <View style={styles.rowRight}>
        {right ?? <Ionicons name="chevron-back" size={18} color={MUTED} />}
      </View>
    </View>
  );

  if (!onPress) return <View style={styles.rowWrap}>{content}</View>;

  return (
    <TouchableOpacity style={styles.rowWrap} onPress={onPress} activeOpacity={0.85}>
      {content}
    </TouchableOpacity>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <View style={styles.sectionCard}>{children}</View>
    </View>
  );
}

const Divider = () => <View style={styles.divider} />;

export default function SettingsScreen() {
  // demo flags
  const isHomeCreator = true;
  const homeInviteCode = "A7K9-3Q";

  // preferences
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [expiryAlertsEnabled, setExpiryAlertsEnabled] = useState(true);
  const [expiryLeadDays, setExpiryLeadDays] = useState<number>(3);

  // modals
  const [daysModalOpen, setDaysModalOpen] = useState(false);
  const [homeCodeOpen, setHomeCodeOpen] = useState(false);

  const clampDays = (n: number) => Math.max(0, Math.min(30, n));

  const updateDaysFromText = (text: string) => {
    const cleaned = text.replace(/[^\d]/g, "");
    if (cleaned === "") return;
    const num = clampDays(parseInt(cleaned, 10));
    if (Number.isFinite(num)) setExpiryLeadDays(num);
  };

  const handleBack = () => {
    if (router.canGoBack?.()) router.back();
    else router.replace("/home/home");
  };

  const confirmLogout = () => {
    Alert.alert("התנתקות", "לצאת מהחשבון?", [
      { text: "ביטול", style: "cancel" },
      {
        text: "התנתק",
        style: "destructive",
        onPress: () => router.replace("/login"),
      },
    ]);
  };

  const leadDaysSubtitle =
    expiryLeadDays === 0
      ? "התראה ביום פג התוקף בלבד"
      : `התראה ${expiryLeadDays} ימים לפני פג התוקף`;

  return (
    <SafeAreaView style={styles.safeArea} edges={["top"]}>
      <LinearGradient
        colors={["#F4F4F4", "#D7F0FF"]}
        start={{ x: 0.5, y: 0.2 }}
        end={{ x: 0.5, y: 0 }}
        style={styles.gradientBackground}
        pointerEvents="none"
      />

      <View style={styles.main}>
        <ScreenHeader title="הגדרות" onBack={handleBack} />

        <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
          <Section title="חשבון">
            <SettingsRow
              icon="person-outline"
              title="פרופיל"
              subtitle="שם, אימייל וסיסמה"
              onPress={() => router.push("/settings")}
            />
            <Divider />
            <SettingsRow
              icon="people-outline"
              title="ניהול בתים"
              subtitle="חברים, הרשאות והזמנות"
              onPress={() => router.push("/home/home")}
            />
          </Section>

          <Section title="התראות">
            <SettingsRow
              icon="notifications-outline"
              title="התראות כלליות"
              subtitle="התראות מערכת ועדכונים"
              right={<Switch value={notificationsEnabled} onValueChange={setNotificationsEnabled} />}
            />
            <Divider />
            <SettingsRow
              icon="time-outline"
              title="התראות תוקף"
              subtitle="התראה כשמוצר קרוב לפג תוקף"
              right={
                <Switch
                  value={expiryAlertsEnabled}
                  onValueChange={setExpiryAlertsEnabled}
                  disabled={!notificationsEnabled}
                />
              }
            />
            <Divider />
            <SettingsRow
              icon="calendar-outline"
              title="התראה לפני פג תוקף"
              subtitle={expiryLeadDays === 0 ? "ביום פג התוקף" : `${expiryLeadDays} ימים מראש`}
              onPress={() => {
                // אם ההתראות כבויות — לא נפתח
                if (!notificationsEnabled || !expiryAlertsEnabled) return;
                setDaysModalOpen(true);
              }}
            />
          </Section>

          {isHomeCreator && (
            <Section title="בית">
              <SettingsRow
                icon="key-outline"
                title="קוד הבית"
                subtitle="הצגת קוד להצטרפות לבית"
                onPress={() => setHomeCodeOpen(true)}
              />
            </Section>
          )}

          <TouchableOpacity style={styles.logoutBtn} onPress={confirmLogout} activeOpacity={0.85}>
            <Ionicons name="log-out-outline" size={18} color="#B91C1C" />
            <Text style={styles.logoutText}>התנתקות</Text>
          </TouchableOpacity>

          <View style={{ height: 24 }} />
        </ScrollView>

        <BottomNavBar activeTab="settings" />
      </View>

      {/* ───────────── Modal: Lead days ───────────── */}
      <Modal
        visible={daysModalOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setDaysModalOpen(false)}
      >
        <View style={styles.modalRoot}>
          <Pressable style={styles.modalBackdrop} onPress={() => setDaysModalOpen(false)} />
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>התראה לפני פג תוקף</Text>
            <Text style={styles.modalSubtitle}>{leadDaysSubtitle}</Text>

            <View style={styles.modalControls}>
              <TouchableOpacity
                style={styles.stepBtn}
                activeOpacity={0.85}
                onPress={() => setExpiryLeadDays((d) => clampDays(d - 1))}
              >
                <Ionicons name="remove" size={18} color={TEXT} />
              </TouchableOpacity>

              <TextInput
                value={String(expiryLeadDays)}
                onChangeText={updateDaysFromText}
                keyboardType="number-pad"
                style={styles.daysInput}
                textAlign="center"
                maxLength={2}
              />

              <TouchableOpacity
                style={styles.stepBtn}
                activeOpacity={0.85}
                onPress={() => setExpiryLeadDays((d) => clampDays(d + 1))}
              >
                <Ionicons name="add" size={18} color={TEXT} />
              </TouchableOpacity>
            </View>

            <Text style={styles.hintText}>ניתן לבחור בין 0 ל־30 ימים. (0 = רק ביום התוקף)</Text>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.secondaryBtn}
                activeOpacity={0.85}
                onPress={() => setDaysModalOpen(false)}
              >
                <Text style={styles.secondaryBtnText}>סגירה</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.primaryBtn}
                activeOpacity={0.85}
                onPress={() => {
                  Alert.alert("עודכן", "ההגדרות נשמרו (דמו).");
                  setDaysModalOpen(false);
                }}
              >
                <Text style={styles.primaryBtnText}>שמירה</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* ───────────── Modal: Home code ───────────── */}
      <Modal
        visible={homeCodeOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setHomeCodeOpen(false)}
      >
        <View style={styles.modalRoot}>
          <Pressable style={styles.modalBackdrop} onPress={() => setHomeCodeOpen(false)} />
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>קוד הבית</Text>
            <Text style={styles.modalSubtitle}>
              שתפי את הקוד כדי שמשתמשים נוספים יוכלו להצטרף לבית.
            </Text>

            <View style={styles.codeBox}>
              <Text style={styles.codeText}>{homeInviteCode}</Text>
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.secondaryBtn}
                activeOpacity={0.85}
                onPress={() => setHomeCodeOpen(false)}
              >
                <Text style={styles.secondaryBtnText}>סגירה</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.primaryBtn}
                activeOpacity={0.85}
                onPress={async () => {
                  await Clipboard.setStringAsync(homeInviteCode);
                  Alert.alert("הועתק", "קוד הבית הועתק ללוח.");
                }}
              >
                <Text style={styles.primaryBtnText}>העתקה</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F4F4F4" },
  gradientBackground: { ...StyleSheet.absoluteFillObject },
  main: { flex: 1 },

  container: {
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 24,
    gap: 14,
  },

  section: { gap: 8 },
  sectionTitle: {
    fontSize: 12,
    fontWeight: "800",
    color: MUTED,
    textAlign: "right",
    paddingHorizontal: 2,
  },
  sectionCard: {
    backgroundColor: CARD,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: BORDER,
    overflow: "hidden",
  },

  rowWrap: { paddingHorizontal: 12, paddingVertical: 12 },
  row: { flexDirection: "row-reverse", alignItems: "center", gap: 10 },

  rowIcon: {
    width: 34,
    height: 34,
    borderRadius: 12,
    backgroundColor: "rgba(2,132,199,0.10)",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(2,132,199,0.14)",
  },
  rowIconDanger: {
    backgroundColor: "rgba(185,28,28,0.08)",
    borderColor: "rgba(185,28,28,0.18)",
  },

  rowText: { flex: 1, gap: 3 },
  rowTitle: { fontSize: 14, fontWeight: "900", color: TEXT, textAlign: "right" },
  rowSubtitle: { fontSize: 12, color: MUTED, textAlign: "right", lineHeight: 16 },

  rowRight: { alignItems: "center", justifyContent: "center" },
  divider: { height: 1, backgroundColor: BORDER, marginHorizontal: 12 },

  logoutBtn: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 16,
    paddingVertical: 12,
    paddingHorizontal: 14,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  logoutText: { color: "#B91C1C", fontWeight: "900", fontSize: 14 },

  /* modal */
  modalRoot: { flex: 1, justifyContent: "center", paddingHorizontal: 16 },
  modalBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(17,24,39,0.40)",
  },
  modalCard: {
    backgroundColor: "white",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: BORDER,
    padding: 16,
  },
  modalTitle: { fontSize: 16, fontWeight: "900", color: TEXT, textAlign: "right" },
  modalSubtitle: {
    marginTop: 6,
    fontSize: 12,
    color: MUTED,
    textAlign: "right",
    lineHeight: 16,
  },
  modalControls: {
    marginTop: 14,
    flexDirection: "row-reverse",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
  },
  stepBtn: {
    width: 34,
    height: 34,
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: BORDER,
    alignItems: "center",
    justifyContent: "center",
  },
  daysInput: {
    width: 44,
    height: 34,
    borderRadius: 12,
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: BORDER,
    fontSize: 14,
    fontWeight: "900",
    color: TEXT,
    paddingVertical: 0,
  },
  hintText: {
    marginTop: 10,
    fontSize: 11,
    color: MUTED,
    textAlign: "right",
    lineHeight: 16,
  },
  modalActions: {
    marginTop: 16,
    flexDirection: "row-reverse",
    gap: 10,
    justifyContent: "flex-start",
  },
  secondaryBtn: {
    backgroundColor: "white",
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: BORDER,
    minWidth: 120,
    alignItems: "center",
    justifyContent: "center",
  },
  secondaryBtnText: { color: TEXT, fontWeight: "900", fontSize: 14 },
  primaryBtn: {
    backgroundColor: BRAND_PRIMARY,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 14,
    minWidth: 120,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryBtnText: { color: "white", fontWeight: "900", fontSize: 14 },

  codeBox: {
    marginTop: 14,
    borderWidth: 1,
    borderColor: BORDER,
    backgroundColor: "#F9FAFB",
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  codeText: {
    fontSize: 22,
    fontWeight: "900",
    letterSpacing: 2,
    color: TEXT,
  },
});
