import { useState, useEffect } from "react";
import { Search } from "lucide-react";

interface CompanyFiltersProps {
    initialSearch?: string;
    onFilterChange: (filters: Record<string, any>) => void;
}

const DOMAINS = ["Logistics", "Technology", "Construction", "Finance", "Healthcare", "Energy"];
const TAGS = ["Spiking", "Struggling", "New Entrant", "Salary Signal"];

export function CompanyFilters({ initialSearch = "", onFilterChange }: CompanyFiltersProps) {
    const [search, setSearch] = useState(initialSearch);
    const [activeDomain, setActiveDomain] = useState<string | null>(null);
    const [activeTag, setActiveTag] = useState<string | null>(null);

    useEffect(() => {
        // Debounce search
        const timer = setTimeout(() => {
            const filters: Record<string, any> = {};
            if (search) filters.search = search;
            if (activeDomain) filters.domain = activeDomain.toLowerCase();
            if (activeTag) filters.bd_tag = activeTag;

            onFilterChange(filters);
        }, 300);

        return () => clearTimeout(timer);
    }, [search, activeDomain, activeTag, onFilterChange]);

    return (
        <div className="w-full bg-bg-surface p-4 rounded-card border border-border-subtle flex flex-col gap-4">
            <div className="flex flex-wrap gap-4 items-center justify-between">

                {/* Search */}
                <div className="relative w-full max-w-sm">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-4 w-4 text-text-muted" />
                    </div>
                    <input
                        type="text"
                        placeholder="Search companies..."
                        className="block w-full pl-10 pr-3 py-2 border border-border-default rounded-md leading-5 bg-bg-base text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary sm:text-sm transition-colors"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                {/* Clear Filters */}
                {(search || activeDomain || activeTag) && (
                    <button
                        onClick={() => {
                            setSearch("");
                            setActiveDomain(null);
                            setActiveTag(null);
                        }}
                        className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                    >
                        Clear filters
                    </button>
                )}
            </div>

            <div className="flex flex-col gap-3">
                {/* Domain Filters */}
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase w-16">Domain</span>
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

                {/* Tag Filters */}
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold text-text-secondary uppercase w-16">BD Tag</span>
                    {TAGS.map(tag => (
                        <button
                            key={tag}
                            onClick={() => setActiveTag(activeTag === tag ? null : tag)}
                            className={`px-3 py-1 rounded-full border text-sm transition-colors ${activeTag === tag
                                ? 'bg-text-primary border-text-primary text-bg-base'
                                : 'bg-bg-elevated border-border-default text-text-secondary hover:text-text-primary hover:border-border-subtle hover:bg-bg-elevated/80'
                                }`}
                        >
                            {tag}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
