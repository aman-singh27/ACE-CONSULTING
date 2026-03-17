import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getGeoHeatmap } from "../../services/api/insights";
import type { GeoLocationInsights } from "../../services/api/insights";
import { GeoHeatmapMap } from "../../components/geo/GeoHeatmapMap";
import { KpiCard } from "../../components/ui/KpiCard";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "../../components/ui/Table";
import { Card } from "../../components/ui/Card";

export function GeoInsightsPage() {
    const [selectedCountry, setSelectedCountry] = useState<GeoLocationInsights | null>(null);

    // Fetch country-level heat map
    const { data: countryData, isLoading: isCountryLoading } = useQuery({
        queryKey: ['geo-heatmap', 'country'],
        queryFn: () => getGeoHeatmap({ group: 'country' })
    });

    // Fetch city-level data if a country is selected
    const { data: cityData, isLoading: isCityLoading } = useQuery({
        queryKey: ['geo-heatmap', 'city', selectedCountry?.country],
        queryFn: () => getGeoHeatmap({ group: 'city', country: selectedCountry?.country }),
        enabled: !!selectedCountry
    });

    const countries = countryData || [];
    const cities = cityData || [];

    return (
        <div className="flex flex-col h-full w-full gap-6">
            {/* Header */}
            <div className="shrink-0">
                <h1 className="text-3xl font-bold tracking-tight text-text-primary">Geo Hiring Map</h1>
                <p className="text-text-secondary mt-1">Visualize global hiring trends and regional job distributions.</p>
            </div>

            <div className="flex flex-col lg:flex-row gap-6 flex-grow min-h-0 pb-4">
                {/* Map Section */}
                <div className="flex-grow bg-bg-surface rounded-md h-[500px] lg:h-auto border border-border-default shadow-sm relative">
                    {isCountryLoading ? (
                        <div className="w-full h-full flex items-center justify-center text-text-secondary animate-pulse absolute inset-0 z-10 bg-bg-surface/50">
                            Loading map data...
                        </div>
                    ) : null}

                    <div className="w-full h-full p-2">
                        <GeoHeatmapMap
                            data={countries}
                            onCountryClick={setSelectedCountry}
                            selectedCountry={selectedCountry?.country}
                        />
                    </div>
                </div>

                {/* Details Panel */}
                <div className="w-full lg:w-[400px] flex flex-col gap-4 overflow-auto shrink-0 pr-1">
                    {selectedCountry ? (
                        <>
                            <Card className="flex flex-col gap-4">
                                <div>
                                    <h2 className="text-xl font-bold text-text-primary">{selectedCountry.country}</h2>
                                    <p className="text-sm text-text-secondary">Country Overview</p>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <KpiCard label="total jobs" metric={selectedCountry.job_count} />
                                    <KpiCard label="active companies" metric={selectedCountry.active_companies} />
                                </div>
                                <div className="flex flex-col gap-2 mt-2">
                                    <div className="bg-bg-elevated p-2 rounded border border-border-subtle flex justify-between items-center text-sm">
                                        <span className="text-text-secondary">Top Domain</span>
                                        <span className="font-semibold text-text-primary">{selectedCountry.top_domain || '-'}</span>
                                    </div>
                                    <div className="bg-bg-elevated p-2 rounded border border-border-subtle flex justify-between items-center text-sm">
                                        <span className="text-text-secondary">Top Company</span>
                                        <span className="font-semibold text-text-primary text-right max-w-[200px] truncate" title={typeof selectedCountry.top_company === 'object' ? selectedCountry.top_company?.company_name : selectedCountry.top_company}>
                                            {typeof selectedCountry.top_company === 'object' ? selectedCountry.top_company?.company_name : selectedCountry.top_company || '-'}
                                        </span>
                                    </div>
                                </div>
                            </Card>

                            <Card className="flex flex-col flex-grow min-h-[300px]">
                                <h3 className="font-semibold mb-3">City Breakdown</h3>
                                {isCityLoading ? (
                                    <div className="text-text-secondary animate-pulse text-sm text-center py-8">Loading cities...</div>
                                ) : cities.length > 0 ? (
                                    <div className="overflow-auto border rounded-sm border-border-subtle">
                                        <Table>
                                            <TableHeader>
                                                <TableRow>
                                                    <TableHead className="bg-bg-elevated">City</TableHead>
                                                    <TableHead className="text-right bg-bg-elevated">Jobs</TableHead>
                                                    <TableHead className="bg-bg-elevated">Top Company</TableHead>
                                                </TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {cities.map(city => (
                                                    <TableRow key={city.city || 'unknown'}>
                                                        <TableCell className="font-medium">{city.city || 'Unknown'}</TableCell>
                                                        <TableCell className="text-right">{city.job_count}</TableCell>
                                                        <TableCell className="text-xs">
                                                            <span className="px-2 py-1 bg-bg-elevated rounded border border-border-subtle inline-block max-w-[150px] truncate" title={typeof city.top_company === 'object' ? city.top_company?.company_name : city.top_company}>
                                                                {typeof city.top_company === 'object' ? city.top_company?.company_name : city.top_company || '-'}
                                                            </span>
                                                        </TableCell>
                                                    </TableRow>
                                                ))}
                                            </TableBody>
                                        </Table>
                                    </div>
                                ) : (
                                    <div className="text-text-secondary text-sm text-center py-8">No city data available for this country.</div>
                                )}
                            </Card>
                        </>
                    ) : (
                        <div className="h-full border border-border-default border-dashed rounded-md flex flex-col items-center justify-center text-text-secondary p-8 text-center bg-bg-surface/50">
                            <svg className="w-12 h-12 mb-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <p>Select a country on the map to view detailed hiring statistics and city breakdown.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
