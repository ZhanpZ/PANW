import { useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { SessionSidebar } from "./components/SessionSidebar";
import { NotificationToast } from "./components/NotificationToast";
import { HomePage } from "./pages/HomePage";
import { RoadmapPage } from "./pages/RoadmapPage";

function HamburgerIcon() {
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
    </svg>
  );
}

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <BrowserRouter>
      <div className="flex h-full bg-gray-50">
        {/* Desktop sidebar — always visible on md+ */}
        <div className="hidden md:flex md:flex-shrink-0">
          <SessionSidebar />
        </div>

        {/* Mobile sidebar — overlay drawer */}
        {sidebarOpen && (
          <div className="md:hidden fixed inset-0 z-40 flex">
            {/* Backdrop */}
            <div
              className="absolute inset-0 bg-black/50"
              onClick={() => setSidebarOpen(false)}
            />
            {/* Drawer */}
            <div className="relative z-50 flex-shrink-0">
              <SessionSidebar onClose={() => setSidebarOpen(false)} />
            </div>
          </div>
        )}

        <main className="flex-1 flex flex-col overflow-hidden min-w-0">
          {/* Mobile top bar */}
          <div className="md:hidden flex items-center gap-3 px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-1.5 rounded-md text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label="Open menu"
            >
              <HamburgerIcon />
            </button>
            <span className="text-sm font-semibold text-gray-800">Skill-Bridge</span>
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
