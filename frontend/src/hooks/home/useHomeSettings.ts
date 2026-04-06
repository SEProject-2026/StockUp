import { useState, useEffect, useMemo, useRef } from "react";
import { Alert } from "react-native";
import { router } from "expo-router";
import { useAuth } from "@/src/context/auth-context";
import {
  updateExpirationRange,
  answerJoinRequest,
  getMyHomes,
  getHomeDetails,
  leaveHome,
  switchHomeHead,
  removeMember,
  deleteHome,
} from "@/src/api/homes";
import { useRealtimeContext } from "../../providers/RealtimeProvider";

export function useHomeSettings(currentHomeId?: string) {
  const { session } = useAuth();
  const currentUserId = session?.user?.id;
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [expiryAlertsEnabled, setExpiryAlertsEnabled] = useState(true);
  const [expiryLeadDays, setExpiryLeadDays] = useState<number>(3);

  const [daysModalOpen, setDaysModalOpen] = useState(false);
  const [homeCodeOpen, setHomeCodeOpen] = useState(false);
  const [joinRequestsOpen, setJoinRequestsOpen] = useState(false);
  const [switchHeadOpen, setSwitchHeadOpen] = useState(false);
  const [membersOpen, setMembersOpen] = useState(false);

  const [homeInviteCode, setHomeInviteCode] = useState("");
  const [loadingHomeCode, setLoadingHomeCode] = useState(false);
  const [savingDays, setSavingDays] = useState(false);

  const [homeMeta, setHomeMeta] = useState<any>(null);
  const [homeMembers, setHomeMembers] = useState<any[]>([]);
  const [loadingHomeMeta, setLoadingHomeMeta] = useState(false);

  const [joinRequests, setJoinRequests] = useState<any[]>([]);
  const [loadingJoinRequests, setLoadingJoinRequests] = useState(false);
  const [processingRequestId, setProcessingRequestId] = useState<string | null>(null);

  const [switchingHead, setSwitchingHead] = useState(false);
  const [removingMemberId, setRemovingMemberId] = useState<string | null>(null);
  const [leavingHomeLoading, setLeavingHomeLoading] = useState(false);
  const [deletingHomeLoading, setDeletingHomeLoading] = useState(false);

  const { homeMetaVersionByHome } = useRealtimeContext();
  const currentHomeMetaVersion = currentHomeId ? (homeMetaVersionByHome[currentHomeId] ?? 0) : 0;

  const clampDays = (n: number) => Math.max(0, Math.min(30, n));

  const loadHomeData = async () => {
    if (!currentHomeId || !currentUserId) return;
    try {
      setLoadingHomeMeta(true);
      const homesRes = await getMyHomes();
      const currentHome = Array.isArray(homesRes.data)
        ? homesRes.data.find((h: any) => String(h.id) === String(currentHomeId))
        : null;

      if (!currentHome) throw new Error("הבית לא נמצא");
      setHomeMeta(currentHome);
      if (typeof currentHome.expiration_range === "number") setExpiryLeadDays(currentHome.expiration_range);

      const detailsRes = await getHomeDetails(currentHomeId);
      const memberNamesMap = detailsRes.data?.member_names || {};
      const members = Object.entries(memberNamesMap).map(([id, name]) => ({
        user_id: String(id),
        name: String(name),
      }));
      setHomeMembers(members);
    } catch (e: any) {
      Alert.alert("שגיאה", "טעינת הנתונים נכשלה");
    } finally {
      setLoadingHomeMeta(false);
    }
  };

  // Automatically load when home or user changes
  useEffect(() => { 
    if (currentHomeId && currentUserId) {
      loadHomeData(); 
    }
  }, [currentHomeId, currentUserId]);

  // Real-time management permission calculation
  const isHomeAdmin = useMemo(() => {
    return !!homeMeta && !!currentUserId && String(homeMeta.admin_id) === String(currentUserId);
  }, [homeMeta, currentUserId]);
  const handleAnswerJoinRequest = async (userId: string, approved: boolean) => {
    try {
      setProcessingRequestId(userId);
      await answerJoinRequest(currentHomeId!, { user_id: userId, approved });
      setJoinRequests(prev => prev.filter(req => req.user_id !== userId));
      await loadHomeData();
    } catch (e) { 
      const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message))? e.message : "הפעולה נכשלה";
      Alert.alert("שגיאה", message); 
    }
    finally { setProcessingRequestId(null); }
  };

  const handleSaveExpiration = async () => {
    try {
      setSavingDays(true);
      await updateExpirationRange(currentHomeId!, { new_range: expiryLeadDays });
      setDaysModalOpen(false);
      await loadHomeData();
    } catch (e) { 
      const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "העדכון נכשל";
      Alert.alert("שגיאה", message); 
    }
    finally { setSavingDays(false); }
  };

  const handleSwitchHead = async (uId: string, uName: string) => {
    Alert.alert("החלפת מנהל", `להפוך את ${uName} למנהל הבית?`, [
      { text: "ביטול" },
      { text: "אישור", onPress: async () => {
        try {
          setSwitchingHead(true);
          await switchHomeHead(currentHomeId!, { new_head_id: uId });
          setSwitchHeadOpen(false);
          await loadHomeData();
        } catch (e) { 
          const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message))? e.message : "ההחלפה נכשלה";
          Alert.alert("שגיאה", message); 
        }
        finally { setSwitchingHead(false); }
      }}
    ]);
  };

  const handleRemoveMember = async (uId: string, uName: string) => {
    Alert.alert("הסרת משתתף", `להסיר את ${uName} מהבית?`, [
      { text: "ביטול" },
      { text: "הסרה", style: "destructive", onPress: async () => {
        try {
          setRemovingMemberId(uId);
          await removeMember(currentHomeId!, uId);
          await loadHomeData();
        } catch (e) { 
          const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message))? e.message : "ההסרה נכשלה";
          Alert.alert("שגיאה", message); 
        }
        finally { setRemovingMemberId(null); }
      }}
    ]);
  };

  const handleLeaveHome = () => {
    Alert.alert("עזיבת בית", "האם את/ה בטוח/ה שברצונך לעזוב?", [
      { text: "ביטול" },
      { text: "עזיבה", style: "destructive", onPress: async () => {
        try {
          setLeavingHomeLoading(true);
          await leaveHome(currentHomeId!);
          router.replace("/home/home");
        } catch (e) { 
          const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "העזיבה נכשלה";
          Alert.alert("שגיאה", message); 
        }
        finally { setLeavingHomeLoading(false); }
      }}
    ]);
  };

  const handleDeleteHome = () => {
    Alert.alert("מחיקת בית", "פעולה זו אינה הפיכה. האם למחוק?", [
      { text: "ביטול" },
      { text: "מחיקה", style: "destructive", onPress: async () => {
        try {
          setDeletingHomeLoading(true);
          await deleteHome(currentHomeId!);
          router.replace("/home/home");
        } catch (e) { 
          const message = (e instanceof Error && /[\u0590-\u05FF]/.test(e.message)) ? e.message : "המחיקה נכשלה";
          Alert.alert("שגיאה", message); 
        }
        finally { setDeletingHomeLoading(false); }
      }}
    ]);
  };

  return {
    state: {
      currentUserId, notificationsEnabled, expiryAlertsEnabled, expiryLeadDays,
      daysModalOpen, homeCodeOpen, joinRequestsOpen, switchHeadOpen, membersOpen,
      homeInviteCode, loadingHomeCode, savingDays, homeMeta, homeMembers,
      loadingHomeMeta, joinRequests, loadingJoinRequests, processingRequestId,
      switchingHead, removingMemberId, leavingHomeLoading, deletingHomeLoading, isHomeAdmin
    },
    actions: {
      setNotificationsEnabled, setExpiryAlertsEnabled, setExpiryLeadDays,
      setDaysModalOpen, setHomeCodeOpen, setJoinRequestsOpen, setSwitchHeadOpen, setMembersOpen,
      clampDays, loadHomeData, setHomeInviteCode, setLoadingHomeCode, setJoinRequests, setLoadingJoinRequests,
      handleAnswerJoinRequest, handleSaveExpiration, handleSwitchHead, handleRemoveMember, handleLeaveHome, handleDeleteHome
    }
  };
}