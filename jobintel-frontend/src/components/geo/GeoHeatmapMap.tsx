import { useMemo } from 'react';
import { ComposableMap, Geographies, Geography, ZoomableGroup } from "react-simple-maps";
import { scaleLinear } from "d3-scale";
import type { GeoLocationInsights } from "../../services/api/insights";

const geoUrl = "https://unpkg.com/world-atlas@2.0.2/countries-110m.json";

const colorScale = scaleLinear<string>()
    .domain([0, 10, 50])
    .range(["#F3F4F6", "#3B82F6", "#1E3A8A"])
    .clamp(true);

interface GeoHeatmapMapProps {
    data: GeoLocationInsights[];
    onCountryClick: (country: GeoLocationInsights) => void;
    selectedCountry?: string;
}

export function GeoHeatmapMap({ data, onCountryClick, selectedCountry }: GeoHeatmapMapProps) {
    const dataByCountry = useMemo(() => {
        const map = new Map<string, GeoLocationInsights>();
        data.forEach(d => {
            let name = d.country.toLowerCase();
            if (name === "united states" || name === "usa") name = "united states of america";
            if (name === "uk") name = "united kingdom";
            map.set(name, d);
        });
        return map;
    }, [data]);

    return (
        <div className="w-full h-full bg-bg-surface overflow-hidden rounded-md border border-border-default relative">
            <ComposableMap
                projectionConfig={{ scale: 140 }}
                width={800}
                height={500}
                style={{ width: "100%", height: "100%" }}
            >
                <ZoomableGroup center={[0, 20]} zoom={1} minZoom={1} maxZoom={8}>
                    <Geographies geography={geoUrl}>
                        {({ geographies }) =>
                            geographies.map((geo) => {
                                const geoName = (geo.properties.name || "").toLowerCase();
                                const countryData = dataByCountry.get(geoName);
                                const isSelected = selectedCountry && (
                                    selectedCountry.toLowerCase() === geoName ||
                                    (countryData && selectedCountry.toLowerCase() === countryData.country.toLowerCase())
                                );
                                const jobCount = countryData ? countryData.job_count : 0;

                                return (
                                    <Geography
                                        key={geo.rsmKey}
                                        geography={geo}
                                        onClick={() => {
                                            if (countryData) {
                                                onCountryClick(countryData);
                                            }
                                        }}
                                        fill={isSelected ? "#F59E0B" : (jobCount > 0 ? colorScale(jobCount) : "#F3F4F6")}
                                        stroke="#D1D5DB"
                                        strokeWidth={0.5}
                                        style={{
                                            default: { outline: "none" },
                                            hover: {
                                                fill: jobCount > 0 ? "#10B981" : "#E5E7EB",
                                                outline: "none",
                                                cursor: countryData ? "pointer" : "default"
                                            },
                                            pressed: { outline: "none" },
                                        }}
                                    />
                                );
                            })
                        }
                    </Geographies>
                </ZoomableGroup>
            </ComposableMap>

            <div className="absolute bottom-4 left-4 flex flex-col gap-1.5 bg-bg-surface p-3 rounded shadow-md text-xs border border-border-default">
                <div className="font-semibold text-text-primary mb-1">Jobs Map</div>
                <div className="flex items-center gap-2 text-text-secondary"><div className="w-4 h-4 rounded-sm" style={{ backgroundColor: "#1E3A8A" }}></div> 50+ jobs</div>
                <div className="flex items-center gap-2 text-text-secondary"><div className="w-4 h-4 rounded-sm" style={{ backgroundColor: "#3B82F6" }}></div> 10-49 jobs</div>
                <div className="flex items-center gap-2 text-text-secondary"><div className="w-4 h-4 rounded-sm" style={{ backgroundColor: colorScale(1) }}></div> 1-9 jobs</div>
                <div className="flex items-center gap-2 text-text-secondary"><div className="w-4 h-4 rounded-sm" style={{ backgroundColor: "#F3F4F6", border: "1px solid #D1D5DB" }}></div> 0 jobs</div>
            </div>
        </div>
    );
}
