import { useEffect, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2, Zap } from "lucide-react";
import type { ActorItem } from "../actors/ActorTable";
import { getActors } from "../../services/api/actors";
import type { CreditSummaryResponse } from "../../services/api/runs";
import { getCreditSummary } from "../../services/api/runs";
import { cn } from "../ui/Card";

const MONTHLY_BUDGET_USD = 29;
const COST_PER_1K_JOBS = 1.0;
const PER_CONFIG_CAP_USD = 1.1;

export interface CreditUsagePanelProps {
    refreshTrigger: number;
}

function platformLabel(platform: string) {
    const p = platform.toLowerCase();
    if (p === "linkedin") return "LinkedIn";
    if (p === "bayt") return "Bayt";
    if (p === "naukrigulf") return "NaukriGulf";
    return platform;
}

function platformBadgeClass(platform: string) {
    const p = platform.toLowerCase();
    if (p === "linkedin") return "bg-blue-500/10 text-blue-400 border border-blue-500/20";
    if (p === "bayt") return "bg-amber-400/10 text-amber-400 border border-amber-400/20";
    if (p === "naukrigulf") return "bg-green-500/10 text-green-400 border border-green-500/20";
    return "bg-bg-elevated text-text-secondary border border-border-subtle";
}

function barColorClass(isNearBudget: boolean, isOverBudget: boolean) {
    if (isOverBudget) return "bg-red-500";
    if (isNearBudget) return "bg-amber-400";
    return "bg-accent-primary";
}

function formatPct(pct: number) {
    return Math.round(pct);
}

export function CreditUsagePanel({ refreshTrigger }: CreditUsagePanelProps) {
    const queryClient = useQueryClient();

    const { data, isLoading: actorsLoading } = useQuery<ActorItem[]>({
        queryKey: ["actors"],
        queryFn: getActors,
    });

    const { data: creditData, isLoading: creditLoading } = useQuery<CreditSummaryResponse>({
        queryKey: ["creditSummary"],
        queryFn: getCreditSummary,
        refetchInterval: 60000,
    });

    useEffect(() => {
        queryClient.invalidateQueries({ queryKey: ["actors"] });
        queryClient.invalidateQueries({ queryKey: ["creditSummary"] });
    }, [refreshTrigger, queryClient]);

    const activeActors = useMemo(() => (data ?? []).filter((a) => a.is_active), [data]);

    const computed = useMemo(() => {
        const rows = activeActors.map((actor) => {
            const runsPerMonth = Math.round(30 / actor.frequency_days);
            const tpl = actor.apify_input_template as Record<string, unknown> | null | undefined;
            const maxItemsRaw = tpl && typeof tpl.maxItems === "number" ? tpl.maxItems : 200;
            const maxItems = Number.isFinite(maxItemsRaw) ? maxItemsRaw : 200;

            const monthlyCost = (maxItems * runsPerMonth / 1000) * COST_PER_1K_JOBS;
            const cappedCost = Math.min(monthlyCost, PER_CONFIG_CAP_USD);

            return {
                actor,
                runsPerMonth,
                maxItems,
                monthlyCost,
                cappedCost,
                isCapped: monthlyCost > PER_CONFIG_CAP_USD,
            };
        });

        const totalCommitted = rows.reduce((sum, r) => sum + r.cappedCost, 0);
        const remaining = Math.max(MONTHLY_BUDGET_USD - totalCommitted, 0);
        const pctUsed = Math.min((totalCommitted / MONTHLY_BUDGET_USD) * 100, 100);
        const isOverBudget = totalCommitted > MONTHLY_BUDGET_USD;
        const isNearBudget = pctUsed >= 70 && !isOverBudget;

        return { rows, totalCommitted, remaining, pctUsed, isOverBudget, isNearBudget };
    }, [activeActors]);

    const fillClass = barColorClass(computed.isNearBudget, computed.isOverBudget);

    const actualByActorId = useMemo(() => {
        const map: Record<string, number> = {};
        for (const row of creditData?.per_actor ?? []) {
            map[row.actor_config_id] = row.actual_spend_usd;
        }
        return map;
    }, [creditData]);

    if (actorsLoading) {
        return (
            <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
                <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                        <Zap size={16} className="text-accent-primary" />
                        <div className="text-base font-semibold text-text-primary">Monthly Credit Budget</div>
                    </div>
                    <div className="h-7 w-32 bg-bg-elevated rounded animate-pulse" />
                </div>

                <div className="w-full h-2 bg-bg-elevated rounded-full overflow-hidden animate-pulse" />
                <div className="flex justify-between mt-2">
                    <div className="h-4 w-44 bg-bg-elevated rounded animate-pulse" />
                    <div className="h-4 w-28 bg-bg-elevated rounded animate-pulse" />
                </div>
            </div>
        );
    }

    const actualSpend = creditData?.total_actual_spend_usd ?? null;
    const actualDiff =
        actualSpend === null ? null : actualSpend < computed.totalCommitted
            ? { dir: "under" as const, value: computed.totalCommitted - actualSpend }
            : { dir: "over" as const, value: actualSpend - computed.totalCommitted };

    return (
        <div className="bg-bg-surface border border-border-subtle rounded-xl p-5">
            {/* TOP ROW */}
            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                    <Zap size={16} className="text-accent-primary" />
                    <div className="text-base font-semibold text-text-primary">Monthly Credit Budget</div>
                </div>

                <div className="flex items-baseline">
                    <div className="font-bold text-xl text-text-primary">
                        ${computed.totalCommitted.toFixed(2)}
                    </div>
                    <div className="text-text-muted mx-1">/</div>
                    <div className="text-text-secondary">${MONTHLY_BUDGET_USD.toFixed(2)}</div>
                </div>
            </div>

            {/* PROGRESS BAR */}
            <div className="w-full h-2 bg-bg-elevated rounded-full overflow-hidden">
                <div
                    className={cn("transition-all duration-500 h-full rounded-full", fillClass)}
                    style={{ width: `${computed.pctUsed}%` }}
                />
            </div>

            <div className="flex justify-between mt-2">
                <div className="text-xs text-text-muted">Committed across active scrapers</div>
                {computed.isOverBudget ? (
                    <div className="text-xs text-red-500">
                        Over budget by ${(computed.totalCommitted - MONTHLY_BUDGET_USD).toFixed(2)}
                    </div>
                ) : computed.isNearBudget ? (
                    <div className="text-xs text-amber-400">
                        ΓÜá ${computed.remaining.toFixed(2)} remaining
                    </div>
                ) : (
                    <div className="text-xs text-text-secondary">
                        ${computed.remaining.toFixed(2)} remaining
                    </div>
                )}
            </div>

            {/* ACTUAL SPEND ROW */}
            {creditData || creditLoading ? (
                <div className="flex justify-between items-center mt-3">
                    <div>
                        <div className="flex items-center gap-2">
                            <div className="text-xs text-text-secondary">Actual spend this month</div>
                            {creditLoading ? <Loader2 size={12} className="animate-spin text-text-muted" /> : null}
                        </div>
                        <div className="text-xs text-text-muted">
                            {creditData ? `${creditData.run_count_mtd} runs completed` : "Loading spend..."}
                        </div>
                    </div>
                    <div className="text-right">
                        <div className="text-sm font-semibold text-text-primary">
                            ${creditData ? creditData.total_actual_spend_usd.toFixed(2) : "0.00"}
                        </div>
                        {actualDiff ? (
                            <div className={cn("text-xs", actualDiff.dir === "under" ? "text-green-500" : "text-amber-400")}>
                                {actualDiff.dir === "under"
                                    ? `Γåô $${actualDiff.value.toFixed(2)} under estimate`
                                    : `Γåæ $${actualDiff.value.toFixed(2)} over estimate`}
                            </div>
                        ) : null}
                    </div>
                </div>
            ) : null}

            {/* STATUS BANNER */}
            {computed.isNearBudget || computed.isOverBudget ? (
                <div
                    className={cn(
                        "mt-3 rounded-lg px-4 py-2.5 flex items-center gap-2 border",
                        computed.isOverBudget
                            ? "bg-red-500/10 border-red-500/20"
                            : "bg-amber-400/10 border-amber-400/20"
                    )}
                >
                    <AlertTriangle
                        size={14}
                        className={cn(computed.isOverBudget ? "text-red-500" : "text-amber-400")}
                    />
                    <div className={cn("text-xs", computed.isOverBudget ? "text-red-500" : "text-amber-400")}>
                        {computed.isOverBudget ? (
                            <>
                                Budget exceeded. Some scrapers may not run. Pause scrapers until you're back under ${MONTHLY_BUDGET_USD}.
                            </>
                        ) : (
                            <>
                                You're using {formatPct(computed.pctUsed)}% of your ${MONTHLY_BUDGET_USD} budget. Pause or reduce scrapers to stay within limits.
                            </>
                        )}
                    </div>
                </div>
            ) : null}

            {/* BREAKDOWN TABLE */}
            <div className="mt-4 pt-4 border-t border-border-subtle">
                <div className="text-xs font-medium text-text-secondary uppercase tracking-widest mb-3">
                    Active scraper costs
                </div>

                {computed.rows.length === 0 ? (
                    <div className="text-center text-xs text-text-muted py-6">No active scrapers</div>
                ) : (
                    <div className="space-y-2">
                        {computed.rows.map(({ actor, cappedCost, isCapped }) => {
                            const sharePct = Math.min((cappedCost / MONTHLY_BUDGET_USD) * 100, 100);
                            const actual = actualByActorId[actor.id] ?? 0;
                            return (
                                <div key={actor.id} className="flex justify-between items-center">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <span
                                            className={cn(
                                                "text-xs px-2 py-0.5 rounded-full border",
                                                platformBadgeClass(actor.platform)
                                            )}
                                        >
                                            {platformLabel(actor.platform)}
                                        </span>
                                        <div className="max-w-[180px] truncate text-sm text-text-primary">
                                            {actor.actor_name}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-3 shrink-0">
                                        <div className="w-16 h-1.5 bg-bg-elevated rounded-full overflow-hidden">
                                            <div
                                                className={cn("h-full rounded-full", fillClass)}
                                                style={{ width: `${sharePct}%` }}
                                            />
                                        </div>
                                        <div className="flex items-start gap-2">
                                            <div className="text-right">
                                                <div className="text-sm font-medium text-text-primary">
                                                    ${cappedCost.toFixed(2)}/mo
                                                </div>
                                                <div className="text-[10px] text-text-muted">
                                                    actual: ${actual.toFixed(2)}
                                                </div>
                                            </div>
                                            {isCapped ? (
                                                <span className="text-[10px] text-text-muted bg-bg-elevated px-1.5 py-0.5 rounded border border-border-subtle">
                                                    capped
                                                </span>
                                            ) : null}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* FOOTER ROW */}
                <div className="mt-4 pt-3 border-t border-border-subtle flex justify-between items-center">
                    <div className="text-xs text-text-muted">Per-config cap: ${PER_CONFIG_CAP_USD.toFixed(2)}/mo</div>
                    <div className={cn("flex items-center gap-1 text-xs", computed.isOverBudget ? "text-red-500" : "text-green-500")}>
                        <CheckCircle2 size={12} />
                        <span>{computed.isOverBudget ? "Over budget" : "Within budget"}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

