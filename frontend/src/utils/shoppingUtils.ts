export function normalizeName(s: string) {
  return s.trim().toLowerCase();
}

export function locationLabel(loc: string) {
  // We no longer translate fixed keys. We just return the string as provided by the user.
  return loc || "אחר";
}

export function locationIcon(loc: string) {
  // Use a single generic icon for all categories to keep it clean and uniform.
  return "list-outline";
}

