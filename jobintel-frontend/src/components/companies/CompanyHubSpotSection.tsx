import { useMutation, useQueryClient } from "@tanstack/react-query";
import { syncCompanyToHubSpot } from "../../services/api/hubspot";
import { Button } from "../ui/Button";
import { Check, X, Clock, RefreshCw, Loader2 } from "lucide-react";
import { relativeTime } from "../../utils/relativeTime";

interface CompanyHubSpotSectionProps {
  company: any;
}

export function CompanyHubSpotSection({ company }: CompanyHubSpotSectionProps) {
  const queryClient = useQueryClient();

  const syncMutation = useMutation({
    mutationFn: () => syncCompanyToHubSpot(company.id),
    onSuccess: () => {
      // Invalidate company data to refresh HubSpot fields
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["company", company.id] });
    },
  });

  const getSyncStatus = () => {
    if (company.hubspot_synced_at) {
      return {
        status: "synced",
        icon: Check,
        color: "text-green-500",
        text: "Synced",
      };
    } else if (company.hubspot_company_id) {
      return {
        status: "in_progress",
        icon: Clock,
        color: "text-yellow-500",
        text: "In Progress",
      };
    } else {
      return {
        status: "not_synced",
        icon: X,
        color: "text-red-500",
        text: "Not Synced",
      };
    }
  };

  const status = getSyncStatus();
  const StatusIcon = status.icon;

  return (
    <div className="mt-6 mb-6 py-6 px-4 bg-bg-base border border-border-subtle rounded-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[16px] font-semibold text-text-primary flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          HubSpot Integration
        </h3>
        <div className="flex items-center gap-2">
          <StatusIcon className={`h-4 w-4 ${status.color}`} />
          <span className={`text-sm font-medium ${status.color}`}>
            {status.text}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-text-secondary uppercase">
            Company ID
          </span>
          <span className="text-sm font-medium text-text-primary">
            {company.hubspot_company_id || "Not set"}
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs text-text-secondary uppercase">Deal ID</span>
          <span className="text-sm font-medium text-text-primary">
            {company.hubspot_deal_id || "Not set"}
          </span>
        </div>
      </div>

      {company.hubspot_synced_at && (
        <div className="mb-4">
          <span className="text-xs text-text-secondary uppercase">
            Last Synced
          </span>
          <div className="text-sm font-medium text-text-primary">
            {relativeTime(company.hubspot_synced_at)}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <Button
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
          size="sm"
          className="flex items-center gap-2"
        >
          {syncMutation.isPending ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3" />
          )}
          {syncMutation.isPending ? "Syncing..." : "Sync to HubSpot"}
        </Button>
      </div>
    </div>
  );
}
