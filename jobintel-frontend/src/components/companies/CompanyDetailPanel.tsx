import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { getCompanyJobs } from "../../services/api/companies";
import { Badge } from "../ui/Badge";
import { X } from "lucide-react";
import { CompanyHubSpotSection } from "./CompanyHubSpotSection";
import { CompanyContacts } from "./CompanyContacts";

interface CompanyDetailProps {
  company: any; // Using any here to quickly wire up, later refine type
  onClose: () => void;
}

export function CompanyDetailPanel({ company, onClose }: CompanyDetailProps) {
  const navigate = useNavigate();
  const {
    data: jobResponse,
    isLoading,
    isError,
  } = useQuery<any>({
    queryKey: ["companyJobs", company?.id],
    queryFn: () => getCompanyJobs(company.id),
    enabled: !!company?.id,
  });

  const handleJobClick = (jobId: string) => {
    navigate(`/jobs?jobId=${jobId}`);
  };

  if (!company) return null;

  const getBadgeVariant = (tag: string) => {
    switch (tag.toLowerCase()) {
      case "spiking":
        return "spiking";
      case "struggling":
        return "struggling";
      case "new entrant":
        return "new";
      case "salary signal":
        return "default";
      default:
        return "secondary";
    }
  };

  const formatVelocity = (score: number) => {
    if (score === 0) return "-";
    const prefix = score > 0 ? "+" : "";
    return `${prefix}${Math.round(score * 100)}%`;
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return "Unknown";
    const date = new Date(dateString);

    const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
    const daysDifference = Math.round(
      (date.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24),
    );

    if (daysDifference === 0) return "Today";
    if (daysDifference > -7) return rtf.format(daysDifference, "day");

    return date.toLocaleDateString();
  };

  return (
    <div className="flex flex-col h-full bg-bg-surface border-l border-border-subtle shadow-lg">
      {/* Header */}
      <div className="p-6 border-b border-border-subtle sticky top-0 bg-bg-surface z-10">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-xl font-bold text-text-primary">
              {company.company_name}
            </h2>
            <div className="flex items-center gap-2 mt-1 text-sm text-text-secondary">
              <span>{company.domains_active?.[0] || "Unknown Domain"}</span>
              {company.countries?.length > 0 && (
                <>
                  <span>•</span>
                  <span>{company.countries.join(", ")}</span>
                </>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-text-muted hover:bg-bg-elevated hover:text-text-primary transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          {company.bd_tags?.map((tag: string) => (
            <Badge key={tag} variant={getBadgeVariant(tag) as any}>
              {tag}
            </Badge>
          ))}
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-bg-base rounded-lg border border-border-subtle">
          <div className="flex flex-col gap-1">
            <span className="text-xs text-text-secondary uppercase">
              7d Jobs
            </span>
            <span className="text-lg font-semibold text-text-primary">
              {company.total_postings_7d}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs text-text-secondary uppercase">
              30d Jobs
            </span>
            <span className="text-lg font-semibold text-text-primary">
              {company.total_postings_30d}
            </span>
          </div>
          <div className="flex flex-col gap-1">
            <span className="text-xs text-text-secondary uppercase">
              Velocity
            </span>
            <span
              className={`text-lg font-semibold ${company.hiring_velocity_score > 0 ? "text-green-500" : company.hiring_velocity_score < 0 ? "text-red-500" : "text-text-primary"}`}
            >
              {formatVelocity(company.hiring_velocity_score)}
            </span>
          </div>
        </div>
      </div>

      {/* Content: HubSpot Integration */}
      <div className="px-6 py-2 border-b border-border-subtle bg-bg-surface">
        <CompanyHubSpotSection company={company} />
      </div>

      {/* Content: Contacts and Recent Jobs */}
      <div className="p-6 overflow-y-auto flex-grow bg-bg-base">
        {/* Contacts Section */}
        <div className="mb-8">
          <h3 className="text-[16px] font-semibold text-text-primary mb-4">
            Contacts
          </h3>
          <CompanyContacts companyId={company.id} />
        </div>

        {/* Recent Jobs Section */}
        <div>
          <h3 className="text-[16px] font-semibold text-text-primary mb-4">
            Recent Jobs
          </h3>

          {isLoading ? (
            <div className="text-center py-8 text-text-secondary animate-pulse">
              Loading jobs...
            </div>
          ) : isError ? (
            <div className="text-center py-8 text-text-error">
              Failed to load jobs
            </div>
          ) : jobResponse?.items && jobResponse.items.length > 0 ? (
            <div className="space-y-4">
              {jobResponse.items.map((job: any) => (
                <div
                  key={job.id}
                  onClick={() => handleJobClick(job.id)}
                  className="p-4 rounded-md border border-border-subtle bg-bg-base flex flex-col gap-2 hover:border-accent-primary/50 transition-colors cursor-pointer"
                >
                  <div className="flex justify-between items-start gap-4">
                    <h4 className="font-medium text-text-primary leading-tight">
                      {job.title}
                    </h4>
                    <span className="text-xs font-medium bg-bg-elevated px-2 py-1 rounded text-text-secondary border border-border-subtle whitespace-nowrap">
                      {job.source_platform}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[13px] text-text-secondary">
                    <span>{job.location_raw || "Remote"}</span>
                    <span>•</span>
                    <span>{formatDate(job.posted_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-text-secondary bg-bg-base rounded-md border border-border-subtle border-dashed">
              No recent jobs found
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
