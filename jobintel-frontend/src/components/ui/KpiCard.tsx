import { Card } from "./Card";

interface KpiCardProps {
    label: string;
    metric: number | string;
    loading?: boolean;
}

export function KpiCard({ label, metric, loading }: KpiCardProps) {
    return (
        <Card className="flex flex-col justify-center items-start gap-1 min-h-[100px]">
            {loading ? (
                <div className="animate-pulse flex flex-col gap-2 w-full">
                    <div className="h-6 bg-border-subtle rounded w-1/2"></div>
                    <div className="h-4 bg-border-subtle rounded w-3/4"></div>
                </div>
            ) : (
                <>
                    <div className="text-[20px] font-semibold text-text-primary leading-tight">
                        {metric}
                    </div>
                    <div className="text-[14px] text-text-secondary">
                        {label}
                    </div>
                </>
            )}
        </Card>
    );
}
