import { useEffect } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useRoadmapStore } from "../../store/roadmapStore";
import type { MasteryLevel } from "../../types";
import { MASTERY_COLORS, toFlowEdges, toFlowNodes } from "./nodeUtils";
import { SkillNode } from "./SkillNode";

// Must be defined OUTSIDE the component to avoid re-renders
const nodeTypes = { skillNode: SkillNode };

export function RoadmapCanvas() {
  const { roadmap } = useRoadmapStore();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  useEffect(() => {
    if (roadmap?.skill_nodes) {
      setNodes(toFlowNodes(roadmap.skill_nodes));
      setEdges(toFlowEdges(roadmap.skill_nodes));
    }
  }, [roadmap, setNodes, setEdges]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.15 }}
      minZoom={0.1}
      maxZoom={2}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#e2e8f0" gap={20} />
      <Controls showInteractive={false} />
      <MiniMap
        nodeColor={(node: Node) => {
          const mastery = (node.data?.mastery_level as MasteryLevel) ?? "LACK";
          return MASTERY_COLORS[mastery].border;
        }}
        maskColor="rgba(0,0,0,0.08)"
        style={{ border: "1px solid #e2e8f0" }}
        className="hidden sm:block"
      />
    </ReactFlow>
  );
}
