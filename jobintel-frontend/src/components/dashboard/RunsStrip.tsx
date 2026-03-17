import { useQuery } from "@tanstack/react-query";
import { getRunsToday } from "../../services/api/runs";
import { Card } from "../ui/Card";

interface RunItem {
    id: string;
    actor_name: string;
    platform: string;
    status: "success" | "running" | "failed";
    total_new: number;
}

export function RunsStrip() {
    const { data: runs, isLoading, isError } = useQuery<RunItem[]>({
        queryKey: ["runsToday"],
        queryFn: getRunsToday,
    });

    const getStatusDisplay = (status: RunItem["status"]) => {
        switch (status) {
            case "success":
                return <span className="text-text-success flex items-center gap-1"><span className="text-lg leading-none">✔</span> Success</span>;
            case "running":
                return <span className="text-text-info flex items-center gap-1"><span className="text-lg leading-none">⏳</span> Running</span>;
            case "failed":
                return <span className="text-text-error flex items-center gap-1"><span className="text-lg leading-none">✖</span> Failed</span>;
            default:
                return null;
        }
    };

    return (
        <Card className="w-full">
            <div className="mb-2">
                <h3 className="text-[16px] font-semibold text-text-primary">Runs Today</h3>
            </div>
            <div className="overflow-x-auto">
                {isLoading ? (
                    <div className="py-2 text-center text-text-secondary animate-pulse">
                        Loading runs...
                    </div>
                ) : isError ? (
                    <div className="py-2 text-center text-text-error">
                        Failed to load run data
                    </div>
                ) : runs && runs.length > 0 ? (
                    <div className="flex gap-6 whitespace-nowrap overflow-x-auto pb-2 items-center">
                        {runs.map((run, index) => (
                            <div key={run.id || index} className="flex gap-4 items-center bg-bg-base px-4 py-2 rounded-md border border-border-subtle shrink-0">
                                <span className="font-medium text-text-primary">
                                    {run.actor_name || run.platform || "Automated Scraper"}
                                </span>
                                <span className="text-[14px]">{getStatusDisplay(run.status)}</span>
                                {run.status === "success" && (
                                    <span className="text-[14px] text-text-secondary">{run.total_new} jobs</span>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="py-2 text-center text-text-secondary">
                        No runs today yet
                    </div>
                )}
            </div>
        </Card>
    );
}
