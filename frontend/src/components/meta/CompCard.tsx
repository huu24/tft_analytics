import type { CompSummary } from "@/types/composition";

interface CompCardProps {
  comp: CompSummary;
  onClick: (comp: CompSummary) => void;
}

export default function CompCard({ comp, onClick }: CompCardProps) {
  return (
    <button
      onClick={() => onClick(comp)}
      className="w-full text-left p-4 rounded-xl bg-dark-700 border border-dark-600 hover:border-gold/50 transition-all duration-200 group"
    >
      <div className="flex items-start justify-between mb-3">
        <h4 className="text-sm font-semibold text-white group-hover:text-gold transition-colors leading-tight">
          {comp.comp_signature}
        </h4>
        <span className="text-xs text-teal font-bold ml-2 shrink-0">
          {(comp.win_rate * 100).toFixed(1)}%
        </span>
      </div>

      <div className="flex flex-wrap gap-1 mb-3">
        {comp.core_units.slice(0, 4).map((unit) => (
          <span
            key={unit}
            className="text-[10px] px-1.5 py-0.5 rounded bg-dark-600 text-gray-300"
          >
            {unit}
          </span>
        ))}
        {comp.core_units.length > 4 && (
          <span className="text-[10px] px-1.5 py-0.5 text-gray-500">
            +{comp.core_units.length - 4}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-500">Top4</span>
          <span className="text-gray-300">
            {(comp.top4_rate * 100).toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Avg</span>
          <span className="text-gray-300">{comp.avg_placement.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Games</span>
          <span className="text-gray-300">{comp.total_games.toLocaleString()}</span>
        </div>
      </div>
    </button>
  );
}
