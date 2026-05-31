export function playerLabel(index?: number): string {
  return index === undefined ? "Player Profile" : `Player ${index + 1}`;
}
