export const CHAMPION_TRAIT_MAP: Record<string, string> = {
  TFT17_Aatrox: "Melee",
  TFT17_Akali: "Assassin",
  TFT17_Belveth: "Ranged",
  TFT17_Blitzcrank: "Tank",
  TFT17_Caitlyn: "Ranged",
  TFT17_Chogath: "Tank",
  TFT17_Corki: "Ranged",
  TFT17_Ezreal: "Ranged",
  TFT17_Fiora: "Melee",
  TFT17_Gnar: "Melee",
  TFT17_Gragas: "Tank",
  TFT17_Graves: "Ranged",
  TFT17_Illaoi: "Tank",
  TFT17_IvernMinion: "Summon",
  TFT17_Jax: "Melee",
  TFT17_Jhin: "Ranged",
  TFT17_Kaisa: "Ranged",
  TFT17_Karma: "Ranged",
  TFT17_Kindred: "Ranged",
  TFT17_Leblanc: "Assassin",
  TFT17_Leona: "Tank",
  TFT17_Lissandra: "Ranged",
  TFT17_Maokai: "Tank",
  TFT17_MasterYi: "Melee",
  TFT17_Milio: "Ranged",
  TFT17_Mordekaiser: "Melee",
  TFT17_Morgana: "Ranged",
  TFT17_Nasus: "Tank",
  TFT17_Nunu: "Tank",
  TFT17_Pantheon: "Melee",
  TFT17_Rammus: "Tank",
  TFT17_Riven: "Melee",
  TFT17_Sona: "Ranged",
  TFT17_Summon: "Summon",
  TFT17_TahmKench: "Tank",
  TFT17_Talon: "Assassin",
  TFT17_Teemo: "Ranged",
  TFT17_TwistedFate: "Ranged",
  TFT17_Vex: "Ranged",
  TFT17_Zoe: "Ranged",
};

export const CHAMPION_DISPLAY_NAME: Record<string, string> = {
  TFT17_Aatrox: "Aatrox",
  TFT17_Akali: "Akali",
  TFT17_Belveth: "Belveth",
  TFT17_Blitzcrank: "Blitzcrank",
  TFT17_Caitlyn: "Caitlyn",
  TFT17_Chogath: "Chogath",
  TFT17_Corki: "Corki",
  TFT17_Ezreal: "Ezreal",
  TFT17_Fiora: "Fiora",
  TFT17_Gnar: "Gnar",
  TFT17_Gragas: "Gragas",
  TFT17_Graves: "Graves",
  TFT17_Illaoi: "Illaoi",
  TFT17_IvernMinion: "Ivern",
  TFT17_Jax: "Jax",
  TFT17_Jhin: "Jhin",
  TFT17_Kaisa: "Kaisa",
  TFT17_Karma: "Karma",
  TFT17_Kindred: "Kindred",
  TFT17_Leblanc: "Leblanc",
  TFT17_Leona: "Leona",
  TFT17_Lissandra: "Lissandra",
  TFT17_Maokai: "Maokai",
  TFT17_MasterYi: "Master Yi",
  TFT17_Milio: "Milio",
  TFT17_Mordekaiser: "Mordekaiser",
  TFT17_Morgana: "Morgana",
  TFT17_Nasus: "Nasus",
  TFT17_Nunu: "Nunu",
  TFT17_Pantheon: "Pantheon",
  TFT17_Rammus: "Rammus",
  TFT17_Riven: "Riven",
  TFT17_Sona: "Sona",
  TFT17_Summon: "Summon",
  TFT17_TahmKench: "Tahm Kench",
  TFT17_Talon: "Talon",
  TFT17_Teemo: "Teemo",
  TFT17_TwistedFate: "Twisted Fate",
  TFT17_Vex: "Vex",
  TFT17_Zoe: "Zoe",
};

export function getDisplayName(championId: string): string {
  return CHAMPION_DISPLAY_NAME[championId] ?? championId
    .replace(/^TFT\d+_/, "")
    .replace(/^TFT_/, "")
    .replace(/_/g, " ")
    .replace(/([a-z])([A-Z])/g, "$1 $2")
    .replace(/\s+/g, " ")
    .trim();
}

export function getChampionTrait(championId: string): string {
  return CHAMPION_TRAIT_MAP[championId] ?? "Unknown";
}
