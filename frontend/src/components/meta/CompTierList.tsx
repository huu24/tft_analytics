import type { CompSummary, TierBucket } from "@/types/composition";
import CompCard from "./CompCard";

interface CompTierListProps {
  comps: CompSummary[];
  onCompClick: (comp: CompSummary) => void;
}

function buildTiers(comps: CompSummary[]): TierBucket[] {
  const tiers: TierBucket[] = [
    { tier: "S", color: "#0ac8b9", range: ">25% WR", comps: [] },
    { tier: "A", color: "#4ade80", range: "20-25% WR", comps: [] },
    { tier: "B", color: "#c8aa6e", range: "15-20% WR", comps: [] },
    { tier: "C", color: "#ef4444", range: "<15% WR", comps: [] },
  ];

  for (const c of comps) {
    const wr = c.win_rate;
    if (wr > 0.25) tiers[0].comps.push(c);
    else if (wr >= 0.2) tiers[1].comps.push(c);
    else if (wr >= 0.15) tiers[2].comps.push(c);
    else tiers[3].comps.push(c);
  }

  return tiers;
}

export default function CompTierList({ comps, onCompClick }: CompTierListProps) {
  const tiers = buildTiers(comps);

  return (
    <div className="space-y-6">
      {tiers.map((bucket) => (
        <div key={bucket.tier}>
          <div className="flex items-center gap-3 mb-3">
            <span
              className="flex items-center justify-center w-8 h-8 rounded-lg text-sm font-bold text-white"
              style={{ backgroundColor: bucket.color }}
            >
              {bucket.tier}
            </span>
            <span className="text-xs text-gray-400">{bucket.range}</span>
            <span className="text-xs text-gray-500 ml-auto">
              {bucket.comps.length} comps
            </span>
          </div>

          {bucket.comps.length === 0 ? (
            <p className="text-xs text-gray-600 pl-11">No compositions in this tier.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {bucket.comps.map((comp) => (
                <CompCard key={comp.comp_signature} comp={comp} onClick={onCompClick} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
