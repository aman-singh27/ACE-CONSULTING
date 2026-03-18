import { useState } from "react";
import { ScraperSetupForm } from "../../components/scrapers/ScraperSetupForm";
import { SavedScrapersList } from "../../components/scrapers/SavedScrapersList";
import { CreditUsagePanel } from "../../components/scrapers/CreditUsagePanel";

export function ScrapersPage() {
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    return (
        <div className="flex flex-col h-full w-full">
            <div className="mb-6 shrink-0">
                <h1 className="text-3xl font-bold tracking-tight text-text-primary">
                    Scrapers
                </h1>
                <p className="text-text-secondary mt-1">
                    Set up and manage your data sources.
                </p>
            </div>

            <CreditUsagePanel refreshTrigger={refreshTrigger} />
            <div className="mb-8" />

            <ScraperSetupForm onSuccess={() => setRefreshTrigger((t) => t + 1)} />
            <div className="my-8 border-t border-border-subtle" />
            <SavedScrapersList refreshTrigger={refreshTrigger} />
        </div>
    );
}

