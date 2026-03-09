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
  ActivityIndicator,
} from "react-native";

import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import * as Clipboard from "expo-clipboard";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";
import {
  getHomeJoinCode,
  updateExpirationRange,
  getMyHomes,
  answerJoinRequest,
} from "@/src/api/homes";

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

type JoinRequestItem = {
  user_id: string;
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
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  const currentHomeId = homeId ? String(homeId) : undefined;

  const isHomeCreator = true;

  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [expiryAlertsEnabled, setExpiryAlertsEnabled] = useState(true);
  const [expiryLeadDays, setExpiryLeadDays] = useState<number>(3);

  const [daysModalOpen, setDaysModalOpen] = useState(false);
  const [homeCodeOpen, setHomeCodeOpen] = useState(false);
  const [joinRequestsOpen, setJoinRequestsOpen] = useState(false);

  const [homeInviteCode, setHomeInviteCode] = useState("");
  const [loadingHomeCode, setLoadingHomeCode] = useState(false);
  const [savingDays, setSavingDays] = useState(false);

  const [joinRequests, setJoinRequests] = useState<JoinRequestItem[]>([]);
  const [loadingJoinRequests, setLoadingJoinRequests] = useState(false);
  const [processingRequestId, setProcessingRequestId] = useState<string | null>(null);

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

  const openHomeCodeModal = async () => {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "לא נמצא מזהה בית.");
      return;
    }

    try {
      setLoadingHomeCode(true);
      setHomeCodeOpen(true);

      const res = await getHomeJoinCode(currentHomeId);
      const code = res.data?.join_code;

      if (!code) {
        throw new Error(res.message || "לא התקבל קוד בית");
      }

      setHomeInviteCode(code);
    } catch (e: any) {
      setHomeCodeOpen(false);
      Alert.alert("שגיאה", e?.message ?? "לא הצלחתי להביא את קוד הבית.");
    } finally {
      setLoadingHomeCode(false);
    }
  };

  const openJoinRequestsModal = async () => {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "לא נמצא מזהה בית.");
      return;
    }

    try {
      setLoadingJoinRequests(true);
      setJoinRequestsOpen(true);

      const res = await getMyHomes();

      const currentHome = Array.isArray(res.data)
        ? res.data.find((home: any) => String(home.id) === String(currentHomeId))
        : null;

      const joinRequests = Array.isArray(currentHome?.join_requests)
        ? currentHome.join_requests
        : [];

      const requests: JoinRequestItem[] = joinRequests.map((id: string) => ({
        user_id: String(id),
      }));

      setJoinRequests(requests);
    } catch (e: any) {
      setJoinRequestsOpen(false);
      Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לטעון את בקשות ההצטרפות.");
    } finally {
      setLoadingJoinRequests(false);
    }
  };

  const handleAnswerJoinRequest = async (userId: string, approved: boolean) => {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "לא נמצא מזהה בית.");
      return;
    }

    try {
      setProcessingRequestId(userId);

      await answerJoinRequest(currentHomeId, {
        user_id: userId,
        approved,
      });

      setJoinRequests((prev) => prev.filter((item) => item.user_id !== userId));

      Alert.alert("בוצע", approved ? "הבקשה אושרה בהצלחה." : "הבקשה נדחתה.");
    } catch (e: any) {
      Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לעדכן את הבקשה.");
    } finally {
      setProcessingRequestId(null);
    }
  };

  const saveExpirationRange = async () => {
    if (!currentHomeId) {
      Alert.alert("שגיאה", "לא נמצא מזהה בית.");
      return;
    }

    try {
      setSavingDays(true);
      await updateExpirationRange(currentHomeId, { new_range: expiryLeadDays });
      Alert.alert("עודכן", "טווח ההתראה נשמר בהצלחה.");
      setDaysModalOpen(false);
    } catch (e: any) {
      Alert.alert("שגיאה", e?.message ?? "לא הצלחתי לעדכן את טווח ההתראה.");
    } finally {
      setSavingDays(false);
    }
  };

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
                onPress={openHomeCodeModal}
              />
              <Divider />
              <SettingsRow
                icon="mail-open-outline"
                title="בקשות הצטרפות"
                subtitle="צפייה ואישור בקשות להצטרפות לבית"
                onPress={openJoinRequestsModal}
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
                style={[styles.primaryBtn, savingDays && styles.disabledBtn]}
                activeOpacity={0.85}
                onPress={saveExpirationRange}
                disabled={savingDays}
              >
                <Text style={styles.primaryBtnText}>
                  {savingDays ? "שומר..." : "שמירה"}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

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
              {loadingHomeCode ? (
                <ActivityIndicator size="small" color={BRAND_PRIMARY} />
              ) : (
                <Text style={styles.codeText}>{homeInviteCode || "—"}</Text>
              )}
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
                style={[
                  styles.primaryBtn,
                  (!homeInviteCode || loadingHomeCode) && styles.disabledBtn,
                ]}
                activeOpacity={0.85}
                disabled={!homeInviteCode || loadingHomeCode}
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

      <Modal
        visible={joinRequestsOpen}
        transparent
        animationType="fade"
        onRequestClose={() => setJoinRequestsOpen(false)}
      >
        <View style={styles.modalRoot}>
          <Pressable style={styles.modalBackdrop} onPress={() => setJoinRequestsOpen(false)} />
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>בקשות הצטרפות</Text>
            <Text style={styles.modalSubtitle}>
              כאן אפשר לצפות בבקשות ולאשר או לדחות אותן.
            </Text>

            <View style={styles.requestsContainer}>
              {loadingJoinRequests ? (
                <View style={styles.requestsLoading}>
                  <ActivityIndicator size="small" color={BRAND_PRIMARY} />
                </View>
              ) : joinRequests.length === 0 ? (
                <Text style={styles.emptyRequestsText}>אין כרגע בקשות הצטרפות.</Text>
              ) : (
                joinRequests.map((request) => {
                  const isProcessing = processingRequestId === request.user_id;

                  return (
                    <View key={request.user_id} style={styles.requestCard}>
                      <View style={styles.requestHeader}>
                        <View style={styles.requestAvatar}>
                          <Ionicons name="person-outline" size={16} color={BRAND_PRIMARY} />
                        </View>

                        <View style={styles.requestTextWrap}>
                          <Text style={styles.requestName}>בקשת הצטרפות</Text>
                          <Text style={styles.requestId} numberOfLines={1}>
                            {request.user_id}
                          </Text>
                        </View>
                      </View>

                      <View style={styles.requestActions}>
                        <TouchableOpacity
                          style={[styles.rejectBtn, isProcessing && styles.disabledBtn]}
                          activeOpacity={0.85}
                          disabled={isProcessing}
                          onPress={() => handleAnswerJoinRequest(request.user_id, false)}
                        >
                          <Text style={styles.rejectBtnText}>דחייה</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                          style={[styles.approveBtn, isProcessing && styles.disabledBtn]}
                          activeOpacity={0.85}
                          disabled={isProcessing}
                          onPress={() => handleAnswerJoinRequest(request.user_id, true)}
                        >
                          <Text style={styles.approveBtnText}>
                            {isProcessing ? "מעבד..." : "אישור"}
                          </Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                  );
                })
              )}
            </View>

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.secondaryBtn}
                activeOpacity={0.85}
                onPress={() => setJoinRequestsOpen(false)}
              >
                <Text style={styles.secondaryBtnText}>סגירה</Text>
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
  disabledBtn: {
    opacity: 0.6,
  },

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
    minHeight: 62,
  },
  codeText: {
    fontSize: 22,
    fontWeight: "900",
    letterSpacing: 2,
    color: TEXT,
  },

  requestsContainer: {
    marginTop: 14,
    gap: 10,
  },
  requestsLoading: {
    paddingVertical: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyRequestsText: {
    fontSize: 13,
    color: MUTED,
    textAlign: "right",
    paddingVertical: 8,
  },
  requestCard: {
    borderWidth: 1,
    borderColor: BORDER,
    borderRadius: 14,
    backgroundColor: "#F9FAFB",
    padding: 12,
    gap: 12,
  },
  requestHeader: {
    flexDirection: "row-reverse",
    alignItems: "center",
    gap: 10,
  },
  requestAvatar: {
    width: 34,
    height: 34,
    borderRadius: 12,
    backgroundColor: "rgba(2,132,199,0.10)",
    alignItems: "center",
    justifyContent: "center",
  },
  requestTextWrap: {
    flex: 1,
    gap: 2,
  },
  requestName: {
    fontSize: 14,
    fontWeight: "900",
    color: TEXT,
    textAlign: "right",
  },
  requestId: {
    fontSize: 11,
    color: MUTED,
    textAlign: "right",
  },
  requestActions: {
    flexDirection: "row-reverse",
    gap: 8,
  },
  approveBtn: {
    flex: 1,
    backgroundColor: "#16A34A",
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  approveBtnText: {
    color: "white",
    fontWeight: "900",
    fontSize: 13,
  },
  rejectBtn: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#FCA5A5",
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
  },
  rejectBtnText: {
    color: "#B91C1C",
    fontWeight: "900",
    fontSize: 13,
  },
});