import { useQuery } from "@tanstack/react-query";
import { getJobs } from "../../services/api/jobs";
import { Badge } from "../ui/Badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../ui/Table";
import { Button } from "../ui/Button";
import { ChevronLeft, ChevronRight } from "lucide-react";

export interface JobItem {
    id: string;
    title: string;
    company_name: string;
    domain: string;
    source_platform: string;
    location_raw: string;
    posted_at: string;
    is_duplicate: boolean;
    emails: string[];
    phones: string[];
}

interface JobTableProps {
    filters: Record<string, any>;
    page: number;
    setPage: (page: number) => void;
    onRowClick: (job: JobItem) => void;
}

export function JobTable({ filters, page, setPage, onRowClick }: JobTableProps) {
    const limit = 25;
    const { data: response, isLoading, isError } = useQuery({
        queryKey: ["jobs", filters, page],
        queryFn: () => getJobs({ ...filters, page, limit }),
    });

    const jobs: JobItem[] = response?.items || [];
    const total: number = response?.total || 0;
    const totalPages = Math.ceil(total / limit) || 1;

    const formatDate = (dateString: string) => {
        if (!dateString) return "Unknown";
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return "Unknown";

            const now = new Date();
            const daysDifference = Math.round((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

            if (daysDifference === 0) return "Today";
            
            const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
            if (daysDifference > -7 && daysDifference < 7) {
                return rtf.format(daysDifference, 'day');
            }

            return date.toLocaleDateString();
        } catch (e) {
            return "Unknown";
        }
    };

    return (
        <div className="w-full flex flex-col h-full bg-bg-surface rounded-card border border-border-subtle overflow-hidden relative">
            <div className="overflow-auto flex-grow">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Title</TableHead>
                            <TableHead>Company</TableHead>
                            <TableHead>Emails</TableHead>
                            <TableHead>Phones</TableHead>
                            <TableHead>Domain</TableHead>
                            <TableHead>Platform</TableHead>
                            <TableHead>Location</TableHead>
                            <TableHead>Posted</TableHead>
                            <TableHead>Duplicate</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading ? (
                            <TableRow>
                                <TableCell colSpan={9} className="text-center py-8 text-text-secondary animate-pulse">
                                    Loading jobs...
                                </TableCell>
                            </TableRow>
                        ) : isError ? (
                            <TableRow>
                                <TableCell colSpan={9} className="text-center py-8 text-text-error">
                                    Failed to load jobs
                                </TableCell>
                            </TableRow>
                        ) : jobs.length > 0 ? (
                            jobs.map((job) => (
                                <TableRow
                                    key={job.id}
                                    onClick={() => onRowClick(job)}
                                    className="cursor-pointer hover:bg-bg-elevated/50"
                                >
                                    <TableCell className="font-medium text-text-primary max-w-[200px] truncate">
                                        {job.title}
                                    </TableCell>
                                    <TableCell className="text-text-primary truncate max-w-[150px]">
                                        {job.company_name || 'Unknown'}
                                    </TableCell>
                                    <TableCell className="text-text-primary text-xs max-w-[150px] truncate">
                                        {Array.isArray(job.emails) && job.emails.length > 0 ? job.emails.join(", ") : <span className="text-text-muted">—</span>}
                                    </TableCell>
                                    <TableCell className="text-text-primary text-xs max-w-[120px] truncate">
                                        {Array.isArray(job.phones) && job.phones.length > 0 ? job.phones.join(", ") : <span className="text-text-muted">—</span>}
                                    </TableCell>
                                    <TableCell className="text-text-secondary">
                                        {job.domain || 'N/A'}
                                    </TableCell>
                                    <TableCell className="text-text-secondary">
                                        {job.source_platform}
                                    </TableCell>
                                    <TableCell className="text-text-secondary truncate max-w-[150px]">
                                        {job.location_raw || 'Remote'}
                                    </TableCell>
                                    <TableCell className="text-text-secondary text-sm whitespace-nowrap">
                                        {formatDate(job.posted_at)}
                                    </TableCell>
                                    <TableCell>
                                        {job.is_duplicate ? (
                                            <Badge variant="default" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                                                Duplicate
                                            </Badge>
                                        ) : (
                                            <span className="text-text-muted text-xs">—</span>
                                        )}
                                    </TableCell>
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={9} className="text-center py-8 text-text-secondary">
                                    No jobs found
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && (
                <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle bg-bg-surface shrink-0">
                    <div className="text-sm text-text-secondary">
                        Showing <span className="font-medium text-text-primary">{(page - 1) * limit + 1}</span> to <span className="font-medium text-text-primary">{Math.min(page * limit, total)}</span> of <span className="font-medium text-text-primary">{total}</span> results
                    </div>
                    <div className="flex gap-2 items-center">
                        <Button
                            className="h-8 w-8 p-0 bg-bg-elevated text-text-primary border-border-default hover:bg-bg-elevated/80"
                            onClick={() => setPage(Math.max(1, page - 1))}
                            disabled={page === 1}
                        >
                            <ChevronLeft size={16} />
                        </Button>
                        <span className="text-sm font-medium px-2">Page {page} of {totalPages}</span>
                        <Button
                            className="h-8 w-8 p-0 bg-bg-elevated text-text-primary border-border-default hover:bg-bg-elevated/80"
                            onClick={() => setPage(Math.min(totalPages, page + 1))}
                            disabled={page === totalPages}
                        >
                            <ChevronRight size={16} />
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
}
