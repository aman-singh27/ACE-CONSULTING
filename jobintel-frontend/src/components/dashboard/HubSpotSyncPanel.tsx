import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getHubSpotSyncStatus,
  triggerHubSpotSync,
  setupHubSpotProperties,
  recordSyncHistory,
} from "../../services/api/hubspot";
import { Button } from "../ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import {
  Loader2,
  RefreshCw,
  Settings,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import { useState } from "react";

export function HubSpotSyncPanel() {
  const queryClient = useQueryClient();
  const [hoursBack, setHoursBack] = useState(24);

  const {
    data: status,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["hubspot-sync-status"],
    queryFn: getHubSpotSyncStatus,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const triggerMutation = useMutation({
    mutationFn: () => triggerHubSpotSync(hoursBack),
    onSuccess: (data) => {
      recordSyncHistory(data);
      queryClient.invalidateQueries({ queryKey: ["hubspot-sync-status"] });
    },
  });

  const setupMutation = useMutation({
    mutationFn: setupHubSpotProperties,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hubspot-sync-status"] });
    },
  });

  const formatLastSync = (lastSync: any) => {
    if (!lastSync?.synced_at) return "Never";

    const date = new Date(lastSync.synced_at);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) return "Just now";
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "text-blue-600";
      case "completed":
        return "text-green-600";
      case "failed":
        return "text-red-600";
      default:
        return "text-gray-600";
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            HubSpot Sync Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
            <span className="ml-2 text-gray-600">Loading sync status...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <XCircle className="h-5 w-5 text-red-500" />
            HubSpot Sync Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-red-600">
            Failed to load sync status
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <RefreshCw className="h-5 w-5" />
          HubSpot Sync Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon(status?.status || "idle")}
            <span
              className={`font-medium ${getStatusColor(status?.status || "idle")}`}
            >
              {status?.status === "running"
                ? "Syncing..."
                : status?.status === "completed"
                  ? "Completed"
                  : status?.status === "failed"
                    ? "Failed"
                    : "Idle"}
            </span>
          </div>
          <div className="text-sm text-gray-600">
            Last sync: {formatLastSync(status?.last_sync)}
          </div>
        </div>

        {/* Last Sync Summary */}
        {status?.last_sync && (
          <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg">
            <div>
              <div className="text-sm text-gray-600">Companies Synced</div>
              <div className="text-lg font-semibold">
                {status.last_sync.companies_synced || 0}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-600">Contacts Synced</div>
              <div className="text-lg font-semibold">
                {status.last_sync.contacts_synced || 0}
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {status?.last_sync?.error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <div className="text-sm text-red-800">
              <strong>Error:</strong> {status.last_sync.error}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600">Sync last:</label>
            <select
              value={hoursBack}
              onChange={(e) => setHoursBack(Number(e.target.value))}
              className="px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value={1}>1 hour</option>
              <option value={6}>6 hours</option>
              <option value={24}>24 hours</option>
              <option value={168}>7 days</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={() => triggerMutation.mutate()}
              disabled={
                triggerMutation.isPending || status?.status === "running"
              }
              className="flex items-center gap-2"
            >
              {triggerMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {triggerMutation.isPending ? "Syncing..." : "Sync Now"}
            </Button>

            <Button
              variant="outline"
              onClick={() => setupMutation.mutate()}
              disabled={setupMutation.isPending}
              className="flex items-center gap-2"
            >
              {setupMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Settings className="h-4 w-4" />
              )}
              Setup Properties
            </Button>
          </div>
        </div>

        {/* Next Scheduled */}
        {status?.next_scheduled && (
          <div className="text-xs text-gray-500 pt-2 border-t">
            Next scheduled sync:{" "}
            {new Date(status.next_scheduled).toLocaleString()}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
