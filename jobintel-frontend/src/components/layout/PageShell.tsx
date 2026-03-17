import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function PageShell() {
    return (
        <div className="min-h-screen bg-bg-primary font-sans text-text-primary flex">
            <Sidebar />
            <div className="flex-1 flex flex-col pl-[240px]">
                <Header />
                <main className="flex-1 overflow-x-hidden p-8">
                    <div className="mx-auto max-w-7xl w-full">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}
