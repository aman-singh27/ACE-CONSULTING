import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "../ui/Button";
import { cn } from "../ui/Card";
import { createActor } from "../../services/api/actors";

export interface ScraperSetupFormProps {
    onSuccess?: () => void;
}

const MONTHLY_BUDGET = 29;
const COST_PER_1K_JOBS = 1.0;

const PLATFORM_ACTOR_MAP = {
    linkedin: "cheap_scraper/linkedin-job-scraper",
    bayt: "shahidirfan/bayt-jobs-scraper",
    naukrigulf: "shahidirfan/nukrigulf-job-scraper",
} as const;

type PlatformKey = keyof typeof PLATFORM_ACTOR_MAP;

const PLATFORM_OPTIONS: Array<{
    key: PlatformKey;
    label: string;
    subtitle: string;
}> = [
    { key: "linkedin", label: "LinkedIn", subtitle: "Global coverage" },
    { key: "bayt", label: "Bayt", subtitle: "MENA focused" },
    { key: "naukrigulf", label: "NaukriGulf", subtitle: "Gulf + South Asia" },
];

const MARKET_PILLS = [
    "UAE",
    "Saudi Arabia",
    "Qatar",
    "Kuwait",
    "Bahrain",
    "India",
    "Egypt",
    "Jordan",
] as const;

const INDUSTRY_PILLS = [
    "Logistics",
    "Fintech",
    "Healthcare",
    "Manufacturing",
    "Retail",
    "Real Estate",
    "E-commerce",
    "FMCG",
    "Pharma",
    "Tech",
] as const;

const SCHEDULE_OPTIONS: Array<{
    frequencyDays: number;
    label: string;
    subtitle: string;
}> = [
    { frequencyDays: 1, label: "Daily", subtitle: "~30 runs/mo" },
    { frequencyDays: 2, label: "Every 2 days", subtitle: "~15 runs/mo" },
    { frequencyDays: 3, label: "Every 3 days", subtitle: "~10 runs/mo" },
    { frequencyDays: 7, label: "Weekly", subtitle: "~4 runs/mo" },
];

function slugifyDomain(label: string) {
    return label
        .toLowerCase()
        .replace(/&/g, "and")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
}

function truncate(str: string, maxLen: number) {
    if (str.length <= maxLen) return str;
    return `${str.slice(0, Math.max(0, maxLen - 1)).trimEnd()}ΓÇª`;
}

function displayMarket(market: string) {
    if (market === "Saudi Arabia") return "KSA";
    return market;
}

export function ScraperSetupForm({ onSuccess }: ScraperSetupFormProps) {
    const [platform, setPlatform] = useState<PlatformKey>("linkedin");
    const [markets, setMarkets] = useState<string[]>(["UAE"]);
    const [industries, setIndustries] = useState<string[]>(["Logistics"]);
    const [jobsPerRun, setJobsPerRun] = useState<number>(200);
    const [frequencyDays, setFrequencyDays] = useState<number>(2);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const runsPerMonth = useMemo(() => Math.round(30 / frequencyDays), [frequencyDays]);
    const monthlyCost = useMemo(() => (jobsPerRun * runsPerMonth / 1000) * COST_PER_1K_JOBS, [jobsPerRun, runsPerMonth]);
    const budgetUsed = useMemo(() => (monthlyCost / MONTHLY_BUDGET), [monthlyCost]);

    const barColorClass = useMemo(() => {
        if (budgetUsed >= 1) return "bg-red-500";
        if (budgetUsed >= 0.7) return "bg-amber-400";
        return "bg-accent-primary";
    }, [budgetUsed]);

    const overBudget = monthlyCost > MONTHLY_BUDGET;

    const isValid =
        Boolean(platform) &&
        markets.length > 0 &&
        industries.length > 0 &&
        !overBudget;

    const summary = useMemo(() => {
        const platformLabel = PLATFORM_OPTIONS.find((p) => p.key === platform)?.label ?? "Platform";
        const marketsLabel = markets.map(displayMarket).join(", ");
        const industriesLabel = industries.join(", ");
        const scheduleLabel =
            SCHEDULE_OPTIONS.find((s) => s.frequencyDays === frequencyDays)?.label ?? `${frequencyDays} days`;
        return `${platformLabel} ┬╖ ${marketsLabel} ┬╖ ${industriesLabel} ΓÇö ${jobsPerRun} jobs ${scheduleLabel.toLowerCase()}`;
    }, [platform, markets, industries, jobsPerRun, frequencyDays]);

    const mutation = useMutation({
        mutationFn: async () => {
            const platformLabel = PLATFORM_OPTIONS.find((p) => p.key === platform)?.label ?? platform;
            const marketsLabel = markets.map(displayMarket).join(", ");
            const actorNameRaw = `${platformLabel} ΓÇô ${marketsLabel} ΓÇô ${industries[0] ?? "Industry"}`;

            const payload = {
                actor_id: PLATFORM_ACTOR_MAP[platform],
                actor_name: truncate(actorNameRaw, 80),
                platform,
                domain: slugifyDomain(industries[0] ?? "general"),
                frequency_days: frequencyDays,
                apify_input_template: {
                    markets: markets.map(displayMarket),
                    industries,
                    jobsPerRun,
                },
                normalizer_key: platform,
                keywords: industries.map((i) => i.toLowerCase()),
                locations: markets.map(displayMarket),
                monthly_budget_usd: MONTHLY_BUDGET,
            };

            return createActor(payload);
        },
        onMutate: () => {
            setErrorMsg(null);
        },
        onSuccess: () => {
            onSuccess?.();
        },
        onError: (err) => {
            const message = err instanceof Error ? err.message : "Failed to save scraper.";
            setErrorMsg(message);
        },
    });

    function toggleMulti(value: string, list: string[], setList: (v: string[]) => void) {
        const exists = list.includes(value);
        if (exists) {
            const next = list.filter((v) => v !== value);
            setList(next);
            return;
        }
        setList([...list, value]);
    }

    return (
        <form
            className="rounded-[10px] border border-border-subtle bg-bg-surface p-6"
            onSubmit={(e) => {
                e.preventDefault();
                if (!isValid || mutation.isPending) return;
                mutation.mutate();
            }}
        >
            <div className="space-y-8">
                {/* SECTION 1 ΓÇö Platform */}
                <section>
                    <div className="mb-3">
                        <div className="text-sm font-semibold text-text-primary">Platform</div>
                        <div className="text-xs text-text-muted mt-0.5">Choose where you want to source jobs.</div>
                    </div>
                    <div className="grid grid-cols-3 gap-3">
                        {PLATFORM_OPTIONS.map((opt) => {
                            const active = platform === opt.key;
                            return (
                                <button
                                    key={opt.key}
                                    type="button"
                                    onClick={() => {
                                        if (active) return;
                                        setPlatform(opt.key);
                                    }}
                                    className={cn(
                                        "rounded-[10px] border bg-bg-base p-4 text-left transition-colors",
                                        active
                                            ? "border-2 border-accent-primary bg-accent-primary/5"
                                            : "border-border-subtle hover:bg-bg-elevated"
                                    )}
                                >
                                    <div className="flex items-start gap-3">
                                        <span
                                            className={cn(
                                                "mt-1 h-2 w-2 rounded-full",
                                                active ? "bg-accent-primary" : "bg-border-secondary"
                                            )}
                                            aria-hidden="true"
                                        />
                                        <div>
                                            <div className="font-semibold text-text-primary">{opt.label}</div>
                                            <div className="text-xs text-text-secondary mt-0.5">{opt.subtitle}</div>
                                        </div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
                </section>

                {/* SECTION 2 ΓÇö Market */}
                <section>
                    <div className="mb-3">
                        <div className="text-sm font-semibold text-text-primary">Market</div>
                        <div className="text-xs text-text-muted mt-0.5">Pick one or more target geographies.</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {MARKET_PILLS.map((m) => {
                            const active = markets.includes(m);
                            return (
                                <button
                                    key={m}
                                    type="button"
                                    onClick={() => toggleMulti(m, markets, setMarkets)}
                                    className={cn(
                                        "rounded-full border px-3 py-1.5 text-sm transition-colors",
                                        active
                                            ? "bg-accent-primary/10 border-accent-primary text-accent-primary font-medium"
                                            : "bg-bg-elevated border-border-subtle text-text-secondary hover:bg-bg-base"
                                    )}
                                >
                                    {m === "Saudi Arabia" ? "Saudi Arabia (KSA)" : m}
                                </button>
                            );
                        })}
                    </div>
                    {markets.length === 0 ? (
                        <div className="text-xs text-red-400 mt-2">Select at least one market.</div>
                    ) : null}
                </section>

                {/* SECTION 3 ΓÇö Industry */}
                <section>
                    <div className="mb-3">
                        <div className="text-sm font-semibold text-text-primary">Industry</div>
                        <div className="text-xs text-text-muted mt-0.5">Choose the industries you care about.</div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {INDUSTRY_PILLS.map((ind) => {
                            const active = industries.includes(ind);
                            return (
                                <button
                                    key={ind}
                                    type="button"
                                    onClick={() => toggleMulti(ind, industries, setIndustries)}
                                    className={cn(
                                        "rounded-full border px-3 py-1.5 text-sm transition-colors",
                                        active
                                            ? "bg-green-500/10 border-green-500/30 text-green-400 font-medium"
                                            : "bg-bg-elevated border-border-subtle text-text-secondary hover:bg-bg-base"
                                    )}
                                >
                                    {ind}
                                </button>
                            );
                        })}
                    </div>
                    {industries.length === 0 ? (
                        <div className="text-xs text-red-400 mt-2">Select at least one industry.</div>
                    ) : null}
                </section>

                {/* SECTION 4 ΓÇö Jobs per run */}
                <section>
                    <div className="mb-3 flex items-center justify-between">
                        <div>
                            <div className="text-sm font-semibold text-text-primary">Jobs per run</div>
                            <div className="text-xs text-text-muted mt-0.5">How many jobs to fetch each run.</div>
                        </div>
                        <div className="text-sm font-medium text-text-secondary">{jobsPerRun} jobs</div>
                    </div>
                    <input
                        type="range"
                        min={50}
                        max={500}
                        step={50}
                        value={jobsPerRun}
                        onChange={(e) => setJobsPerRun(Number(e.target.value))}
                        className="w-full accent-accent-primary"
                    />
                </section>

                {/* SECTION 5 ΓÇö Schedule */}
                <section>
                    <div className="mb-3">
                        <div className="text-sm font-semibold text-text-primary">Schedule</div>
                        <div className="text-xs text-text-muted mt-0.5">How often should it run?</div>
                    </div>
                    <div className="grid grid-cols-4 gap-3">
                        {SCHEDULE_OPTIONS.map((opt) => {
                            const active = frequencyDays === opt.frequencyDays;
                            return (
                                <button
                                    key={opt.frequencyDays}
                                    type="button"
                                    onClick={() => setFrequencyDays(opt.frequencyDays)}
                                    className={cn(
                                        "rounded-[10px] border bg-bg-base p-4 text-left transition-colors",
                                        active
                                            ? "border-2 border-green-500/60 bg-green-500/5"
                                            : "border-border-subtle hover:bg-bg-elevated"
                                    )}
                                >
                                    <div className={cn("font-semibold", active ? "text-green-400" : "text-text-primary")}>
                                        {opt.label}
                                    </div>
                                    <div className="text-xs text-text-secondary mt-0.5">{opt.subtitle}</div>
                                </button>
                            );
                        })}
                    </div>
                </section>

                {/* SECTION 6 ΓÇö Cost estimate bar */}
                <section className="rounded-[10px] border border-border-subtle bg-bg-base p-4">
                    <div className="h-1.5 w-full rounded bg-bg-elevated overflow-hidden">
                        <div
                            className={cn("h-full rounded", barColorClass)}
                            style={{ width: `${Math.min(100, Math.max(0, budgetUsed * 100))}%` }}
                        />
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-4">
                        <div className="text-sm text-text-secondary">
                            <span className="text-text-muted">Est. cost this config</span>{" "}
                            <span className="text-text-primary font-semibold">${monthlyCost.toFixed(2)} / mo</span>
                        </div>
                        <div className="text-sm text-text-secondary">
                            <span className="text-text-muted">Budget remaining</span>{" "}
                            <span className={cn("font-semibold", overBudget ? "text-red-400" : "text-text-primary")}>
                                ${Math.max(0, MONTHLY_BUDGET - monthlyCost).toFixed(2)}
                            </span>
                        </div>
                    </div>
                    {overBudget ? (
                        <div className="mt-2 text-xs text-red-400">
                            This config exceeds your ${MONTHLY_BUDGET} monthly budget. Reduce frequency or jobs.
                        </div>
                    ) : null}
                </section>

                {/* SECTION 7 ΓÇö Summary + Save */}
                <section>
                    <div className="text-sm text-text-secondary">{summary}</div>
                    <div className="mt-3">
                        <Button
                            type="submit"
                            disabled={!isValid || mutation.isPending}
                            className="w-full h-10"
                        >
                            {mutation.isPending ? "Saving..." : "Save Scraper"}
                        </Button>
                        {errorMsg ? <div className="mt-2 text-xs text-red-400">{errorMsg}</div> : null}
                    </div>
                </section>
            </div>
        </form>
    );
}

