import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getPriorityList } from "../../services/api/dashboard";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";

interface PriorityItem {
    company_name: string;
    bd_tags: string[];
    total_postings_7d: number;
    bd_priority_score: number;
}

export function AlertsPanel() {
    const navigate = useNavigate();
    const { data: priorityItems, isLoading, isError } = useQuery<PriorityItem[]>({
        queryKey: ["priority"],
        queryFn: getPriorityList,
    });

    // Filter companies that have tags
    const alertCompanies = priorityItems?.filter(item => item.bd_tags && item.bd_tags.length > 0) || [];

    // Group by tag for display (Spiking, Struggling, New Entrant, etc)
    const groupedAlerts = alertCompanies.reduce((acc, item) => {
        item.bd_tags.forEach(tag => {
            if (!acc[tag]) {
                acc[tag] = [];
            }
            acc[tag].push(item.company_name);
        });
        return acc;
    }, {} as Record<string, string[]>);

    const getBadgeVariant = (tag: string) => {
        switch (tag.toLowerCase()) {
            case "spiking":
                return "spiking";
            case "struggling":
                return "struggling";
            case "new entrant":
                return "new";
            default:
                return "default";
        }
    };

    return (
        <Card className="flex flex-col h-full overflow-hidden">
            <div className="mb-4">
                <h3 className="text-[16px] font-semibold text-text-primary">Alerts Panel</h3>
                <p className="text-[14px] text-text-secondary">Key company events</p>
            </div>

            <div className="overflow-y-auto pr-2 space-y-4">
                {isLoading ? (
                    <div className="text-center py-4 text-text-secondary animate-pulse">
                        Loading alerts...
                    </div>
                ) : isError ? (
                    <div className="text-center py-4 text-text-error">
                        Failed to load alerts
                    </div>
                ) : Object.keys(groupedAlerts).length > 0 ? (
                    Object.entries(groupedAlerts).map(([tag, companies]) => (
                        <div key={tag} className="space-y-2">
                            <Badge variant={getBadgeVariant(tag)}>{tag}</Badge>
                            <div className="bg-bg-base rounded-md border border-border-subtle p-3 space-y-1">
                                {companies.map((company, idx) => (
                                    <div
                                        key={idx}
                                        onClick={() => navigate(`/companies?search=${encodeURIComponent(company)}`)}
                                        className="text-sm font-medium text-text-primary cursor-pointer hover:text-accent-primary transition-colors"
                                    >
                                        {company}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-4 text-text-secondary">
                        No active alerts
                    </div>
                )}
            </div>
        </Card>
    );
}
