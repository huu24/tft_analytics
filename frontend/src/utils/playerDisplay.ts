export function playerLabel(playerName?: string | null, fallback?: string): string {
  if (playerName && playerName.trim()) return playerName;
  return fallback ?? "Unknown player";
}
