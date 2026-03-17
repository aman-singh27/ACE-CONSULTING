import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDomainTrends } from "../../services/api/insights";
import type { DomainTrendParams } from "../../services/api/insights";
import { DomainTrendsTable } from "../../components/domain/DomainTrendsTable";
import { KpiCard } from "../../components/ui/KpiCard";

export function DomainIntelligencePage() {
    const [period, setPeriod] = useState<DomainTrendParams['period']>('30d');

    const { data, isLoading } = useQuery({
        queryKey: ['domain-trends', period],
        queryFn: () => getDomainTrends({ period })
    });

    const topDomains = data?.data?.slice(0, 3) || [];

    return (
        <div className="flex flex-col h-full w-full gap-6">
            {/* Header */}
            <div className="flex justify-between items-end shrink-0">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-text-primary">Domain Intelligence</h1>
                    <p className="text-text-secondary mt-1">Monitor hiring trends and activity across industries.</p>
                </div>

                {/* Filters */}
                <div className="flex bg-bg-surface rounded border border-border-default p-1 shadow-sm">
                    {(['7d', '30d', '60d'] as const).map((p) => (
                        <button
                            key={p}
                            onClick={() => setPeriod(p)}
                            className={`px-4 py-1.5 text-sm font-medium rounded transition-all ${period === p
                                ? 'bg-accent-primary text-white shadow'
                                : 'text-text-secondary hover:text-text-primary hover:bg-bg-elevated'
                                }`}
                        >
                            {p}
                        </button>
                    ))}
                </div>
            </div>

            {/* Leaderboard Cards */}
            <div>
                <h2 className="text-lg font-semibold text-text-primary mb-3">Top Hiring Domains</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 shrink-0">
                    {isLoading && !topDomains.length ? (
                        <>
                            <KpiCard loading label="Loading..." metric="-" />
                            <KpiCard loading label="Loading..." metric="-" />
                            <KpiCard loading label="Loading..." metric="-" />
                        </>
                    ) : topDomains.length > 0 ? (
                        topDomains.map((domain) => (
                            <KpiCard
                                key={domain.domain}
                                label="jobs"
                                metric={`${domain.domain} ${domain.jobs_today}`}
                            />
                        ))
                    ) : (
                        <div className="col-span-3 text-text-secondary">No domain data available.</div>
                    )}
                </div>
            </div>

            {/* Main Table Content */}
            <div className="flex-grow min-h-0 overflow-auto">
                <DomainTrendsTable period={period} />
            </div>
        </div>
    );
}
