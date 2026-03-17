import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { PageShell } from "../components/layout/PageShell";
import { CommandCenterPage } from "../pages/CommandCenter/CommandCenterPage";
import { CompaniesPage } from "../pages/Companies/CompaniesPage";
import { JobsPage } from "../pages/Jobs/JobsPage";
import { RunsPage } from "../pages/Runs/RunsPage";
import { ActorsPage } from "../pages/Actors/ActorsPage";

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
