import { useMutation, useQueryClient } from "@tanstack/react-query";
import { enrichCompany } from "../../services/api/companies";
import { Loader2, Zap } from "lucide-react";

interface CompanyEnrichmentProps {
    company: any;
}

export function CompanyEnrichment({ company }: CompanyEnrichmentProps) {
    const queryClient = useQueryClient();

    const mutation = useMutation({
        mutationFn: () => enrichCompany(company.id),
        onSuccess: () => {
            // Invalidate company data so it updates the main detail view
            queryClient.invalidateQueries({ queryKey: ["companies"] });
            queryClient.invalidateQueries({ queryKey: ["company", company.id] });
        }
    });

    if (mutation.isError) {
        return (
            <div className="text-center py-4 text-text-error text-sm mt-4 bg-bg-base border border-border-subtle rounded-md">
                Failed to enrich company.
            </div>
        );
    }

    if (mutation.isPending) {
        return (
            <div className="flex flex-col items-center justify-center py-6 text-text-secondary mt-4 bg-bg-base border border-border-subtle hover:border-accent-primary/50 transition-colors rounded-md border-dashed">
                <Loader2 className="animate-spin mb-2" size={24} />
                <span className="text-sm font-medium">Fetching company enrichment...</span>
            </div>
        );
    }

    if (company.is_enriched) {
        return (
            <div className="mt-6 mb-6">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-[16px] font-semibold text-text-primary">Company Details</h3>
                    <span className="text-xs font-medium text-green-500 bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">
                        Enriched ✅
                    </span>
                </div>

                <div className="grid grid-cols-2 gap-4 p-4 bg-bg-base rounded-lg border border-border-subtle">
                    <div className="flex flex-col gap-1">
                        <span className="text-xs text-text-secondary uppercase">Industry</span>
                        <span className="text-sm font-medium text-text-primary">
                            {company.industry_apollo || "N/A"}
                        </span>
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className="text-xs text-text-secondary uppercase">Employee Count</span>
                        <span className="text-sm font-medium text-text-primary">
                            {company.employee_count || "N/A"}
                        </span>
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className="text-xs text-text-secondary uppercase">Website</span>
                        {company.website ? (
                            <a
                                href={company.website.startsWith('http') ? company.website : `https://${company.website}`}
                                target="_blank"
                                rel="noreferrer"
                                className="text-sm font-medium text-accent-primary hover:underline truncate"
                            >
                                {company.website}
                            </a>
                        ) : (
                            <span className="text-sm font-medium text-text-primary">N/A</span>
                        )}
                    </div>
                    <div className="flex flex-col gap-1">
                        <span className="text-xs text-text-secondary uppercase">LinkedIn</span>
                        {company.linkedin_url ? (
                            <a
                                href={company.linkedin_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-sm font-medium text-accent-primary hover:underline truncate"
                            >
                                LinkedIn Profile
                            </a>
                        ) : (
                            <span className="text-sm font-medium text-text-primary">N/A</span>
                        )}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="mt-6 mb-6 py-6 px-4 bg-bg-base border border-border-subtle rounded-lg flex flex-col items-center justify-center gap-3">
            <p className="text-sm text-text-secondary text-center">
                Missing details? Apollo enrichment can gather industry, employee count, and links for this company.
            </p>
            <button
                onClick={() => mutation.mutate()}
                className="flex items-center gap-2 px-4 py-2 bg-accent-primary hover:bg-accent-secondary text-white rounded-md text-sm font-medium transition-colors shadow-sm"
            >
                <Zap size={16} fill="currentColor" className="text-yellow-300" />
                Enrich Company
            </button>
        </div>
    );
}
