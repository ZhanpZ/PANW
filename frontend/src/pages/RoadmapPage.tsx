import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useRoadmapStore } from "../store/roadmapStore";
import { useSessionStore } from "../store/sessionStore";
import { RoadmapCanvas } from "../components/RoadmapCanvas";
import { NodeDetailPanel } from "../components/NodeDetailPanel";

const STATUS_MESSAGES = [
  "Parsing your resume…",
  "Analyzing job requirements…",
  "Identifying skill gaps…",
  "Generating your personalized roadmap…",
  "Almost there…",
];

function LoadingOverlay({ jobTitle }: { jobTitle?: string }) {
  const [msgIdx, setMsgIdx] = useState(0);
  const elapsed = useRef(0);

  useEffect(() => {
    const tick = setInterval(() => {
      elapsed.current += 1;
      // Advance message roughly every 15s
      const next = Math.min(Math.floor(elapsed.current / 15), STATUS_MESSAGES.length - 1);
      setMsgIdx(next);
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  return (
    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center
      bg-white/80 backdrop-blur-sm">
      <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4" />
      <p className="text-gray-700 font-medium text-sm">{STATUS_MESSAGES[msgIdx]}</p>
      {jobTitle && (
        <p className="text-gray-400 text-xs mt-1">Target role: {jobTitle}</p>
      )}
    </div>
  );
}

export function RoadmapPage() {
  const { roadmap, jobError, isPolling, clearRoadmap } = useRoadmapStore();
  const { activeSessionId } = useSessionStore();
  const navigate = useNavigate();

  // If no session and no roadmap in progress, redirect home
  useEffect(() => {
    if (!activeSessionId && !isPolling && !roadmap) {
      navigate("/");
    }
  }, [activeSessionId, isPolling, roadmap, navigate]);

  const jobTitle = roadmap?.skill_nodes[0]
    ? undefined
    : undefined; // We don't store job title in roadmap store; shown generically

  return (
    <div className="flex-1 relative overflow-hidden">
      {/* Polling overlay */}
      {isPolling && <LoadingOverlay jobTitle={jobTitle} />}

      {/* Error state */}
      {jobError && !isPolling && !roadmap && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white/90">
          <p className="text-red-600 font-medium mb-2">Roadmap generation failed.</p>
          <p className="text-sm text-gray-500 mb-4 max-w-sm text-center">{jobError}</p>
          <div className="flex gap-3">
            <button
              onClick={() => { clearRoadmap(); navigate("/"); }}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-500"
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isPolling && !roadmap && !jobError && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
          No roadmap yet.{" "}
          <button className="ml-1 text-blue-500 hover:underline" onClick={() => navigate("/")}>
            Generate one
          </button>
        </div>
      )}

      {/* Canvas */}
      {roadmap && (
        <div className="w-full h-full">
          <RoadmapCanvas />
        </div>
      )}

      {/* Node detail panel */}
      <NodeDetailPanel />
    </div>
  );
}
