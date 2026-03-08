import { useCallback, useEffect, useRef, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  useNodes,
  useViewport,
  useReactFlow,
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

type Dirs = { top: boolean; bottom: boolean; left: boolean; right: boolean };

const PAN_STEP = 200; // pixels to pan per click

// Rendered inside ReactFlow so it can access useNodes / useViewport / useReactFlow
function DirectionTracker({
  containerRef,
  onUpdate,
}: {
  containerRef: React.RefObject<HTMLDivElement>;
  onUpdate: (dirs: Dirs, pan: (dx: number, dy: number) => void) => void;
}) {
  const nodes = useNodes();
  const { x, y, zoom } = useViewport();
  const { setViewport, getViewport } = useReactFlow();

  const pan = useCallback(
    (dx: number, dy: number) => {
      const vp = getViewport();
      setViewport({ ...vp, x: vp.x + dx, y: vp.y + dy }, { duration: 200 });
    },
    [getViewport, setViewport]
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el || nodes.length === 0) return;
    const { width: W, height: H } = el.getBoundingClientRect();

    const dirs: Dirs = { top: false, bottom: false, left: false, right: false };
    nodes.forEach((node) => {
      const sx = node.position.x * zoom + x;
      const sy = node.position.y * zoom + y;
      const nw = ((node.measured?.width as number) ?? 200) * zoom;
      const nh = ((node.measured?.height as number) ?? 60) * zoom;

      if (sx + nw < 0) dirs.left = true;
      if (sx > W) dirs.right = true;
      if (sy + nh < 0) dirs.top = true;
      if (sy > H) dirs.bottom = true;
    });
    onUpdate(dirs, pan);
  }, [nodes, x, y, zoom, containerRef, onUpdate, pan]);

  return null;
}

const ARROW_BASE =
  "absolute z-10 flex items-center justify-center cursor-pointer " +
  "text-white font-bold select-none transition-opacity duration-300";

function OffscreenArrows({
  dirs,
  pan,
}: {
  dirs: Dirs;
  pan: (dx: number, dy: number) => void;
}) {
  return (
    <>
      {dirs.top && (
        <div
          className={`${ARROW_BASE} top-2 left-1/2 -translate-x-1/2`}
          style={{ width: 36, height: 36 }}
          onClick={() => pan(0, PAN_STEP)}
        >
          <span
            className="flex items-center justify-center rounded-full bg-zinc-600/70 backdrop-blur-sm shadow hover:bg-zinc-500/90"
            style={{ width: 36, height: 36 }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 19V5M5 12l7-7 7 7" />
            </svg>
          </span>
        </div>
      )}
      {dirs.bottom && (
        <div
          className={`${ARROW_BASE} bottom-2 left-1/2 -translate-x-1/2`}
          style={{ width: 36, height: 36 }}
          onClick={() => pan(0, -PAN_STEP)}
        >
          <span
            className="flex items-center justify-center rounded-full bg-zinc-600/70 backdrop-blur-sm shadow hover:bg-zinc-500/90"
            style={{ width: 36, height: 36 }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14M19 12l-7 7-7-7" />
            </svg>
          </span>
        </div>
      )}
      {dirs.left && (
        <div
          className={`${ARROW_BASE} left-2 top-1/2 -translate-y-1/2`}
          style={{ width: 36, height: 36 }}
          onClick={() => pan(PAN_STEP, 0)}
        >
          <span
            className="flex items-center justify-center rounded-full bg-zinc-600/70 backdrop-blur-sm shadow hover:bg-zinc-500/90"
            style={{ width: 36, height: 36 }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
          </span>
        </div>
      )}
      {dirs.right && (
        <div
          className={`${ARROW_BASE} right-2 top-1/2 -translate-y-1/2`}
          style={{ width: 36, height: 36 }}
          onClick={() => pan(-PAN_STEP, 0)}
        >
          <span
            className="flex items-center justify-center rounded-full bg-zinc-600/70 backdrop-blur-sm shadow hover:bg-zinc-500/90"
            style={{ width: 36, height: 36 }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </span>
        </div>
      )}
    </>
  );
}

export function RoadmapCanvas() {
  const { roadmap } = useRoadmapStore();
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [dirs, setDirs] = useState<Dirs>({ top: false, bottom: false, left: false, right: false });
  const [pan, setPan] = useState<(dx: number, dy: number) => void>(() => () => {});
  const containerRef = useRef<HTMLDivElement>(null);

  const handleDirsUpdate = useCallback((newDirs: Dirs, panFn: (dx: number, dy: number) => void) => {
    setDirs((prev) => {
      if (
        prev.top === newDirs.top &&
        prev.bottom === newDirs.bottom &&
        prev.left === newDirs.left &&
        prev.right === newDirs.right
      )
        return prev;
      return newDirs;
    });
    setPan(() => panFn);
  }, []);

  useEffect(() => {
    if (roadmap?.skill_nodes) {
      setNodes(toFlowNodes(roadmap.skill_nodes));
      setEdges(toFlowEdges(roadmap.skill_nodes));
    }
  }, [roadmap, setNodes, setEdges]);

  return (
    <div ref={containerRef} className="relative w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2, minZoom: 0.65 }}
        minZoom={0.1}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
        elevateEdgesOnSelect
        defaultEdgeOptions={{
          type: "smoothstep",
          style: { strokeWidth: 2.5 },
        }}
      >
        <Background color="#f1f5f9" gap={24} size={1} />
        <Controls
          showInteractive={false}
          style={{
            boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
            borderRadius: "10px",
            border: "1px solid #e4e4e7",
            overflow: "hidden",
          }}
        />
        <MiniMap
          nodeColor={(node: Node) => {
            const mastery = (node.data?.mastery_level as MasteryLevel) ?? "LACK";
            return MASTERY_COLORS[mastery].border;
          }}
          maskColor="rgba(0,0,0,0.05)"
          style={{
            border: "1px solid #e4e4e7",
            borderRadius: "10px",
            overflow: "hidden",
          }}
          className="hidden sm:block"
        />
        <DirectionTracker containerRef={containerRef} onUpdate={handleDirsUpdate} />
      </ReactFlow>
      <OffscreenArrows dirs={dirs} pan={pan} />
    </div>
  );
}
