import { apiClient } from './client';

export async function getActors() {
    const res = await apiClient.get('/actors');
    return res.data;
}

export async function createActor(data: Record<string, any>) {
    const res = await apiClient.post('/actors', data);
    return res.data;
}

export async function updateActor(id: string, data: Record<string, any>) {
    const res = await apiClient.patch(`/actors/${id}`, data);
    return res.data;
}

export async function triggerActor(id: string) {
    const res = await apiClient.post(`/actors/${id}/trigger`);
    return res.data;
}
