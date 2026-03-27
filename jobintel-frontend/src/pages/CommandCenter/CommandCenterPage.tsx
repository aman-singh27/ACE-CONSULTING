import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getDashboardSummary } from "../../services/api/dashboard";
import { KpiCard } from "../../components/ui/KpiCard";
import { PriorityList } from "../../components/dashboard/PriorityList";
import { AlertsPanel } from "../../components/dashboard/AlertsPanel";
import { RunsStrip } from "../../components/dashboard/RunsStrip";

interface DashboardSummary {
    jobs_scraped_today: number;
    new_companies_today: number;
    active_actors: number;
    bd_alerts: number;
}

export function CommandCenterPage() {
    const navigate = useNavigate();
    const { data: summary, isLoading, isError } = useQuery<DashboardSummary>({
        queryKey: ["dashboardSummary"],
        queryFn: getDashboardSummary,
    });

    if (isError) {
        return (
            <div className="flex items-center justify-center p-8 text-text-error">
                Failed to load dashboard data
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="mb-6">
                <h1 className="text-2xl font-bold text-text-primary">Command Center</h1>
                <p className="text-text-secondary">Hiring Intelligence Overview</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <KpiCard
                    label="Jobs scraped today"
                    metric={summary?.jobs_scraped_today ?? 0}
                    loading={isLoading}
                />
                <KpiCard
                    label="New companies today"
                    metric={summary?.new_companies_today ?? 0}
                    loading={isLoading}
                    onClick={() => navigate("/companies")}
                />
                <KpiCard
                    label="Active actors"
                    metric={summary?.active_actors ?? 0}
                    loading={isLoading}
                />
                <KpiCard
                    label="BD alerts"
                    metric={summary?.bd_alerts ?? 0}
                    loading={isLoading}
                />
            </div>

            <div className="grid gap-6 md:grid-cols-2 h-[400px]">
                <PriorityList />
                <AlertsPanel />
            </div>

            <div className="w-full">
                <RunsStrip />
            </div>
        </div>
    );
}
