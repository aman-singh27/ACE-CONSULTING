import { apiClient } from './client';

export async function getRunsToday() {
    const res = await apiClient.get('/runs/today');
    return res.data;
}

export interface RunHealth {
    actor_id: string;
    platform: string;
    last_run: string | null;
    last_success: string | null;
}

export interface RunsHealthResponse {
    status: string;
    data: RunHealth[];
}

export async function getRunsHealth(): Promise<RunsHealthResponse> {
    const res = await apiClient.get('/runs/health');
    return res.data;
}
