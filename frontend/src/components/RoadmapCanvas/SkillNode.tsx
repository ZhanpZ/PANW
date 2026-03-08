import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { MasteryLevel } from "../../types";
import { useUiStore } from "../../store/uiStore";

export function SkillNode({ data, selected }: NodeProps) {
  const mastery = (data.mastery_level as MasteryLevel) ?? "LACK";
  const isDone = mastery === "DONE";
  const { setSelectedNodeId } = useUiStore();

  return (
    <>
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <div
        onClick={() => setSelectedNodeId(data.id as number)}
        className={`w-48 rounded-2xl border cursor-pointer select-none transition-all duration-150
          hover:shadow-lg hover:-translate-y-0.5
          ${selected ? "ring-2 ring-orange-500 ring-offset-1" : ""}
          ${isDone
            ? "bg-white border-emerald-200 shadow-sm shadow-emerald-100/60"
            : "bg-white border-rose-200 shadow-sm shadow-rose-100/60"
          }`}
      >
        {/* Color stripe */}
        <div
          className={`h-1 rounded-t-2xl
            ${isDone ? "bg-emerald-400" : "bg-rose-400"}`}
        />

        <div className="px-3.5 py-3">
          <p className="font-semibold text-[13px] text-zinc-900 leading-snug">
            {data.skill_name as string}
          </p>
          {data.category != null && (
            <p className="text-[11px] text-zinc-400 mt-0.5 truncate">{String(data.category)}</p>
          )}

          <div className="flex items-center justify-between mt-2.5">
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-md tracking-wide
                ${isDone
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-rose-50 text-rose-600"
                }`}
            >
              {mastery}
            </span>
            {data.estimated_hours != null && (
              <span className="text-[11px] text-zinc-400">
                {data.estimated_hours as number}h
              </span>
            )}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </>
  );
}
