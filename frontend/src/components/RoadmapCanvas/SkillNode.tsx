import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { MasteryLevel } from "../../types";
import { MASTERY_COLORS } from "./nodeUtils";
import { useUiStore } from "../../store/uiStore";

export function SkillNode({ data, selected }: NodeProps) {
  const mastery = (data.mastery_level as MasteryLevel) ?? "LACK";
  const colors = MASTERY_COLORS[mastery];
  const { setSelectedNodeId } = useUiStore();

  return (
    <>
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div
        onClick={() => setSelectedNodeId(data.id as number)}
        style={{
          backgroundColor: colors.bg,
          borderColor: selected ? "#3b82f6" : colors.border,
        }}
        className={`rounded-xl border-2 p-3 w-52 cursor-pointer select-none
          transition-shadow hover:shadow-lg
          ${selected ? "shadow-lg ring-2 ring-blue-400" : "shadow-sm"}`}
      >
        <p className="font-semibold text-sm leading-tight" style={{ color: colors.text }}>
          {data.skill_name as string}
        </p>
        {data.category != null && (
          <p className="text-xs text-gray-500 mt-0.5 truncate">{String(data.category)}</p>
        )}
        <div className="flex items-center justify-between mt-2">
          <span
            className="text-xs font-bold px-2 py-0.5 rounded-full text-white"
            style={{ backgroundColor: colors.border }}
          >
            {mastery}
          </span>
          {data.estimated_hours != null && (
            <span className="text-xs text-gray-400">{data.estimated_hours as number}h</span>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </>
  );
}
