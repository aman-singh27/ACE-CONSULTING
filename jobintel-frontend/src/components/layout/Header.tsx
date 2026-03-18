import { Bell, Search } from "lucide-react";
import { useLocation } from "react-router-dom";

const ROUTE_TITLES: Record<string, string> = {
  "/": "Command Center",
  "/companies": "Company Intelligence",
  "/hubspot": "HubSpot CRM",
  "/jobs": "Master Job Table",
  "/runs": "Run Monitor",
  "/scrapers": "Scrapers",
};

export function Header() {
  const location = useLocation();
  const title = ROUTE_TITLES[location.pathname] || "Dashboard";

  return (
    <header className="sticky top-0 z-10 flex h-16 shrink-0 items-center gap-x-6 border-b border-border-default bg-bg-primary/80 backdrop-blur-md px-8 shadow-sm">
      <div className="flex flex-1 items-center justify-between">
        {/* Left Side: Title */}
        <div className="flex items-center gap-x-4">
          <h1 className="text-xl font-semibold text-text-primary leading-none">
            {title}
          </h1>
          <div className="rounded-full bg-accent-primary/10 px-2 py-0.5 text-xs font-medium text-accent-primary border border-accent-primary/20">
            Production
          </div>
        </div>

        {/* Right Side: Search & Actions */}
        <div className="flex items-center gap-x-6">
          <button className="text-text-muted hover:text-text-primary transition-colors cursor-pointer">
            <Search className="h-5 w-5 pointer-events-none" />
          </button>
          <button className="relative text-text-muted hover:text-text-primary transition-colors cursor-pointer">
            <Bell className="h-5 w-5 pointer-events-none" />
            <span className="absolute top-0 right-0 h-2 w-2 rounded-full bg-red-500 border border-bg-primary pointer-events-none"></span>
          </button>

          <div className="h-4 w-px bg-border-default"></div>

          <div className="flex items-center gap-x-3">
            <div className="h-8 w-8 rounded-full bg-bg-surface flex justify-center items-center border border-border-subtle">
              <span className="text-sm font-semibold text-text-primary">A</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
