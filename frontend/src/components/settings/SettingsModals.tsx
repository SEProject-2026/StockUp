import React from "react";
import { View, Text, StyleSheet, Modal, Pressable, TouchableOpacity, TextInput, ActivityIndicator, ScrollView } from "react-native";
import { Ionicons } from "@expo/vector-icons";

const BRAND_PRIMARY = "#0284C7";
const BORDER = "#E5E7EB";
const TEXT = "#111827";
const MUTED = "#6B7280";

export const ExpiryDaysModal = ({ visible, onClose, days, setDays, onSave, loading, clamp }: any) => (
  <Modal visible={visible} transparent animationType="fade">
    <View style={styles.modalRoot}>
      <Pressable style={styles.modalBackdrop} onPress={onClose} />
      <View style={styles.modalCard}>
        <Text style={styles.modalTitle}>התראה לפני פג תוקף</Text>
        <Text style={styles.modalSub}>בחר כמה ימים מראש תרצה לקבל התראה</Text>
        <View style={styles.modalControls}>
          <TouchableOpacity style={styles.stepBtn} onPress={() => setDays(clamp(days - 1))}><Ionicons name="remove" size={20} color={TEXT}/></TouchableOpacity>
          <TextInput value={String(days)} keyboardType="number-pad" style={styles.daysInput} textAlign="center" onChangeText={(v) => setDays(clamp(parseInt(v) || 0))} />
          <TouchableOpacity style={styles.stepBtn} onPress={() => setDays(clamp(days + 1))}><Ionicons name="add" size={20} color={TEXT}/></TouchableOpacity>
        </View>
        <View style={styles.modalActions}>
          <TouchableOpacity style={styles.secondaryBtn} onPress={onClose}><Text style={styles.btnText}>ביטול</Text></TouchableOpacity>
          <TouchableOpacity style={styles.primaryBtn} onPress={onSave} disabled={loading}>
             {loading ? <ActivityIndicator size="small" color="white" /> : <Text style={styles.primaryBtnText}>שמירה</Text>}
          </TouchableOpacity>
        </View>
      </View>
    </View>
  </Modal>
);

export const HomeCodeModal = ({ visible, onClose, code, loading, onCopy }: any) => (
  <Modal visible={visible} transparent animationType="fade">
    <View style={styles.modalRoot}>
      <Pressable style={styles.modalBackdrop} onPress={onClose} />
      <View style={styles.modalCard}>
        <View style={styles.modalHeader}>
           <Text style={styles.modalTitle}>קוד הצטרפות לבית</Text>
           <TouchableOpacity onPress={onClose}><Ionicons name="close" size={20} color={MUTED}/></TouchableOpacity>
        </View>
        <View style={styles.codeContainer}>
          {loading ? <ActivityIndicator color={BRAND_PRIMARY} /> : (
            <>
              <Text style={styles.codeText}>{code}</Text>
              <TouchableOpacity style={styles.copyBtn} onPress={onCopy}><Ionicons name="copy-outline" size={20} color={BRAND_PRIMARY}/></TouchableOpacity>
            </>
          )}
        </View>
        <Text style={styles.codeHint}>שתף את הקוד עם בני הבית כדי שיוכלו להצטרף</Text>
      </View>
    </View>
  </Modal>
);

export const JoinRequestsModal = ({ visible, onClose, requests, loading, onAnswer, processingId }: any) => (
  <Modal visible={visible} transparent animationType="slide">
    <View style={styles.modalRoot}>
      <Pressable style={styles.modalBackdrop} onPress={onClose} />
      <View style={[styles.modalCard, { maxHeight: '80%', paddingBottom: 24 }]}>
        <View style={styles.modalHeader}>
           <Text style={styles.modalTitle}>בקשות הצטרפות ({requests.length})</Text>
           <TouchableOpacity onPress={onClose}><Ionicons name="close" size={20} color={MUTED}/></TouchableOpacity>
        </View>
        <ScrollView showsVerticalScrollIndicator={false} style={{ marginTop: 15 }}>
          {loading ? <ActivityIndicator color={BRAND_PRIMARY} style={{ margin: 20 }} /> : requests.length === 0 ? 
            <View style={{ alignItems: 'center', padding: 30 }}><Ionicons name="mail-outline" size={40} color={BORDER} /><Text style={{color:MUTED, marginTop: 10}}>אין בקשות חדשות</Text></View> : 
            requests.map((req: any) => (
              <View key={req.user_id} style={styles.requestItem}>
                <View style={styles.requestRow}>
                  <View style={styles.requestAvatar}><Ionicons name="person" size={16} color={BRAND_PRIMARY} /></View>
                  <View style={styles.requestTextWrap}><Text style={styles.requestName}>{req.name}</Text></View>
                </View>
                <View style={styles.requestActions}>
                  <TouchableOpacity style={styles.approveBtn} onPress={() => onAnswer(req.user_id, true)} disabled={!!processingId}>
                    {processingId === req.user_id ? <ActivityIndicator size="small" color="white" /> : <Text style={styles.approveBtnText}>אשר</Text>}
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.rejectBtn} onPress={() => onAnswer(req.user_id, false)} disabled={!!processingId}>
                    <Text style={styles.rejectBtnText}>דחה</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))
          }
        </ScrollView>
      </View>
    </View>
  </Modal>
);

export const SwitchHeadModal = ({ visible, onClose, members, onSwitch, currentAdminId }: any) => (
  <Modal visible={visible} transparent animationType="slide">
    <View style={styles.modalRoot}>
      <Pressable style={styles.modalBackdrop} onPress={onClose} />
      <View style={styles.modalCard}>
        <View style={styles.modalHeader}>
           <Text style={styles.modalTitle}>החלפת מנהל בית</Text>
           <TouchableOpacity onPress={onClose}><Ionicons name="close" size={20} color={MUTED}/></TouchableOpacity>
        </View>
        <Text style={styles.modalSub}>בחר משתמש שיהפוך למנהל הבית החדש</Text>
        <ScrollView style={{ marginTop: 10 }} showsVerticalScrollIndicator={false}>
          {members.filter((m: any) => String(m.user_id) !== String(currentAdminId)).map((m: any) => (
            <TouchableOpacity key={m.user_id} style={styles.memberSelectItem} onPress={() => onSwitch(m.user_id, m.name)}>
              <View style={styles.requestRow}>
                <View style={styles.requestAvatar}><Ionicons name="swap-horizontal" size={16} color={BRAND_PRIMARY} /></View>
                <Text style={styles.requestName}>{m.name}</Text>
              </View>
              <Ionicons name="chevron-back" size={18} color={MUTED} />
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </View>
  </Modal>
);

// 5. מודאל ניהול משתתפים
export const ManageMembersModal = ({ visible, onClose, members, onRemove, removingId, currentAdminId }: any) => (
  <Modal visible={visible} transparent animationType="slide">
    <View style={styles.modalRoot}>
      <Pressable style={styles.modalBackdrop} onPress={onClose} />
      <View style={styles.modalCard}>
        <View style={styles.modalHeader}>
           <Text style={styles.modalTitle}>ניהול משתתפים</Text>
           <TouchableOpacity onPress={onClose}><Ionicons name="close" size={20} color={MUTED}/></TouchableOpacity>
        </View>
        <ScrollView style={{ marginTop: 10 }} showsVerticalScrollIndicator={false}>
          {members.map((m: any) => (
            <View key={m.user_id} style={styles.memberSelectItem}>
              <View style={styles.requestRow}>
                <View style={styles.requestAvatar}><Ionicons name="person" size={16} color={BRAND_PRIMARY} /></View>
                <Text style={styles.requestName}>{m.name} {String(m.user_id) === String(currentAdminId) ? "(מנהל)" : ""}</Text>
              </View>
              {String(m.user_id) !== String(currentAdminId) && (
                <TouchableOpacity onPress={() => onRemove(m.user_id, m.name)} style={styles.deleteAction}>
                  {removingId === m.user_id ? <ActivityIndicator size="small" color="#B91C1C" /> : <Ionicons name="trash-outline" size={20} color="#B91C1C" />}
                </TouchableOpacity>
              )}
            </View>
          ))}
        </ScrollView>
      </View>
    </View>
  </Modal>
);

const styles = StyleSheet.create({
  modalRoot: { flex: 1, justifyContent: "center", paddingHorizontal: 20 },
  modalBackdrop: { ...StyleSheet.absoluteFillObject, backgroundColor: "rgba(17,24,39,0.60)" },
  modalCard: { backgroundColor: "white", borderRadius: 24, padding: 20, shadowColor: "#000", shadowOpacity: 0.15, shadowRadius: 10, elevation: 10 },
  modalHeader: { flexDirection: 'row-reverse', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 },
  modalTitle: { fontSize: 18, fontWeight: "900", textAlign: "right", color: TEXT },
  modalSub: { fontSize: 13, color: MUTED, textAlign: "right", marginBottom: 10 },
  modalControls: { flexDirection: "row-reverse", alignItems: "center", justifyContent: "center", gap: 15, marginVertical: 20 },
  stepBtn: { width: 42, height: 42, borderRadius: 14, backgroundColor: "#F9FAFB", borderWidth: 1, borderColor: BORDER, alignItems: "center", justifyContent: "center" },
  daysInput: { width: 60, height: 42, borderRadius: 14, backgroundColor: "#F3F4F6", borderWidth: 1, borderColor: BORDER, fontSize: 18, fontWeight: "900", color: TEXT },
  modalActions: { flexDirection: "row-reverse", gap: 12 },
  primaryBtn: { backgroundColor: BRAND_PRIMARY, paddingVertical: 14, borderRadius: 16, flex: 1, alignItems: 'center', justifyContent: 'center' },
  primaryBtnText: { color: 'white', fontWeight: "900", fontSize: 15 },
  secondaryBtn: { borderWidth: 1, borderColor: BORDER, paddingVertical: 14, borderRadius: 16, flex: 1, alignItems: 'center' },
  btnText: { fontWeight: "800", color: TEXT },
  codeContainer: { flexDirection: "row-reverse", alignItems: "center", justifyContent: "center", gap: 16, backgroundColor: "#F3F4F6", padding: 20, borderRadius: 18, marginVertical: 15, borderWidth: 1, borderColor: BORDER },
  codeText: { fontSize: 28, fontWeight: "900", letterSpacing: 3, color: TEXT },
  copyBtn: { padding: 8, backgroundColor: "white", borderRadius: 10, borderWidth: 1, borderColor: BORDER },
  codeHint: { fontSize: 12, color: MUTED, textAlign: 'center' },
  requestItem: { backgroundColor: "#F9FAFB", borderRadius: 16, padding: 12, marginBottom: 12, borderWidth: 1, borderColor: BORDER },
  requestRow: { flexDirection: "row-reverse", alignItems: "center", gap: 10, flex: 1 },
  requestAvatar: { width: 34, height: 34, borderRadius: 12, backgroundColor: "rgba(2,132,199,0.10)", alignItems: "center", justifyContent: "center" },
  requestTextWrap: { flex: 1 },
  requestName: { fontSize: 14, fontWeight: "900", color: TEXT, textAlign: "right" },
  requestActions: { flexDirection: "row-reverse", gap: 8, marginTop: 12 },
  approveBtn: { flex: 1, backgroundColor: "#16A34A", paddingVertical: 10, borderRadius: 12, alignItems: "center" },
  approveBtnText: { color: "white", fontWeight: "900", fontSize: 13 },
  rejectBtn: { flex: 1, backgroundColor: "#FFFFFF", borderWidth: 1, borderColor: "#FCA5A5", paddingVertical: 10, borderRadius: 12, alignItems: "center" },
  rejectBtnText: { color: "#B91C1C", fontWeight: "900", fontSize: 13 },
  memberSelectItem: { flexDirection: "row-reverse", alignItems: "center", justifyContent: "space-between", paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: BORDER },
  deleteAction: { padding: 5 },
});