import { useState, useRef, useEffect } from "react";
import { ChevronDown, X, Search } from "lucide-react";

interface Option {
  value: string;
  label: string;
}

interface MultiSelectDropdownProps {
  options: Option[];
  selected: string[];
  onChange: (selected: string[]) => void;
  placeholder: string;
  loading?: boolean;
}

export default function MultiSelectDropdown({
  options,
  selected,
  onChange,
  placeholder,
  loading = false,
}: MultiSelectDropdownProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const filtered = options.filter((o) =>
    o.label.toLowerCase().includes(search.toLowerCase())
  );

  const toggle = (value: string) => {
    onChange(
      selected.includes(value)
        ? selected.filter((v) => v !== value)
        : [...selected, value]
    );
  };

  const removeTag = (value: string) => {
    onChange(selected.filter((v) => v !== value));
  };

  const selectedLabels = selected
    .map((v) => options.find((o) => o.value === v)?.label ?? v)
    .slice(0, 3);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2.5 bg-dark-700 border border-dark-600 rounded-lg text-sm text-gray-300 hover:border-gold/50 transition-colors min-h-[42px]"
      >
        <div className="flex flex-wrap gap-1 flex-1 text-left">
          {selected.length === 0 && (
            <span className="text-gray-500">{placeholder}</span>
          )}
          {selectedLabels.map((label, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-gold/15 text-gold rounded text-xs"
            >
              {label}
              <X
                className="w-3 h-3 cursor-pointer hover:text-white"
                onClick={(e) => {
                  e.stopPropagation();
                  removeTag(selected[i]);
                }}
              />
            </span>
          ))}
          {selected.length > 3 && (
            <span className="text-xs text-gray-500">
              +{selected.length - 3} more
            </span>
          )}
        </div>
        <ChevronDown
          className={`w-4 h-4 text-gray-500 shrink-0 transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 w-full bg-dark-700 border border-dark-600 rounded-lg shadow-xl max-h-64 overflow-hidden">
          <div className="p-2 border-b border-dark-600">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search..."
                className="w-full pl-8 pr-3 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-gray-300 placeholder-gray-500 focus:outline-none focus:border-gold/50"
                autoFocus
              />
            </div>
          </div>
          <div className="overflow-y-auto max-h-48">
            {loading && (
              <div className="px-3 py-4 text-center text-gray-500 text-sm">
                Loading...
              </div>
            )}
            {!loading && filtered.length === 0 && (
              <div className="px-3 py-4 text-center text-gray-500 text-sm">
                No options found
              </div>
            )}
            {filtered.map((option) => (
              <label
                key={option.value}
                className="flex items-center gap-2 px-3 py-2 hover:bg-dark-600 cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(option.value)}
                  onChange={() => toggle(option.value)}
                  className="w-3.5 h-3.5 rounded border-dark-600 bg-dark-800 text-gold accent-gold"
                />
                <span className="text-sm text-gray-300">{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
