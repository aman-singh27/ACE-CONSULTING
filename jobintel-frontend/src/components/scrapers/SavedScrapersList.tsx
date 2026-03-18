import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Clock, Loader2, MapPin, Play, Trash2 } from "lucide-react";
import type { ActorItem } from "../actors/ActorTable";
import { getActors, triggerActor, updateActor } from "../../services/api/actors";
import { Button } from "../ui/Button";
import { cn } from "../ui/Card";

const DELETED_IDS_STORAGE_KEY = "jobintel.scrapers.deletedIds";

function loadDeletedIdsFromStorage(): Set<string> {
    try {
        const raw = window.localStorage.getItem(DELETED_IDS_STORAGE_KEY);
        if (!raw) return new Set();
        const parsed: unknown = JSON.parse(raw);
        if (!Array.isArray(parsed)) return new Set();
        return new Set(parsed.filter((v) => typeof v === "string"));
    } catch {
        return new Set();
    }
}

function persistDeletedIdsToStorage(ids: Set<string>) {
    try {
        window.localStorage.setItem(DELETED_IDS_STORAGE_KEY, JSON.stringify(Array.from(ids)));
    } catch {
        // ignore storage quota / disabled storage
    }
}

export interface SavedScrapersListProps {
    refreshTrigger: number;
}

type TriggerStatus = "idle" | "pending" | "success" | "error";

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

function displayLocation(loc: string) {
    if (loc === "KSA") return "Saudi Arabia";
    return loc;
}

function capitalizeDomain(domain: string) {
    const cleaned = domain.replace(/[-_]+/g, " ").trim();
    if (!cleaned) return "ΓÇö";
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function humanFrequency(frequencyDays: number) {
    if (frequencyDays === 1) return "Daily";
    if (frequencyDays === 2) return "Every 2 days";
    if (frequencyDays === 3) return "Every 3 days";
    if (frequencyDays === 7) return "Weekly";
    return `Every ${frequencyDays} days`;
}

function formatLastRun(lastRunAt: string | null | undefined) {
    if (!lastRunAt) return "Never run";
    const date = new Date(lastRunAt);
    const diffMs = Date.now() - date.getTime();
    if (Number.isNaN(diffMs)) return "Never run";

    const minutes = Math.floor(diffMs / (1000 * 60));
    if (minutes < 60) return "Just now";

    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    if (hours < 24) return `${hours} hours ago`;

    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    if (days < 7) return `${days} days ago`;

    return date.toLocaleDateString();
}

function SkeletonCard() {
    return (
        <div className="bg-bg-surface border border-border-subtle rounded-xl p-5 animate-pulse">
            <div className="flex items-start justify-between">
                <div className="space-y-2">
                    <div className="h-5 w-20 rounded bg-bg-elevated" />
                    <div className="h-5 w-64 rounded bg-bg-elevated" />
                </div>
                <div className="h-6 w-20 rounded bg-bg-elevated" />
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
                <div className="h-4 w-40 rounded bg-bg-elevated" />
                <div className="h-4 w-24 rounded bg-bg-elevated" />
                <div className="h-4 w-28 rounded bg-bg-elevated" />
            </div>
            <div className="mt-5 pt-4 border-t border-border-subtle flex items-center justify-between">
                <div className="h-4 w-32 rounded bg-bg-elevated" />
                <div className="flex gap-2">
                    <div className="h-8 w-24 rounded bg-bg-elevated" />
                    <div className="h-8 w-8 rounded bg-bg-elevated" />
                </div>
            </div>
        </div>
    );
}

export function SavedScrapersList({ refreshTrigger }: SavedScrapersListProps) {
    const queryClient = useQueryClient();

    const [confirmingIds, setConfirmingIds] = useState<Set<string>>(() => new Set());
    const [deletedIds, setDeletedIds] = useState<Set<string>>(() => loadDeletedIdsFromStorage());

    const [triggerStatusById, setTriggerStatusById] = useState<Record<string, TriggerStatus>>({});
    const [togglePendingIds, setTogglePendingIds] = useState<Set<string>>(() => new Set());
    const [deletePendingIds, setDeletePendingIds] = useState<Set<string>>(() => new Set());

    const { data, isLoading, isError } = useQuery<ActorItem[]>({
        queryKey: ["actors"],
        queryFn: getActors,
    });

    useEffect(() => {
        queryClient.invalidateQueries({ queryKey: ["actors"] });
    }, [refreshTrigger, queryClient]);

    useEffect(() => {
        persistDeletedIdsToStorage(deletedIds);
    }, [deletedIds]);

    const actors = useMemo(() => {
        const list = data ?? [];
        return list.filter((a) => !deletedIds.has(a.id));
    }, [data, deletedIds]);

    const toggleMutation = useMutation({
        mutationFn: async (vars: { id: string; is_active: boolean }) => updateActor(vars.id, { is_active: vars.is_active }),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["actors"] }),
        onSettled: (_data, _err, vars) => {
            if (!vars) return;
            setTogglePendingIds((prev) => {
                const next = new Set(prev);
                next.delete(vars.id);
                return next;
            });
        },
    });

    const triggerMutation = useMutation({
        mutationFn: async (id: string) => triggerActor(id),
        onSuccess: (_data, id) => {
            setTriggerStatusById((prev) => ({ ...prev, [id]: "success" }));
            queryClient.invalidateQueries({ queryKey: ["actors"] });
            window.setTimeout(() => {
                setTriggerStatusById((prev) => ({ ...prev, [id]: "idle" }));
            }, 3000);
        },
        onError: (_err, id) => {
            setTriggerStatusById((prev) => ({ ...prev, [id]: "error" }));
            window.setTimeout(() => {
                setTriggerStatusById((prev) => ({ ...prev, [id]: "idle" }));
            }, 3000);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: async (id: string) => updateActor(id, { is_active: false }),
        onSuccess: (_data, id) => {
            setDeletedIds((prev) => {
                const next = new Set(prev);
                next.add(id);
                return next;
            });
            setConfirmingIds((prev) => {
                const next = new Set(prev);
                next.delete(id);
                return next;
            });
            queryClient.invalidateQueries({ queryKey: ["actors"] });
        },
        onSettled: (_data, _err, id) => {
            setDeletePendingIds((prev) => {
                const next = new Set(prev);
                next.delete(id);
                return next;
            });
        },
    });

    const totalConfigured = actors.length;

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <div className="text-lg font-semibold text-text-primary">Your Scrapers</div>
                <div className="text-xs text-text-secondary bg-bg-elevated px-2 py-0.5 rounded-full border border-border-subtle">
                    {totalConfigured} configured
                </div>
            </div>

            {isLoading ? (
                <div className="space-y-3">
                    <SkeletonCard />
                    <SkeletonCard />
                    <SkeletonCard />
                </div>
            ) : isError ? (
                <div className="py-10 text-center text-red-500">
                    Failed to load scrapers.
                </div>
            ) : actors.length === 0 ? (
                <div className="border border-dashed border-border-subtle rounded-xl p-10 bg-bg-base text-center">
                    <div className="text-text-secondary">
                        No scrapers set up yet. Create your first one above.
                    </div>
                </div>
            ) : (
                <div className="space-y-3">
                    {actors.map((actor) => {
                        const isConfirming = confirmingIds.has(actor.id);
                        const triggerStatus = triggerStatusById[actor.id] ?? "idle";
                        const isTriggering = triggerStatus === "pending";
                        const isTogglePending = togglePendingIds.has(actor.id);
                        const isDeleting = deletePendingIds.has(actor.id);

                        const locations = (actor.locations ?? []).map(displayLocation);
                        const locationsLabel = locations.length > 0 ? locations.join(", ") : "ΓÇö";

                        return (
                            <div
                                key={actor.id}
                                className="bg-bg-surface border border-border-subtle rounded-xl p-5"
                            >
                                {/* ROW 1 ΓÇö Header row */}
                                <div className="flex justify-between items-start gap-4">
                                    <div className="min-w-0">
                                        <div
                                            className={cn(
                                                "inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full",
                                                platformBadgeClass(actor.platform)
                                            )}
                                        >
                                            {platformLabel(actor.platform)}
                                        </div>
                                        <div className="text-base font-semibold text-text-primary mt-1 truncate">
                                            {actor.actor_name}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 shrink-0">
                                        <button
                                            type="button"
                                            onClick={() => {
                                                if (isTogglePending || isDeleting) return;
                                                setTogglePendingIds((prev) => new Set(prev).add(actor.id));
                                                toggleMutation.mutate({ id: actor.id, is_active: !actor.is_active });
                                            }}
                                            className={cn(
                                                "relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/50",
                                                actor.is_active ? "bg-green-500" : "bg-bg-elevated"
                                            )}
                                            aria-label={actor.is_active ? "Pause scraper" : "Activate scraper"}
                                        >
                                            <span
                                                className={cn(
                                                    "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                                                    actor.is_active ? "translate-x-6" : "translate-x-1"
                                                )}
                                            />
                                        </button>
                                        <span
                                            className={cn(
                                                "text-xs",
                                                actor.is_active ? "text-green-500" : "text-text-muted"
                                            )}
                                        >
                                            {actor.is_active ? "Active" : "Paused"}
                                        </span>
                                    </div>
                                </div>

                                {/* ROW 2 ΓÇö Meta chips */}
                                <div className="flex gap-3 mt-3 flex-wrap">
                                    <div className="flex items-center gap-1 text-xs text-text-secondary">
                                        <MapPin size={12} className="text-text-muted" />
                                        <span>{locationsLabel}</span>
                                    </div>
                                    <div className="flex items-center gap-1 text-xs text-text-secondary">
                                        <Briefcase size={12} className="text-text-muted" />
                                        <span>{capitalizeDomain(actor.domain)}</span>
                                    </div>
                                    <div className="flex items-center gap-1 text-xs text-text-secondary">
                                        <Clock size={12} className="text-text-muted" />
                                        <span>{humanFrequency(actor.frequency_days)}</span>
                                    </div>
                                </div>

                                {/* ROW 3 ΓÇö Footer row */}
                                <div className="flex justify-between items-center mt-4 pt-4 border-t border-border-subtle gap-4">
                                    <div className="text-xs text-text-muted">
                                        Last run: {formatLastRun(actor.last_run_at)}
                                    </div>

                                    <div className="shrink-0">
                                        {isConfirming ? (
                                            <div className="flex items-center gap-3">
                                                <div className="text-sm text-text-secondary">Delete this scraper?</div>
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setConfirmingIds((prev) => {
                                                            const next = new Set(prev);
                                                            next.delete(actor.id);
                                                            return next;
                                                        });
                                                    }}
                                                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                                                    disabled={isDeleting}
                                                >
                                                    Cancel
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        if (isDeleting) return;
                                                        setDeletePendingIds((prev) => new Set(prev).add(actor.id));
                                                        deleteMutation.mutate(actor.id);
                                                    }}
                                                    className="text-sm text-red-500 hover:text-red-500/80 transition-colors"
                                                    disabled={isDeleting}
                                                >
                                                    {isDeleting ? "Deleting..." : "Yes, delete"}
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-2">
                                                {triggerStatus === "success" ? (
                                                    <span className="text-xs font-medium px-2 py-1 rounded text-green-500 bg-green-500/10">
                                                        Triggered Γ£ô
                                                    </span>
                                                ) : triggerStatus === "error" ? (
                                                    <span className="text-xs font-medium px-2 py-1 rounded text-red-500 bg-red-500/10">
                                                        Failed Γ£ù
                                                    </span>
                                                ) : (
                                                    <Button
                                                        type="button"
                                                        onClick={() => {
                                                            setTriggerStatusById((prev) => ({ ...prev, [actor.id]: "pending" }));
                                                            triggerMutation.mutate(actor.id);
                                                        }}
                                                        disabled={!actor.is_active || isTriggering}
                                                        className="h-8 px-3 text-xs gap-1.5"
                                                    >
                                                        {isTriggering ? (
                                                            <>
                                                                <Loader2 size={14} className="animate-spin" />
                                                                Running...
                                                            </>
                                                        ) : (
                                                            <>
                                                                <Play size={14} />
                                                                Run Now
                                                            </>
                                                        )}
                                                    </Button>
                                                )}

                                                <button
                                                    type="button"
                                                    onClick={() => {
                                                        setConfirmingIds((prev) => {
                                                            const next = new Set(prev);
                                                            next.add(actor.id);
                                                            return next;
                                                        });
                                                    }}
                                                    className="h-8 w-8 p-0 bg-bg-elevated border border-border-subtle text-text-muted hover:text-red-500 hover:border-red-500/30 transition-colors rounded-md inline-flex items-center justify-center"
                                                    aria-label="Delete scraper"
                                                    disabled={isDeleting}
                                                >
                                                    <Trash2 size={14} />
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

