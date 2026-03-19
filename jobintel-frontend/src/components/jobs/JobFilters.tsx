import { useState, useEffect } from "react";
import { Search } from "lucide-react";

interface JobFiltersProps {
    onFilterChange: (filters: Record<string, any>) => void;
}

const DOMAINS = ["Logistics", "Technology", "Construction", "Finance", "Healthcare", "Energy"];
const PLATFORMS = ["LinkedIn", "NaukriGulf", "Bayt"];

export function JobFilters({ onFilterChange }: JobFiltersProps) {
    const [search, setSearch] = useState("");
    const [activeDomain, setActiveDomain] = useState<string | null>(null);
    const [activePlatform, setActivePlatform] = useState<string | null>(null);
    const [hideDuplicates, setHideDuplicates] = useState<boolean>(false);
    const [hideConfidential, setHideConfidential] = useState<boolean>(false);

    useEffect(() => {
        // Debounce search
        const timer = setTimeout(() => {
            const filters: Record<string, any> = {};
            if (search) filters.search = search;
            if (activeDomain) filters.domain = activeDomain.toLowerCase();
            if (activePlatform) filters.platform = activePlatform.toLowerCase();
            if (hideDuplicates) filters.is_duplicate = false;
            if (hideConfidential) filters.hide_confidential = true;

            onFilterChange(filters);
        }, 300);

        return () => clearTimeout(timer);
    }, [search, activeDomain, activePlatform, hideDuplicates, hideConfidential, onFilterChange]);

    return (
        <div className="w-full bg-bg-surface p-4 rounded-card border border-border-subtle flex flex-col gap-4">
            <div className="flex flex-wrap gap-4 items-center justify-between">

                {/* Search */}
                <div className="relative w-full max-w-md">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-4 w-4 text-text-muted" />
                    </div>
                    <input
                        type="text"
                        placeholder="Search jobs by title or company..."
                        className="block w-full pl-10 pr-3 py-2 border border-border-default rounded-md leading-5 bg-bg-base text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary sm:text-sm transition-colors"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                {/* Hide Duplicates Toggle */}
                <label className="flex items-center gap-2 cursor-pointer text-sm text-text-secondary hover:text-text-primary transition-colors">
                    <input
                        type="checkbox"
                        checked={hideDuplicates}
                        onChange={(e) => setHideDuplicates(e.target.checked)}
                        className="rounded border-border-default text-accent-primary focus:ring-accent-primary bg-bg-base"
                    />
                    Hide duplicates
                </label>

                {/* Hide Confidential Toggle */}
                <label className="flex items-center gap-2 cursor-pointer text-sm text-text-secondary hover:text-text-primary transition-colors">
                    <input
                        type="checkbox"
                        checked={hideConfidential}
                        onChange={(e) => setHideConfidential(e.target.checked)}
                        className="rounded border-border-default text-accent-primary focus:ring-accent-primary bg-bg-base"
                    />
                    Hide confidential companies
                </label>

                {/* Clear Filters */}
                {(search || activeDomain || activePlatform || hideDuplicates || hideConfidential) && (
                    <button
                        onClick={() => {
                            setSearch("");
                            setActiveDomain(null);
                            setActivePlatform(null);
                            setHideDuplicates(false);
                            setHideConfidential(false);
                        }}
                        className="text-sm text-text-error hover:text-red-400 transition-colors ml-auto"
                    >
                        Clear filters
                    </button>
                )}
            </div>

            <div className="flex flex-col gap-3">
                {/* Domain Filters */}
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase w-16 shrink-0">Domain</span>
                    {DOMAINS.map(domain => (
                        <button
                            key={domain}
                            onClick={() => setActiveDomain(activeDomain === domain ? null : domain)}
                            className={`px-3 py-1 rounded-full border text-sm transition-colors ${activeDomain === domain
                                ? 'bg-accent-primary border-accent-primary text-white'
                                : 'bg-bg-elevated border-border-default text-text-secondary hover:text-text-primary hover:border-border-subtle hover:bg-bg-elevated/80'
                                }`}
                        >
                            {domain}
                        </button>
                    ))}
                </div>

                {/* Platform Filters */}
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase w-16 shrink-0">Platform</span>
                    {PLATFORMS.map(platform => (
                        <button
                            key={platform}
                            onClick={() => setActivePlatform(activePlatform === platform ? null : platform)}
                            className={`px-3 py-1 rounded-full border text-sm transition-colors ${activePlatform === platform
                                ? 'bg-text-primary border-text-primary text-bg-base'
                                : 'bg-bg-elevated border-border-default text-text-secondary hover:text-text-primary hover:border-border-subtle hover:bg-bg-elevated/80'
                                }`}
                        >
                            {platform}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
