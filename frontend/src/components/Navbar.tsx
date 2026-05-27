import { useLocation } from "react-router-dom";
import { Menu } from "lucide-react";

const pageTitles: Record<string, string> = {
  "/players": "Player Profile",
  "/meta": "Top Meta Compositions",
  "/champions": "Champion Analysis",
  "/items": "Item Analysis",
  "/analysis": "General Analysis",
};

interface NavbarProps {
  onMenuToggle: () => void;
}

export default function Navbar({ onMenuToggle }: NavbarProps) {
  const location = useLocation();
  const title = pageTitles[location.pathname] || "TFT Analytics";

  return (
    <header className="flex items-center gap-4 h-14 px-6 border-b border-dark-600 bg-dark-800 shrink-0">
      <button
        onClick={onMenuToggle}
        className="lg:hidden text-gray-400 hover:text-white transition-colors"
      >
        <Menu className="w-5 h-5" />
      </button>
      <h1 className="text-lg font-semibold text-white">{title}</h1>
    </header>
  );
}
