import { useQuery } from "@tanstack/react-query";
import { getDomainTrends } from "../../services/api/insights";
import type { DomainTrendParams } from "../../services/api/insights";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/Table";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "../ui/Card";

interface DomainTrendsTableProps {
    period: DomainTrendParams['period'];
}

export function DomainTrendsTable({ period }: DomainTrendsTableProps) {
    const { data, isLoading, error } = useQuery({
        queryKey: ['domain-trends', period],
        queryFn: () => getDomainTrends({ period })
    });

    if (isLoading) {
        return (
            <div className="rounded-md border border-border-default bg-bg-surface overflow-hidden p-8 text-center text-text-secondary animate-pulse">
                Loading domain trends...
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-md border border-border-default bg-bg-surface overflow-hidden p-8 text-center text-status-error">
                Failed to load domain trends.
            </div>
        );
    }

    const trends = data?.data || [];

    return (
        <div className="rounded-md border border-border-default bg-bg-surface overflow-hidden">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Domain</TableHead>
                        <TableHead className="text-right">Jobs Today</TableHead>
                        <TableHead className="text-right">Jobs Yesterday</TableHead>
                        <TableHead className="text-center">WoW Change</TableHead>
                        <TableHead className="text-right">Active Companies</TableHead>
                        <TableHead>Top Hiring Company</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {trends.length === 0 ? (
                        <TableRow>
                            <TableCell colSpan={6} className="text-center text-text-secondary py-8 h-24">
                                No domain trends found
                            </TableCell>
                        </TableRow>
                    ) : (
                        trends.map((trend) => {
                            const isPositive = trend.wow_change > 0;
                            const isNegative = trend.wow_change < 0;

                            return (
                                <TableRow key={trend.domain}>
                                    <TableCell className="font-medium">{trend.domain}</TableCell>
                                    <TableCell className="text-right font-semibold">{trend.jobs_today}</TableCell>
                                    <TableCell className="text-right text-text-secondary">{trend.jobs_yesterday}</TableCell>
                                    <TableCell className="text-center">
                                        <div className={cn(
                                            "inline-flex items-center justify-center gap-1 px-2 py-0.5 rounded text-xs font-semibold w-20",
                                            isPositive ? "bg-status-success/10 text-status-success" :
                                                isNegative ? "bg-status-error/10 text-status-error" :
                                                    "bg-bg-elevated text-text-secondary"
                                        )}>
                                            {isPositive ? <TrendingUp size={14} className="shrink-0" /> :
                                                isNegative ? <TrendingDown size={14} className="shrink-0" /> :
                                                    <Minus size={14} className="shrink-0" />}
                                            {isPositive ? '+' : ''}{trend.wow_change}%
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">{trend.active_companies}</TableCell>
                                    <TableCell>
                                        <span className="text-text-primary px-2 py-1 bg-border-subtle/30 rounded text-xs font-medium">
                                            {trend.top_hiring_company || '-'}
                                        </span>
                                    </TableCell>
                                </TableRow>
                            );
                        })
                    )}
                </TableBody>
            </Table>
        </div>
    );
}
