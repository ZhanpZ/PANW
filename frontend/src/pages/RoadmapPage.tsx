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
      const next = Math.min(Math.floor(elapsed.current / 15), STATUS_MESSAGES.length - 1);
      setMsgIdx(next);
    }, 1000);
    return () => clearInterval(tick);
  }, []);

  return (
    <div className="absolute inset-0 z-20 flex flex-col items-center justify-center
      bg-white/90 backdrop-blur-sm">
      {/* Spinner ring */}
      <div className="relative w-12 h-12 mb-5">
        <div className="absolute inset-0 rounded-full border-2 border-zinc-200" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent
          border-t-orange-500 animate-spin" />
      </div>
      <p className="text-[14px] font-medium text-zinc-800">{STATUS_MESSAGES[msgIdx]}</p>
      {jobTitle && (
        <p className="text-[12px] text-zinc-400 mt-1">Target role: {jobTitle}</p>
      )}
    </div>
  );
}

export function RoadmapPage() {
  const { roadmap, jobError, isPolling, clearRoadmap } = useRoadmapStore();
  const { activeSessionId } = useSessionStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (!activeSessionId && !isPolling && !roadmap) {
      navigate("/");
    }
  }, [activeSessionId, isPolling, roadmap, navigate]);

  return (
    <div className="flex-1 relative overflow-hidden">
      {isPolling && <LoadingOverlay jobTitle={roadmap?.job_title ?? undefined} />}

      {/* Error state */}
      {jobError && !isPolling && !roadmap && (
        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-white">
          <div className="w-12 h-12 rounded-full bg-rose-50 flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
          </div>
          <p className="text-[15px] font-semibold text-zinc-900 mb-1">Generation failed</p>
          <p className="text-[13px] text-zinc-500 mb-6 max-w-sm text-center">{jobError}</p>
          <button
            onClick={() => { clearRoadmap(); navigate("/"); }}
            className="px-5 py-2 bg-orange-500 text-white text-[13px] font-medium rounded-xl
              hover:bg-orange-600 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isPolling && !roadmap && !jobError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
          <p className="text-[13px] text-zinc-400">No roadmap yet.</p>
          <button
            className="text-[13px] text-orange-500 hover:text-orange-700 font-medium transition-colors"
            onClick={() => navigate("/")}
          >
            Generate one →
          </button>
        </div>
      )}

      {roadmap && (
        <div className="w-full h-full relative">
          {roadmap.job_title && (
            <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 pointer-events-none">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full
                bg-white/90 border border-zinc-200 shadow-sm text-[12px] font-medium text-zinc-600">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500 flex-shrink-0" />
                {roadmap.job_title}
              </span>
            </div>
          )}
          <RoadmapCanvas />
        </div>
      )}

      <NodeDetailPanel />
    </div>
  );
}
