import { apiClient } from './client';

export async function getDashboardSummary() {
    const res = await apiClient.get('/dashboard/summary');
    return res.data;
}

export async function getPriorityList() {
    const res = await apiClient.get('/insights/priority-list');
    return res.data;
}
