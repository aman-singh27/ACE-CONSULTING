import { apiClient } from "./client";

export interface SyncStatusResponse {
  status: "idle" | "running" | "completed" | "failed";
  last_sync: {
    synced_at?: string;
    companies_synced?: number;
    contacts_synced?: number;
    notes_created?: number;
    deals_created?: number;
    duration_seconds?: number;
    error?: string;
  } | null;
  next_scheduled: string;
  message: string;
}

export interface SyncTriggerResponse {
  status: string;
  message: string;
  summary: Record<string, unknown> | null;
}

export async function getHubSpotSyncStatus(): Promise<SyncStatusResponse> {
  const res = await apiClient.get("/hubspot/sync/status");
  return res.data;
}

export async function triggerHubSpotSync(
  hoursBack: number = 24,
  forceAll: boolean = false,
): Promise<SyncTriggerResponse> {
  const res = await apiClient.post(
    `/hubspot/sync?hours_back=${hoursBack}&force_all=${forceAll}`,
  );
  return res.data;
}

export async function syncCompanyToHubSpot(
  companyId: string,
): Promise<SyncTriggerResponse> {
  const res = await apiClient.post(`/hubspot/sync/company/${companyId}`);
  return res.data;
}

export async function setupHubSpotProperties(): Promise<{
  status: string;
  message: string;
}> {
  const res = await apiClient.post("/hubspot/setup");
  return res.data;
}

export async function saveHubSpotAPIKey(apiKey: string): Promise<{
  status: string;
  message: string;
  saved: boolean;
}> {
  const res = await apiClient.post("/hubspot/config/api-key", {
    api_key: apiKey,
  });
  return res.data;
}

export async function getHubSpotAPIKeyStatus(): Promise<{
  status: string;
  configured_from: string;
  message: string;
}> {
  const res = await apiClient.get("/hubspot/config/api-key-status");
  return res.data;
}

export interface SyncHistoryEntry {
  id: string;
  triggered_at: string;
  status: "completed" | "failed";
  companies_synced: number;
  notes_created: number;
  deals_created: number;
  contacts_synced: number;
  duration_seconds: number;
  error?: string;
}

// Module-level history store (in-memory, max 20 entries)
const _syncHistory: SyncHistoryEntry[] = [];

export function recordSyncHistory(result: SyncTriggerResponse): void {
  const entry: SyncHistoryEntry = {
    id: crypto.randomUUID(),
    triggered_at: new Date().toISOString(),
    status: result.status === "completed" ? "completed" : "failed",
    companies_synced: (result.summary?.companies_synced as number) ?? 0,
    notes_created: (result.summary?.notes_created as number) ?? 0,
    deals_created: (result.summary?.deals_created as number) ?? 0,
    contacts_synced: (result.summary?.contacts_synced as number) ?? 0,
    duration_seconds: (result.summary?.duration_seconds as number) ?? 0,
    error: result.summary?.error as string | undefined,
  };
  _syncHistory.unshift(entry);
  if (_syncHistory.length > 20) _syncHistory.pop();
}

export function getSyncHistory(): SyncHistoryEntry[] {
  return [..._syncHistory];
}
