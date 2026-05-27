export interface CompTrait {
  name: string;
  tier_current: number;
}

export interface CompSummary {
  comp_signature: string;
  traits: CompTrait[];
  core_units: string[];
  total_games: number;
  wins: number;
  top4_count: number;
  avg_placement: number;
  win_rate: number;
  top4_rate: number;
  last_updated: string | null;
  pick_rate?: number;
}

export interface CompDetail extends CompSummary {
  core_items?: string[];
}

export interface CompListResponse {
  items: CompSummary[];
  total: number;
  limit: number;
  offset: number;
}

export type SortField = "win_rate" | "avg_placement" | "top4_rate";

export type TierLabel = "S" | "A" | "B" | "C";

export interface TierBucket {
  tier: TierLabel;
  color: string;
  range: string;
  comps: CompSummary[];
}
