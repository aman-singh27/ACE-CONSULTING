import { Activity, Briefcase, Building2, LayoutDashboard } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "../ui/Card";

const NAV_ITEMS = [
    { label: 'Command Center', path: '/', icon: LayoutDashboard },
    { label: 'Company Intelligence', path: '/companies', icon: Building2 },
    { label: 'Master Job Table', path: '/jobs', icon: Briefcase },
    { label: 'Actors', path: '/actors', icon: Activity },
    { label: 'Run Monitor', path: '/runs', icon: Activity },
];

export function Sidebar() {
    const location = useLocation();

    return (
        <aside className="fixed left-0 top-0 h-screen w-[240px] flex-col border-r border-border-default bg-bg-surface px-4 py-6 flex">
            <div className="mb-8 flex items-center px-2">
                <div className="h-8 w-8 rounded bg-accent-primary mr-3 flex items-center justify-center font-bold text-white shadow-lg shadow-accent-primary/20">
                    JI
                </div>
                <h1 className="text-xl font-bold text-text-primary tracking-tight">JobIntel<span className="text-accent-primary">.</span></h1>
            </div>

            <nav className="flex-1 space-y-1.5">
                {NAV_ITEMS.map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={cn(
                                "flex items-center rounded-md px-3 py-2.5 text-sm font-medium transition-all group",
                                isActive
                                    ? "bg-accent-primary/10 text-accent-primary"
                                    : "text-text-secondary hover:bg-bg-elevated hover:text-text-primary"
                            )}
                        >
                            <item.icon
                                className={cn(
                                    "mr-3 h-5 w-5 flex-shrink-0 transition-colors",
                                    isActive ? "text-accent-primary" : "text-text-muted group-hover:text-text-primary"
                                )}
                                aria-hidden="true"
                            />
                            {item.label}
                        </Link>
                    );
                })}
            </nav>

            <div className="mt-auto px-2">
                <div className="rounded border border-border-subtle bg-bg-elevated p-3 text-xs text-text-muted">
                    <p className="font-semibold text-text-primary mb-1">Apify Sync</p>
                    <p>Online & Active</p>
                </div>
            </div>
        </aside>
    );
}
