export function normalizeName(s: string) {
  return s.trim().toLowerCase();
}

export function locationLabel(loc: string) {
  if (!loc || loc === "OTHER" || loc === "UNSORTED") return "אחר";
  return loc;
}

export function locationIcon(loc: string) {
  // Use a single generic icon for all categories to keep it clean and uniform.
  return "list-outline";
}

