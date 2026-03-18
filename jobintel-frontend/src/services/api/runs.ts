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

export interface ActorCreditSummary {
    actor_config_id: string;
    actor_name: string | null;
    platform: string | null;
    actual_spend_usd: number;
    run_count_mtd: number;
}

export interface CreditSummaryResponse {
    total_actual_spend_usd: number;
    total_estimated_usd: number;
    run_count_mtd: number;
    period_start: string;
    period_end: string;
    per_actor: ActorCreditSummary[];
}

export async function getCreditSummary(): Promise<CreditSummaryResponse> {
    const res = await apiClient.get('/runs/credit-summary');
    return res.data;
}

