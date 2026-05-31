import { useState, useEffect, useRef } from "react";
import { Search, X } from "lucide-react";
import apiClient from "@/api/client";
import type { PlayerSearchResult } from "@/types/player";

interface SearchBarProps {
  onSelect: (puuid: string) => void;
}

export default function SearchBar({ onSelect }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PlayerSearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await apiClient.get<PlayerSearchResult[]>(
          `/players/search?name=${encodeURIComponent(query)}`
        );
        setResults(res.data);
        setOpen(true);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div ref={wrapRef} className="relative w-full max-w-md">
      <div className="flex items-center gap-2 bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 focus-within:border-gold transition-colors">
        <Search className="w-4 h-4 text-gray-400 shrink-0" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search summoner name..."
          className="min-w-0 flex-1 bg-transparent text-sm text-white placeholder-gray-500 outline-none"
        />
        {query && (
          <button onClick={() => { setQuery(""); setResults([]); setOpen(false); }}>
            <X className="w-4 h-4 text-gray-400 hover:text-white" />
          </button>
        )}
      </div>

      {open && results.length > 0 && (
        <ul className="absolute z-50 mt-1 w-full bg-dark-700 border border-dark-600 rounded-lg shadow-xl overflow-hidden">
          {results.map((r) => (
            <li key={r.puuid}>
              <button
                onClick={() => {
                  onSelect(r.puuid);
                  setOpen(false);
                  setQuery("");
                }}
                className="w-full min-w-0 text-left px-4 py-2.5 hover:bg-dark-600 transition-colors flex items-center justify-between gap-3"
              >
                <span title={r.puuid} className="text-truncate-safe text-sm text-white font-medium">
                  {r.puuid}
                </span>
                <span className="shrink-0 text-xs text-gray-400">{r.total_games} games</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {open && loading && (
        <div className="absolute z-50 mt-1 w-full bg-dark-700 border border-dark-600 rounded-lg p-3 text-center text-sm text-gray-400">
          Searching...
        </div>
      )}
    </div>
  );
}
