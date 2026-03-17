import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getActors, triggerActor, updateActor } from "../../services/api/actors";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/Table";
import { Button } from "../ui/Button";
import { Play, Loader2 } from "lucide-react";
import { useState } from "react";

export interface ActorItem {
    id: string;
    actor_id: string;
    actor_name: string;
    platform: string;
    domain: string;
    frequency_days: number;
    is_active: boolean;
    monthly_budget_usd: number | null;
    normalizer_key: string | null;
    apify_input_template: Record<string, unknown> | null;
    keywords: string[] | null;
    locations: string[] | null;
    last_run_at: string | null;
    created_at: string;
}

interface ActorTableProps {
    onEdit: (actor: ActorItem) => void;
}

export function ActorTable({ onEdit }: ActorTableProps) {
    const queryClient = useQueryClient();
    const [triggeringId, setTriggeringId] = useState<string | null>(null);
    const [triggerResult, setTriggerResult] = useState<Record<string, string>>({});

    const { data: actors = [], isLoading, isError } = useQuery<ActorItem[]>({
        queryKey: ["actors"],
        queryFn: getActors,
    });

    const triggerMutation = useMutation({
        mutationFn: (id: string) => triggerActor(id),
        onMutate: (id) => setTriggeringId(id),
        onSuccess: (_data, id) => {
            setTriggeringId(null);
            setTriggerResult(prev => ({ ...prev, [id]: "Run triggered ✓" }));
            setTimeout(() => {
                setTriggerResult(prev => {
                    const next = { ...prev };
                    delete next[id];
                    return next;
                });
            }, 3000);
            queryClient.invalidateQueries({ queryKey: ["actors"] });
        },
        onError: (_err, id) => {
            setTriggeringId(null);
            setTriggerResult(prev => ({ ...prev, [id]: "Failed ✗" }));
            setTimeout(() => {
                setTriggerResult(prev => {
                    const next = { ...prev };
                    delete next[id];
                    return next;
                });
            }, 3000);
        },
    });

    const toggleMutation = useMutation({
        mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
            updateActor(id, { is_active }),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["actors"] }),
    });

    const formatDate = (dateString: string | null) => {
        if (!dateString) return "Never";
        const date = new Date(dateString);
        const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
        const hoursDiff = Math.round((date.getTime() - Date.now()) / (1000 * 60 * 60));
        if (hoursDiff === 0) return "Just now";
        if (hoursDiff > -24) return rtf.format(hoursDiff, "hour");
        const daysDiff = Math.round(hoursDiff / 24);
        if (daysDiff > -7) return rtf.format(daysDiff, "day");
        return date.toLocaleDateString();
    };

    return (
        <div className="w-full bg-bg-surface rounded-card border border-border-subtle overflow-hidden">
            <Table>
                <TableHeader>
                    <TableRow>
                        <TableHead>Actor Name</TableHead>
                        <TableHead>Platform</TableHead>
                        <TableHead>Domain</TableHead>
                        <TableHead>Frequency</TableHead>
                        <TableHead>Last Run</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Actions</TableHead>
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {isLoading ? (
                        <TableRow>
                            <TableCell colSpan={7} className="text-center py-8 text-text-secondary animate-pulse">
                                Loading actors...
                            </TableCell>
                        </TableRow>
                    ) : isError ? (
                        <TableRow>
                            <TableCell colSpan={7} className="text-center py-8 text-text-error">
                                Failed to load actors
                            </TableCell>
                        </TableRow>
                    ) : actors.length > 0 ? (
                        actors.map((actor) => (
                            <TableRow key={actor.id}>
                                <TableCell className="font-medium text-text-primary">
                                    {actor.actor_name}
                                </TableCell>
                                <TableCell className="text-text-secondary capitalize">
                                    {actor.platform}
                                </TableCell>
                                <TableCell className="text-text-secondary capitalize">
                                    {actor.domain}
                                </TableCell>
                                <TableCell className="text-text-secondary">
                                    Every {actor.frequency_days}d
                                </TableCell>
                                <TableCell className="text-text-secondary text-sm whitespace-nowrap">
                                    {formatDate(actor.last_run_at)}
                                </TableCell>
                                <TableCell>
                                    <button
                                        onClick={() => toggleMutation.mutate({ id: actor.id, is_active: !actor.is_active })}
                                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-accent-primary/50 ${actor.is_active ? 'bg-green-500' : 'bg-bg-elevated'
                                            }`}
                                    >
                                        <span
                                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${actor.is_active ? 'translate-x-6' : 'translate-x-1'
                                                }`}
                                        />
                                    </button>
                                    <span className={`ml-2 text-xs font-medium ${actor.is_active ? 'text-green-500' : 'text-text-muted'}`}>
                                        {actor.is_active ? 'Active' : 'Paused'}
                                    </span>
                                </TableCell>
                                <TableCell>
                                    <div className="flex items-center gap-2">
                                        {triggerResult[actor.id] ? (
                                            <span className={`text-xs font-medium px-2 py-1 rounded ${triggerResult[actor.id].includes('✓')
                                                ? 'text-green-500 bg-green-500/10'
                                                : 'text-red-500 bg-red-500/10'
                                                }`}>
                                                {triggerResult[actor.id]}
                                            </span>
                                        ) : (
                                            <Button
                                                onClick={() => triggerMutation.mutate(actor.id)}
                                                disabled={triggeringId === actor.id || !actor.is_active}
                                                className="h-8 px-3 text-xs gap-1.5"
                                            >
                                                {triggeringId === actor.id ? (
                                                    <><Loader2 size={14} className="animate-spin" /> Running...</>
                                                ) : (
                                                    <><Play size={14} /> Run Now</>
                                                )}
                                            </Button>
                                        )}
                                        <button
                                            onClick={() => onEdit(actor)}
                                            className="text-xs text-text-secondary hover:text-text-primary transition-colors px-2 py-1 rounded hover:bg-bg-elevated"
                                        >
                                            Edit
                                        </button>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ))
                    ) : (
                        <TableRow>
                            <TableCell colSpan={7} className="text-center py-8 text-text-secondary">
                                No actors configured yet. Click "Create Actor" to get started.
                            </TableCell>
                        </TableRow>
                    )}
                </TableBody>
            </Table>
        </div>
    );
}
