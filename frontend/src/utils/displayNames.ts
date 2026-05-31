import { getDisplayName } from "@/data/championTraits";
import type { CompSummary } from "@/types/composition";

function splitCamelCase(value: string): string {
  return value
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/([A-Z])([A-Z][a-z])/g, "$1 $2");
}

function humanizeId(value: string): string {
  return splitCamelCase(
    value
      .replace(/^TFT\d+_Item_/, "")
      .replace(/^TFT\d+_/, "")
      .replace(/^TFT_Item_/, "")
      .replace(/^TFT_/, "")
      .replace(/_/g, " ")
      .trim()
  ).replace(/\s+/g, " ").trim();
}

export function getItemDisplayName(itemId: string): string {
  return humanizeId(itemId);
}

export function getChampionDisplayName(championId: string): string {
  return getDisplayName(championId);
}

export function getTraitDisplayName(traitId: string): string {
  return humanizeId(traitId);
}

export function getCompDisplayName(comp: Pick<CompSummary, "core_units">): string {
  const names = comp.core_units.map(getChampionDisplayName).filter(Boolean);
  if (names.length === 0) return "Composition";
  if (names.length <= 3) return names.join(" + ");
  return `${names.slice(0, 3).join(" + ")} +${names.length - 3}`;
}
