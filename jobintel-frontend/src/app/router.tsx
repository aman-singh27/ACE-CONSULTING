import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { PageShell } from "../components/layout/PageShell";
import { CommandCenterPage } from "../pages/CommandCenter/CommandCenterPage";
import { CompaniesPage } from "../pages/Companies/CompaniesPage";
import { JobsPage } from "../pages/Jobs/JobsPage";
import { RunsPage } from "../pages/Runs/RunsPage";
import { ActorsPage } from "../pages/Actors/ActorsPage";
import { ScrapersPage } from "../pages/Scrapers/ScrapersPage";
import { HubSpotPage } from "../pages/HubSpot/HubSpotPage";

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
        path: "hubspot",
        element: <HubSpotPage />,
      },
      {
        path: "jobs",
        element: <JobsPage />,
      },
      {
        path: "scrapers",
        element: <ScrapersPage />,
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
