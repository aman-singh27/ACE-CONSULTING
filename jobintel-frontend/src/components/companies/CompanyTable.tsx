import { useQuery } from "@tanstack/react-query";
import { getCompanies } from "../../services/api/companies";
import { Badge } from "../ui/Badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/Table";

interface CompanyItem {
    id: string;
    company_name: string;
    domains_active: string[];
    total_postings_7d: number;
    total_postings_30d: number;
    hiring_velocity_score: number;
    bd_tags: string[];
    last_active_at: string;
}

interface CompanyTableProps {
    filters: Record<string, any>;
    onRowClick: (company: CompanyItem) => void;
}

export function CompanyTable({ filters, onRowClick }: CompanyTableProps) {
    const { data: response, isLoading, isError } = useQuery<{ items: CompanyItem[], total: number }>({
        queryKey: ["companies", filters],
        queryFn: () => getCompanies({ ...filters, limit: 100 }), // Default to larger limit for table view
    });

    const companies = response?.items || [];

    const getBadgeVariant = (tag: string) => {
        switch (tag.toLowerCase()) {
            case "spiking":
                return "spiking";
            case "struggling":
                return "struggling";
            case "new entrant":
                return "new";
            case "salary signal":
                return "default"; // Reusing default for yellow as per spec later
            default:
                return "secondary";
        }
    };

    const formatDate = (dateString: string) => {
        if (!dateString) return "Never";
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    const formatVelocity = (score: number) => {
        if (score === 0) return "-";
        const prefix = score > 0 ? "+" : "";
        return `${prefix}${Math.round(score * 100)}%`;
    };

    return (
        <div className="w-full flex flex-col h-full bg-bg-surface rounded-card border border-border-subtle overflow-hidden">
            <div className="overflow-auto flex-grow">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Company</TableHead>
                            <TableHead>Domain</TableHead>
                            <TableHead className="text-right">7d Jobs</TableHead>
                            <TableHead className="text-right">30d Jobs</TableHead>
                            <TableHead className="text-right">Velocity</TableHead>
                            <TableHead>BD Tags</TableHead>
                            <TableHead>Last Active</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={7} className="text-center py-8 text-text-secondary animate-pulse">
                                    Loading companies...
                                </TableCell>
                            </TableRow>
                        ) : isError ? (
                            <TableRow>
                                <TableCell colSpan={7} className="text-center py-8 text-text-error">
                                    Failed to load companies
                                </TableCell>
                            </TableRow>
                        ) : companies.length > 0 ? (
                            companies.map((company) => (
                                <TableRow
                                    key={company.id}
                                    onClick={() => onRowClick(company)}
                                    className="cursor-pointer hover:bg-bg-elevated/50"
                                >
                                    <TableCell className="font-medium text-text-primary">
                                        {company.company_name}
                                    </TableCell>
                                    <TableCell className="text-text-secondary">
                                        {company.domains_active?.[0] || 'Unknown'}
                                    </TableCell>
                                    <TableCell className="text-right text-text-primary">
                                        {company.total_postings_7d}
                                    </TableCell>
                                    <TableCell className="text-right text-text-secondary">
                                        {company.total_postings_30d}
                                    </TableCell>
                                    <TableCell className={`text-right font-medium ${company.hiring_velocity_score > 0 ? 'text-green-500' : company.hiring_velocity_score < 0 ? 'text-red-500' : 'text-text-secondary'}`}>
                                        {formatVelocity(company.hiring_velocity_score)}
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex gap-1 flex-wrap">
                                            {company.bd_tags && company.bd_tags.length > 0 ? (
                                                company.bd_tags.map(tag => (
                                                    <Badge key={tag} variant={getBadgeVariant(tag) as any}>
                                                        {tag}
                                                    </Badge>
                                                ))
                                            ) : (
                                                <span className="text-text-muted text-xs">-</span>
                                            )}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-text-secondary text-sm">
                                        {formatDate(company.last_active_at)}
                                    </TableCell>
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={7} className="text-center py-8 text-text-secondary">
                                    No companies match the current filters
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
