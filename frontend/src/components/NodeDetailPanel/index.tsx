import { useState, useEffect } from "react";
import { useUiStore } from "../../store/uiStore";
import { useRoadmapStore } from "../../store/roadmapStore";
import type { MasteryLevel, ProofUpload as ProofUploadType } from "../../types";
import { MASTERY_COLORS } from "../RoadmapCanvas/nodeUtils";
import { ResourceList } from "./ResourceList";
import { ProofUpload } from "./ProofUpload";

export function NodeDetailPanel() {
  const { selectedNodeId, isPanelOpen, setIsPanelOpen } = useUiStore();
  const { roadmap, updateNodeMastery } = useRoadmapStore();
  const { addToast } = useUiStore();

  const node = roadmap?.skill_nodes.find((n) => n.id === selectedNodeId);
  const [localUploads, setLocalUploads] = useState<ProofUploadType[]>([]);

  useEffect(() => {
    if (node) setLocalUploads(node.proof_uploads ?? []);
  }, [node]);

  const handleMasteryToggle = async () => {
    if (!node) return;
    const next: MasteryLevel = node.mastery_level === "DONE" ? "LACK" : "DONE";
    try {
      await updateNodeMastery(node.id, next);
      addToast(`Mastery updated to ${next}.`, "success");
    } catch {
      addToast("Failed to update mastery.", "error");
    }
  };

  if (!node) return null;

  const mastery = node.mastery_level as MasteryLevel;
  const colors = MASTERY_COLORS[mastery];

  return (
    <>
      {/* Backdrop */}
      {isPanelOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/10"
          onClick={() => setIsPanelOpen(false)}
        />
      )}

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 h-full w-96 bg-white shadow-2xl z-50
          transition-transform duration-300 flex flex-col
          ${isPanelOpen ? "translate-x-0" : "translate-x-full"}`}
      >
        {/* Header */}
        <div
          className="flex items-start justify-between p-5 border-b"
          style={{ backgroundColor: colors.bg }}
        >
          <div className="flex-1 min-w-0">
            <span
              className="inline-block text-xs font-bold px-2 py-0.5 rounded-full text-white mb-1"
              style={{ backgroundColor: colors.border }}
            >
              {mastery}
            </span>
            <h2 className="text-base font-bold text-gray-900 leading-tight">
              {node.skill_name}
            </h2>
            {node.category && (
              <p className="text-xs text-gray-500 mt-0.5">{node.category}</p>
            )}
          </div>
          <button
            onClick={() => setIsPanelOpen(false)}
            className="ml-3 text-gray-400 hover:text-gray-700 text-xl leading-none flex-shrink-0"
          >
            ×
          </button>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Description */}
          {node.description && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Overview
              </p>
              <p className="text-sm text-gray-700 leading-relaxed">{node.description}</p>
            </div>
          )}

          {/* Reasoning */}
          {node.reasoning && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                Gap Analysis
              </p>
              <p className="text-sm text-gray-600 italic leading-relaxed">{node.reasoning}</p>
            </div>
          )}

          {/* Estimated hours */}
          {node.estimated_hours != null && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span className="text-gray-400">⏱</span>
              <span>~{node.estimated_hours} hours to proficiency</span>
            </div>
          )}

          {/* Toggle mastery */}
          <button
            onClick={handleMasteryToggle}
            className={`w-full py-2 rounded-lg text-sm font-medium transition-colors border-2
              ${mastery === "DONE"
                ? "border-red-300 text-red-600 hover:bg-red-50"
                : "border-green-400 text-green-700 hover:bg-green-50"}`}
          >
            {mastery === "DONE" ? "Mark as LACK" : "Mark as DONE"}
          </button>

          {/* Resources */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Learning Resources
            </p>
            <ResourceList resources={node.resources} />
          </div>

          {/* Proof uploads */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Proof of Work
            </p>
            <ProofUpload
              nodeId={node.id}
              uploads={localUploads}
              onUploaded={(u) => setLocalUploads((prev) => [...prev, u])}
              onDeleted={(id) => setLocalUploads((prev) => prev.filter((u) => u.id !== id))}
            />
          </div>
        </div>
      </div>
    </>
  );
}
