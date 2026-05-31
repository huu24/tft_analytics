import { Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

interface BreadcrumbItem {
  label: string;
  to?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="flex min-w-0 max-w-full items-center gap-1.5 overflow-hidden text-sm text-gray-400">
      <Link
        to="/players"
        className="hover:text-gold transition-colors flex items-center gap-1 shrink-0"
      >
        <Home className="w-3.5 h-3.5" />
      </Link>
      {items.map((item, i) => (
        <span key={i} className="flex min-w-0 items-center gap-1.5">
          <ChevronRight className="w-3 h-3 shrink-0 text-gray-600" />
          {item.to ? (
            <Link
              to={item.to}
              title={item.label}
              className="text-truncate-safe max-w-[clamp(7rem,24vw,18rem)] hover:text-gold transition-colors"
            >
              {item.label}
            </Link>
          ) : (
            <span
              title={item.label}
              className="text-truncate-safe max-w-[clamp(7rem,24vw,18rem)] text-white font-medium"
            >
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}
