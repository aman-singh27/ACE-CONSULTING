import { apiClient } from './client';

export async function getCompanies(params: Record<string, any> = {}) {
    // If params has something like { bdTags: 'Spiking', ... }, pass them
    const res = await apiClient.get('/companies', { params });
    return res.data;
}

export async function getCompany(id: string) {
    const res = await apiClient.get(`/companies/${id}`);
    return res.data;
}

export async function getCompanyJobs(id: string) {
    const res = await apiClient.get(`/companies/${id}/jobs`);
    return res.data;
}

export async function enrichCompany(companyId: string) {
    const res = await apiClient.post(`/companies/${companyId}/enrich`);
    return res.data;
}

export async function findCompanyContacts(companyId: string) {
    const res = await apiClient.post(`/companies/${companyId}/contacts`);
    return res.data;
}
