import type { Edge, Node } from "@xyflow/react";
import type { MasteryLevel, SkillNode } from "../../types";

export const MASTERY_COLORS: Record<MasteryLevel, { bg: string; border: string; text: string }> =
  {
    DONE: { bg: "#dcfce7", border: "#16a34a", text: "#15803d" },
    LACK: { bg: "#fee2e2", border: "#dc2626", text: "#991b1b" },
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
    .map((node) => ({
      id: `edge-${node.parent_id}-${node.id}`,
      source: String(node.parent_id),
      target: String(node.id),
      type: "smoothstep",
      style: { stroke: "#94a3b8", strokeWidth: 1.5 },
      animated: node.mastery_level === "LACK",
    }));
}
