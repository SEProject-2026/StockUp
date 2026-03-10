import React from "react";
import { View, Text, StyleSheet, Switch, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { router, useLocalSearchParams } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import * as Clipboard from "expo-clipboard";

import ScreenHeader from "@/src/layout/ScreenHeader";
import BottomNavBar from "@/src/layout/BottomNavBar";
import { useHomeSettings } from "@/src/hooks/useHomeSettings";
import { Section, SettingsRow, Divider } from "@/src/components/settings/SettingsUI";
import { 
  ExpiryDaysModal, HomeCodeModal, JoinRequestsModal, 
  SwitchHeadModal, ManageMembersModal 
} from "@/src/components/settings/SettingsModals";

import { getHomeJoinCode, getJoinRequests } from "@/src/api/homes";

export default function SettingsScreen() {
  const { homeId } = useLocalSearchParams<{ homeId?: string }>();
  const { state, actions } = useHomeSettings(homeId);


  const handleOpenCode = async () => {
    actions.setHomeCodeOpen(true);
    actions.setLoadingHomeCode(true);
    try {
      const res = await getHomeJoinCode(homeId!);
      actions.setHomeInviteCode(res.data?.join_code || "");
    } catch (e) { Alert.alert("שגיאה", "טעינת קוד נכשלה"); }
    finally { actions.setLoadingHomeCode(false); }
  };

  const handleOpenJoinRequests = async () => {
    actions.setJoinRequestsOpen(true);
    actions.setLoadingJoinRequests(true);
    try {
      const res = await getJoinRequests(homeId!);
      const requests = Object.entries(res.data || {}).map(([id, name]) => ({ user_id: id, name }));
      actions.setJoinRequests(requests);
    } catch (e) { Alert.alert("שגיאה", "טעינת בקשות נכשלה"); }
    finally { actions.setLoadingJoinRequests(false); }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={["top"]}>
      <LinearGradient colors={["#F4F4F4", "#D7F0FF"]} start={{ x: 0.5, y: 0.2 }} end={{ x: 0.5, y: 0 }} style={styles.gradientBackground} />
      
      <View style={styles.main}>
        <ScreenHeader title="הגדרות" onBack={() => router.replace("/home/home")} />
        
        <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
          <Section title="התראות">
            <SettingsRow icon="notifications-outline" title="התראות כלליות" subtitle="התראות מערכת ועדכונים" right={<Switch value={state.notificationsEnabled} onValueChange={actions.setNotificationsEnabled} trackColor={{ true: "#0284C7" }} />} />
            <Divider />
            <SettingsRow icon="calendar-outline" title="התראה לפני פג תוקף" subtitle={state.expiryLeadDays === 0 ? "ביום פג התוקף" : `${state.expiryLeadDays} ימים מראש`} onPress={() => actions.setDaysModalOpen(true)} />
          </Section>

          <Section title="בית">
            <SettingsRow icon="arrow-undo-outline" title="חזרה לבתים" onPress={() => router.replace("/home/home")} />
            <Divider />
            <SettingsRow icon="exit-outline" title="עזיבת בית" danger onPress={actions.handleLeaveHome} />
          </Section>

          {state.isHomeAdmin && (
            <Section title="הרשאות מנהל">
              <SettingsRow icon="key-outline" title="קוד הבית" onPress={handleOpenCode} />
              <Divider />
              <SettingsRow icon="mail-open-outline" title="בקשות הצטרפות" onPress={handleOpenJoinRequests} />
              <Divider />
              <SettingsRow icon="swap-horizontal-outline" title="החלפת מנהל בית" onPress={() => actions.setSwitchHeadOpen(true)} />
              <Divider />
              <SettingsRow icon="people-circle-outline" title="ניהול משתתפים" onPress={() => actions.setMembersOpen(true)} />
              <Divider />
              <SettingsRow icon="trash-outline" title="מחיקת בית" danger onPress={actions.handleDeleteHome} />
            </Section>
          )}

          <TouchableOpacity style={styles.logoutBtn} onPress={() => router.replace("/login")}>
            <Ionicons name="log-out-outline" size={18} color="#B91C1C" />
            <Text style={styles.logoutText}>התנתקות מהמערכת</Text>
          </TouchableOpacity>
        </ScrollView>
        <BottomNavBar activeTab="settings" />
      </View>

      <ExpiryDaysModal visible={state.daysModalOpen} onClose={() => actions.setDaysModalOpen(false)} days={state.expiryLeadDays} setDays={actions.setExpiryLeadDays} onSave={actions.handleSaveExpiration} loading={state.savingDays} clamp={actions.clampDays} />
      <HomeCodeModal visible={state.homeCodeOpen} onClose={() => actions.setHomeCodeOpen(false)} code={state.homeInviteCode} loading={state.loadingHomeCode} onCopy={() => { Clipboard.setStringAsync(state.homeInviteCode); Alert.alert("הועתק"); }} />
      <JoinRequestsModal visible={state.joinRequestsOpen} onClose={() => actions.setJoinRequestsOpen(false)} requests={state.joinRequests} loading={state.loadingJoinRequests} onAnswer={actions.handleAnswerJoinRequest} processingId={state.processingRequestId} />
      <SwitchHeadModal visible={state.switchHeadOpen} onClose={() => actions.setSwitchHeadOpen(false)} members={state.homeMembers} currentAdminId={state.homeMeta?.admin_id} onSwitch={actions.handleSwitchHead} />
      <ManageMembersModal visible={state.membersOpen} onClose={() => actions.setMembersOpen(false)} members={state.homeMembers} currentAdminId={state.homeMeta?.admin_id} onRemove={actions.handleRemoveMember} removingId={state.removingMemberId} />

      {(state.leavingHomeLoading || state.deletingHomeLoading) && <View style={styles.overlay}><ActivityIndicator size="large" color="white" /></View>}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#F4F4F4" },
  gradientBackground: { ...StyleSheet.absoluteFillObject },
  main: { flex: 1 },
  container: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 24, gap: 14 },
  logoutBtn: { backgroundColor: "#FFFFFF", borderWidth: 1, borderColor: "#E5E7EB", borderRadius: 16, paddingVertical: 14, flexDirection: "row-reverse", alignItems: "center", justifyContent: "center", gap: 8, marginTop: 10 },
  logoutText: { color: "#B91C1C", fontWeight: "900", fontSize: 14 },
  overlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' }
});