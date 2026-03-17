import { apiClient } from './client';

export async function getJobs(params: Record<string, any> = {}) {
    const res = await apiClient.get('/jobs', { params });
    return res.data;
}

export async function getJob(id: string) {
    const res = await apiClient.get(`/jobs/${id}`);
    return res.data;
}

export async function exportJobs(params: Record<string, any> = {}) {
    const res = await apiClient.get('/jobs/export', {
        params,
        responseType: 'blob'
    });

    // Create a download link and click it
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'jobs_export.csv');
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);

    return true;
}
