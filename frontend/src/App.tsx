import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { SessionSidebar } from "./components/SessionSidebar";
import { NotificationToast } from "./components/NotificationToast";
import { HomePage } from "./pages/HomePage";
import { RoadmapPage } from "./pages/RoadmapPage";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <BrowserRouter>
      <div className="flex h-full bg-white">
        {/* Desktop sidebar */}
        <div className="hidden md:flex md:flex-shrink-0">
          <SessionSidebar />
        </div>

        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div className="md:hidden fixed inset-0 z-40 flex">
            <div
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setSidebarOpen(false)}
            />
            <div className="relative z-50 flex-shrink-0">
              <SessionSidebar onClose={() => setSidebarOpen(false)} />
            </div>
          </div>
        )}

        <main className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* Mobile top bar */}
          <div className="md:hidden flex items-center gap-3 px-4 py-3 border-b border-zinc-100 bg-blue-950 flex-shrink-0">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-1.5 rounded-lg text-zinc-300 hover:bg-white/10 transition-colors"
              aria-label="Open menu"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" />
              </svg>
            </button>
            <span className="text-sm font-semibold tracking-tight text-white">Skill-Bridge</span>
          </div>

          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/roadmap" element={<RoadmapPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
      <NotificationToast />
    </BrowserRouter>
  );
}

export default App;
