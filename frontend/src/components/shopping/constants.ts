import { BRAND } from "../shopping/styles"; // אפשר להשתמש באותו BRAND מקודם

export const LIST_BRAND = {
  ...BRAND,
  SUCCESS: "#10B981",
};

export function formatUpdatedAt(dateString: string): string {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) return "עודכן לאחרונה";
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffHours < 1) return "עודכן עכשיו";
  if (diffHours < 24) return `עודכן לפני ${diffHours} שעות`;
  if (diffDays === 1) return "עודכן אתמול";
  if (diffDays < 7) return `עודכן לפני ${diffDays} ימים`;
  return `עודכן ב־${date.toLocaleDateString("he-IL")}`;
}