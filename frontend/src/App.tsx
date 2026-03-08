import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { SessionSidebar } from "./components/SessionSidebar";
import { NotificationToast } from "./components/NotificationToast";
import { HomePage } from "./pages/HomePage";
import { RoadmapPage } from "./pages/RoadmapPage";

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-full bg-gray-50">
        <SessionSidebar />
        <main className="flex-1 flex flex-col overflow-hidden">
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
