import { useQuery } from "@tanstack/react-query";
import { getJob } from "../../services/api/jobs";
import { Badge } from "../ui/Badge";
import { X, ExternalLink, MapPin, Building, Calendar, DollarSign, Briefcase } from "lucide-react";
import { Button } from "../ui/Button";

interface JobDetailProps {
    jobId: string;
    onClose: () => void;
}

export function JobDetailDrawer({ jobId, onClose }: JobDetailProps) {
    const { data: job, isLoading, isError } = useQuery({
        queryKey: ["jobDetail", jobId],
        queryFn: () => getJob(jobId),
        enabled: !!jobId,
    });

    const formatDate = (dateString: string) => {
        if (!dateString) return "Unknown";
        return new Date(dateString).toLocaleDateString();
    };

    return (
        <div className="flex flex-col h-full bg-bg-surface border-l border-border-subtle shadow-xl w-full">
            {/* Header */}
            <div className="p-6 border-b border-border-subtle sticky top-0 bg-bg-surface z-10">
                <div className="flex justify-between items-start mb-4">
                    <div className="pr-8">
                        <div className="flex items-center gap-2 mb-2">
                            <Badge variant="default" className="bg-bg-elevated border-border-default">
                                {job?.source_platform || 'Loading...'}
                            </Badge>
                            {job?.is_duplicate && (
                                <Badge variant="default" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                                    Duplicate
                                </Badge>
                            )}
                        </div>
                        <h2 className="text-xl font-bold text-text-primary leading-tight">
                            {job?.title || 'Unknown Title'}
                        </h2>
                        <div className="flex items-center gap-4 mt-3 text-sm text-text-secondary flex-wrap">
                            <span className="flex items-center gap-1">
                                <Building size={14} />
                                {job?.company_name || 'Unknown Company'}
                            </span>
                            <span className="flex items-center gap-1">
                                <MapPin size={14} />
                                {job?.location_raw || 'Location Not Specified'}
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-full text-text-muted hover:bg-bg-elevated hover:text-text-primary transition-colors absolute right-4 top-4"
                    >
                        <X size={20} />
                    </button>
                </div>

                {job && (
                    <div className="flex gap-3 mt-6">
                        {job?.job_url && (
                            <Button
                                onClick={() => window.open(job.job_url, '_blank')}
                                className="flex-1 gap-2 rounded-full"
                            >
                                View Job <ExternalLink size={16} />
                            </Button>
                        )}
                    </div>
                )}
            </div>

            {/* Content Body */}
            <div className="p-6 overflow-y-auto flex-grow bg-bg-base">
                {isLoading ? (
                    <div className="space-y-4 animate-pulse">
                        <div className="h-4 bg-bg-elevated rounded w-1/4"></div>
                        <div className="h-24 bg-bg-elevated rounded w-full"></div>
                        <div className="h-4 bg-bg-elevated rounded w-1/2"></div>
                    </div>
                ) : isError ? (
                    <div className="text-center py-8 text-text-error">
                        Failed to load job details.
                    </div>
                ) : job ? (
                    <div className="space-y-6">
                        {/* Attributes Grid */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="flex flex-col gap-1 p-3 bg-bg-surface rounded-md border border-border-subtle">
                                <span className="flex items-center gap-1.5 text-xs text-text-secondary font-medium">
                                    <Calendar size={14} /> Date Posted
                                </span>
                                <span className="text-sm font-medium text-text-primary">
                                    {formatDate(job.posted_at)}
                                </span>
                            </div>
                            <div className="flex flex-col gap-1 p-3 bg-bg-surface rounded-md border border-border-subtle">
                                <span className="flex items-center gap-1.5 text-xs text-text-secondary font-medium">
                                    <Briefcase size={14} /> Emp. Type
                                </span>
                                <span className="text-sm font-medium text-text-primary">
                                    {job.employment_type || 'Unspecified'}
                                </span>
                            </div>
                            <div className="flex flex-col gap-1 p-3 bg-bg-surface rounded-md border border-border-subtle">
                                <span className="flex items-center gap-1.5 text-xs text-text-secondary font-medium">
                                    <DollarSign size={14} /> Salary
                                </span>
                                <span className="text-sm font-medium text-text-primary">
                                    {job.salary_raw || 'Unspecified'}
                                </span>
                            </div>
                            <div className="flex flex-col gap-1 p-3 bg-bg-surface rounded-md border border-border-subtle">
                                <span className="flex items-center gap-1.5 text-xs text-text-secondary font-medium">
                                    <Building size={14} /> Domain
                                </span>
                                <span className="text-sm font-medium text-text-primary">
                                    {job.domain || 'Unspecified'}
                                </span>
                            </div>
                        </div>

                        {/* Description */}
                        <div>
                            <h3 className="text-md font-semibold text-text-primary mb-3">Job Description</h3>
                            <div className="text-sm text-text-secondary leading-relaxed bg-bg-surface p-4 border border-border-subtle rounded-md whitespace-pre-wrap">
                                {job.description_raw || 'No description provided.'}
                            </div>
                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
