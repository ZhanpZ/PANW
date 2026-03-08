import { useUiStore } from "../../store/uiStore";
import { useRoadmapStore } from "../../store/roadmapStore";
import type { MasteryLevel } from "../../types";
import { MASTERY_COLORS } from "../RoadmapCanvas/nodeUtils";
import { ResourceList } from "./ResourceList";

export function NodeDetailPanel() {
  const { selectedNodeId, isPanelOpen, setIsPanelOpen } = useUiStore();
  const { roadmap, updateNodeMastery } = useRoadmapStore();
  const { addToast } = useUiStore();

  const node = roadmap?.skill_nodes.find((n) => n.id === selectedNodeId);

  const handleMarkDone = async () => {
    if (!node) return;
    try {
      await updateNodeMastery(node.id, "DONE");
      addToast(`${node.skill_name} marked as DONE.`, "success");
    } catch {
      addToast("Failed to update mastery.", "error");
    }
  };

  if (!node) return null;

  const mastery = node.mastery_level as MasteryLevel;
  const isDone = mastery === "DONE";

  return (
    <>
      {isPanelOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/10 backdrop-blur-[1px]"
          onClick={() => setIsPanelOpen(false)}
        />
      )}

      <div
        className={`fixed right-0 top-0 h-full w-[380px] bg-white border-l border-zinc-100
          shadow-2xl shadow-black/10 z-50 transition-transform duration-300 ease-out flex flex-col
          ${isPanelOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-5 border-b border-zinc-100">
          <div className="flex-1 min-w-0 pr-4">
            <div className="flex items-center gap-2 mb-1.5">
              <span
                className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold
                  tracking-wide
                  ${isDone
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-rose-50 text-rose-600"
                  }`}
              >
                {mastery}
              </span>
              {node.category && (
                <span className="text-[11px] text-zinc-400">{node.category}</span>
              )}
            </div>
            <h2 className="text-[15px] font-semibold text-zinc-900 leading-snug">
              {node.skill_name}
            </h2>
          </div>
          <button
            onClick={() => setIsPanelOpen(false)}
            className="flex-shrink-0 p-1 text-zinc-400 hover:text-zinc-700 rounded-lg
              hover:bg-zinc-100 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {/* Overview */}
          {node.description && (
            <div>
              <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest mb-2">
                Overview
              </p>
              <p className="text-[13px] text-zinc-600 leading-relaxed">{node.description}</p>
            </div>
          )}

          {/* Gap Analysis */}
          {node.reasoning && (
            <div>
              <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest mb-2">
                Gap Analysis
              </p>
              <p className="text-[13px] text-zinc-500 italic leading-relaxed">{node.reasoning}</p>
            </div>
          )}

          {/* Estimated hours */}
          {node.estimated_hours != null && (
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-[13px] text-zinc-500">
                ~{node.estimated_hours} hours to proficiency
              </span>
            </div>
          )}

          {/* Mastery toggle */}
          {!isDone ? (
            <button
              onClick={handleMarkDone}
              className="w-full py-2.5 rounded-xl text-[13px] font-medium transition-all
                border border-emerald-300 text-emerald-700 hover:bg-emerald-50
                hover:border-emerald-400"
            >
              Mark as DONE
            </button>
          ) : (
            <div className="w-full py-2.5 rounded-xl text-[13px] font-medium text-center
              border border-emerald-300 bg-emerald-50 text-emerald-700 flex items-center
              justify-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
              Completed
            </div>
          )}

          {/* Resources */}
          <div>
            <p className="text-[10px] font-semibold text-zinc-400 uppercase tracking-widest mb-3">
              Learning Resources
            </p>
            <ResourceList resources={node.resources} />
          </div>
        </div>
      </div>
    </>
  );
}
