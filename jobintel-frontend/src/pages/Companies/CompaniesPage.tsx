import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CompanyFilters } from "../../components/companies/CompanyFilters";
import { CompanyTable } from "../../components/companies/CompanyTable";
import { CompanyDetailPanel } from "../../components/companies/CompanyDetailPanel";

export function CompaniesPage() {
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [selectedCompany, setSelectedCompany] = useState<any | null>(null);

  const initialSearch = searchParams.get("search") || undefined;

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <div className="mb-8 shrink-0">
        <h1 className="text-3xl font-bold tracking-tight text-text-primary">
          Company Intelligence
        </h1>
        <p className="text-text-secondary mt-1">
          Browse and analyze all discovered companies.
        </p>
      </div>

      <div className="flex flex-col flex-grow min-h-0 gap-6">
        {/* Filters Row */}
        <div className="shrink-0 w-full">
          <CompanyFilters
            initialSearch={initialSearch}
            onFilterChange={setFilters}
          />
        </div>

        {/* Main Content Area */}
        <div className="flex-grow min-h-0 w-full flex gap-6 overflow-hidden relative">
          {/* Table View */}
          <div
            className={`transition-all duration-300 ease-in-out h-full ${
              selectedCompany ? "w-full lg:w-[70%]" : "w-full"
            }`}
          >
            <CompanyTable filters={filters} onRowClick={setSelectedCompany} />
          </div>

          {/* Detail Panel */}
          <div
            className={`absolute right-0 top-0 h-full w-full lg:w-[30%] lg:static transition-all duration-300 ease-in-out transform ${
              selectedCompany
                ? "translate-x-0 opacity-100 z-10"
                : "translate-x-full opacity-0 -z-10 absolute pointer-events-none"
            }`}
          >
            {selectedCompany && (
              <CompanyDetailPanel
                company={selectedCompany}
                onClose={() => setSelectedCompany(null)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
