import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { PageShell } from "../components/layout/PageShell";
import { CommandCenterPage } from "../pages/CommandCenter/CommandCenterPage";
import { CompaniesPage } from "../pages/Companies/CompaniesPage";
import { JobsPage } from "../pages/Jobs/JobsPage";
import { RunsPage } from "../pages/Runs/RunsPage";
import { ActorsPage } from "../pages/Actors/ActorsPage";
import { DomainIntelligencePage } from "../pages/DomainIntelligence/DomainIntelligencePage";
import { GeoInsightsPage } from "../pages/GeoInsights/GeoInsightsPage";

const router = createBrowserRouter([
    {
        path: "/",
        element: <PageShell />,
        children: [
            {
                index: true,
                element: <CommandCenterPage />,
            },
            {
                path: "companies",
                element: <CompaniesPage />,
            },
            {
                path: "domain-intelligence",
                element: <DomainIntelligencePage />,
            },
            {
                path: "geo-insights",
                element: <GeoInsightsPage />,
            },
            {
                path: "jobs",
                element: <JobsPage />,
            },
            {
                path: "runs",
                element: <RunsPage />,
            },
            {
                path: "actors",
                element: <ActorsPage />,
            },
        ],
    },
]);

export function Router() {
    return <RouterProvider router={router} />;
}
