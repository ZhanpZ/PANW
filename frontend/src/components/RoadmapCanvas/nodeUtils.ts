import { MarkerType, type Edge, type Node } from "@xyflow/react";
import type { MasteryLevel, SkillNode } from "../../types";

export const MASTERY_COLORS: Record<MasteryLevel, { bg: string; border: string; text: string }> =
  {
    DONE: { bg: "#f0fdf4", border: "#34d399", text: "#059669" },
    LACK: { bg: "#fff1f2", border: "#fb7185", text: "#e11d48" },
  };

// Edge colors: green when target is DONE, red when target is LACK
const EDGE_COLORS: Record<MasteryLevel, string> = {
  DONE: "#34d399",
  LACK: "#fb7185",
};

export function toFlowNodes(skillNodes: SkillNode[]): Node[] {
  return skillNodes.map((node) => ({
    id: String(node.id),
    type: "skillNode",
    position: { x: node.position_x, y: node.position_y },
    data: { ...node },
  }));
}

export function toFlowEdges(skillNodes: SkillNode[]): Edge[] {
  return skillNodes
    .filter((node) => node.parent_id !== null)
    .map((node) => {
      const color = EDGE_COLORS[node.mastery_level as MasteryLevel] ?? "#94a3b8";
      return {
        id: `edge-${node.parent_id}-${node.id}`,
        source: String(node.parent_id),
        target: String(node.id),
        type: "smoothstep",
        style: { stroke: color, strokeWidth: 2.5 },
        animated: node.mastery_level === "LACK",
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 18,
          height: 18,
          color,
        },
        label: undefined,
      };
    });
}
