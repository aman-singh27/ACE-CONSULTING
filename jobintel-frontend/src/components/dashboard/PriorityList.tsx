import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getPriorityList } from "../../services/api/dashboard";
import { Card } from "../ui/Card";
import { Badge } from "../ui/Badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/Table";

interface PriorityItem {
    company_name: string;
    bd_tags: string[];
    total_postings_7d: number;
    bd_priority_score: number;
}

export function PriorityList() {
    const navigate = useNavigate();
    const { data: priorityItems, isLoading, isError } = useQuery<PriorityItem[]>({
        queryKey: ["priority"],
        queryFn: getPriorityList,
    });

    return (
        <Card className="flex flex-col h-full overflow-hidden">
            <div className="mb-4">
                <h3 className="text-[16px] font-semibold text-text-primary">Priority List</h3>
                <p className="text-[14px] text-text-secondary">Top 10 companies for BD</p>
            </div>

            <div className="overflow-auto flex-grow">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Company Name</TableHead>
                            <TableHead>BD Tags</TableHead>
                            <TableHead>Jobs last 7d</TableHead>
                            <TableHead className="text-right">Priority score</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-4 text-text-secondary h-20 animate-pulse">
                                    Loading priority list...
                                </TableCell>
                            </TableRow>
                        ) : isError ? (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-4 text-text-error">
                                    Failed to load priority data
                                </TableCell>
                            </TableRow>
                        ) : priorityItems && priorityItems.length > 0 ? (
                            priorityItems.slice(0, 10).map((item, index) => (
                                <TableRow
                                    key={index}
                                    onClick={() => navigate(`/companies?search=${encodeURIComponent(item.company_name)}`)}
                                    className="cursor-pointer hover:bg-bg-elevated/50"
                                >
                                    <TableCell className="font-medium text-text-primary">{item.company_name}</TableCell>
                                    <TableCell>
                                        <div className="flex gap-1 flex-wrap">
                                            {(item.bd_tags ?? []).map(tag => (
                                                <Badge key={tag} variant="default" className="text-xs">
                                                    {tag}
                                                </Badge>
                                            ))}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-text-secondary">{item.total_postings_7d} jobs</TableCell>
                                    <TableCell className="text-right font-semibold text-text-primary">
                                        {item.bd_priority_score}
                                    </TableCell>
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-4 text-text-secondary">
                                    No priority data available
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </Card>
    );
}
