import { useQuery } from "@tanstack/react-query";
import { getRunsHealth } from "../../services/api/runs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/Table";
import { Card } from "../ui/Card";
import { cn } from "../ui/Card";

export function RunsHealthPanel() {
    const { data, isLoading, error } = useQuery({
        queryKey: ['runs-health'],
        queryFn: getRunsHealth,
        refetchInterval: 60000, // Refresh every minute
    });

    if (isLoading) {
        return (
            <Card className="animate-pulse flex flex-col items-center justify-center p-8 text-text-secondary min-h-[200px]">
                Loading system health...
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="flex flex-col items-center justify-center p-8 text-status-error bg-status-error/5 min-h-[200px]">
                Failed to load system health.
            </Card>
        );
    }

    const healthData = data?.data || [];

    // Sort array so that failing platforms appear at the top
    const sortedData = [...healthData].sort((a, b) => {
        const aHealthy = a.last_run === a.last_success;
        const bHealthy = b.last_run === b.last_success;
        if (aHealthy === bHealthy) return 0;
        return aHealthy ? 1 : -1;
    });

    return (
        <Card className="flex flex-col gap-4">
            <div>
                <h2 className="text-xl font-bold text-text-primary">System Scraping Health</h2>
                <p className="text-sm text-text-secondary">Monitor the operational status of all platform scrapers.</p>
            </div>

            <div className="overflow-auto border rounded-sm border-border-default">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="bg-bg-elevated">Actor / Platform</TableHead>
                            <TableHead className="bg-bg-elevated">Last Run</TableHead>
                            <TableHead className="bg-bg-elevated">Last Success</TableHead>
                            <TableHead className="bg-bg-elevated">Status</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {sortedData.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center text-text-secondary py-8">
                                    No system health data available.
                                </TableCell>
                            </TableRow>
                        ) : (
                            sortedData.map((health) => {
                                const isHealthy = health.last_run === health.last_success && health.last_run !== null;
                                const isUnknown = health.last_run === null;

                                return (
                                    <TableRow key={health.actor_id}>
                                        <TableCell className="font-medium">
                                            <div>{health.platform}</div>
                                            <div className="text-xs text-text-muted font-normal mt-0.5 max-w-[200px] truncate" title={health.actor_id}>
                                                {health.actor_id}
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-text-secondary">
                                            {health.last_run ? new Date(health.last_run).toLocaleString() : 'Never'}
                                        </TableCell>
                                        <TableCell className="text-text-secondary">
                                            {health.last_success ? new Date(health.last_success).toLocaleString() : 'Never'}
                                        </TableCell>
                                        <TableCell>
                                            <div className={cn(
                                                "inline-flex items-center justify-center px-2 py-1 rounded text-xs font-semibold w-20",
                                                isUnknown ? "bg-bg-elevated text-text-secondary" :
                                                    isHealthy ? "bg-status-success/10 text-status-success" :
                                                        "bg-status-warning/10 text-status-warning"
                                            )}>
                                                {isUnknown ? 'Unknown' : isHealthy ? 'Healthy' : 'Warning'}
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                );
                            })
                        )}
                    </TableBody>
                </Table>
            </div>
        </Card>
    );
}
