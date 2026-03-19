import { useState, useCallback, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { JobFilters } from "../../components/jobs/JobFilters";
import { JobTable, type JobItem } from "../../components/jobs/JobTable";
import { JobDetailDrawer } from "../../components/jobs/JobDetailDrawer";
import { exportJobs } from "../../services/api/jobs";
import { Button } from "../../components/ui/Button";
import { Download } from "lucide-react";

export function JobsPage() {
  const [searchParams] = useSearchParams();
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [page, setPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState<JobItem | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  // Check for jobId in URL params on mount
  useEffect(() => {
    const jobId = searchParams.get("jobId");
    if (jobId && !selectedJob) {
      // We'll set a dummy job object - the JobDetailDrawer will fetch the full details
      setSelectedJob({ id: jobId } as JobItem);
    }
  }, [searchParams, selectedJob]);

  const handleFilterChange = useCallback((newFilters: Record<string, any>) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page on filter change
  }, []);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await exportJobs(filters);
    } catch (error) {
      console.error("Failed to export jobs", error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full">
      {/* Header */}
      <div className="mb-6 flex justify-between items-end shrink-0">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">
            Master Job Table
          </h1>
          <p className="text-text-secondary mt-1">
            Explore, search, and export the full dataset of scraped jobs.
          </p>
        </div>
        <Button
          onClick={handleExport}
          disabled={isExporting}
          className="flex items-center gap-2"
        >
          <Download size={16} />
          {isExporting ? "Exporting..." : "Export CSV"}
        </Button>
      </div>

      <div className="flex flex-col flex-grow min-h-0 gap-6">
        {/* Filters Row */}
        <div className="shrink-0 w-full">
          <JobFilters onFilterChange={handleFilterChange} />
        </div>

        {/* Main Content Area */}
        <div className="flex-grow min-h-0 w-full flex gap-6 overflow-hidden relative">
          {/* Table View */}
          <div
            className={`transition-all duration-300 ease-in-out h-full ${
              selectedJob ? "w-full lg:w-[65%]" : "w-full"
            }`}
          >
            <JobTable
              filters={filters}
              page={page}
              setPage={setPage}
              onRowClick={setSelectedJob}
            />
          </div>

          {/* Detail Drawer Slide-over */}
          <div
            className={`absolute right-0 top-0 h-full w-full lg:w-[35%] lg:static transition-all duration-300 ease-in-out transform ${
              selectedJob
                ? "translate-x-0 opacity-100 z-10"
                : "translate-x-full opacity-0 -z-10 absolute pointer-events-none"
            }`}
          >
            {selectedJob && (
              <JobDetailDrawer
                jobId={selectedJob.id}
                onClose={() => setSelectedJob(null)}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
