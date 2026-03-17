import { Card } from "../../components/ui/Card";
import { RunsHealthPanel } from "../../components/runs/RunsHealthPanel";

export function RunsPage() {
    return (
        <div className="space-y-6 flex flex-col h-full">
            <div className="shrink-0">
                <h1 className="text-3xl font-bold tracking-tight text-text-primary">Runs Monitor</h1>
                <p className="text-text-secondary mt-1">Monitor system scraping health and view run histories.</p>
            </div>

            <RunsHealthPanel />

            <Card className="min-h-[400px] flex flex-col items-center justify-center text-text-muted flex-grow">
                <h2 className="text-xl font-bold text-text-primary mb-2">Run History</h2>
                <p>Apify asynchronous pipeline statuses will appear here.</p>
            </Card>
        </div>
    );
}
