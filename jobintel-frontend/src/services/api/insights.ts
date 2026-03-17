import { apiClient } from './client';

export interface DomainTrendParams {
    period?: '60d' | '30d' | '7d';
}

export interface DomainTrend {
    domain: string;
    jobs_today: number;
    jobs_yesterday: number;
    wow_change: number; // percentage
    active_companies: number;
    top_hiring_company: string;
}

export interface DomainTrendsResponse {
    status: string;
    data: DomainTrend[];
}

export const getDomainTrends = async (params?: DomainTrendParams): Promise<DomainTrendsResponse> => {
    const res = await apiClient.get('/insights/domain-trends', { params });
    return res.data;
};

export interface GeoHeatmapParams {
    group?: 'country' | 'city';
    country?: string;
}

export interface GeoLocationInsights {
    country: string;
    city?: string;
    job_count: number;
    top_domain?: string;
    top_company?: string;
    active_companies: number;
}

export type GeoHeatmapResponse = GeoLocationInsights[];

export const getGeoHeatmap = async (params?: GeoHeatmapParams): Promise<GeoLocationInsights[]> => {
    const res = await apiClient.get('/insights/geo-heatmap', { params });
    return res.data;
};
