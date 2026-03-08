import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { roadmapApi } from "../../api/client";
import { useSessionStore } from "../../store/sessionStore";
import { useRoadmapStore } from "../../store/roadmapStore";
import { useUiStore } from "../../store/uiStore";


export function SessionSidebar({ onClose }: { onClose?: () => void }) {
  const { sessions, activeSessionId, loading, loadSessions, createSession, deleteSession, setActiveSessionId } =
    useSessionStore();
  const { clearRoadmap, setRoadmap, sessionJobTitles } = useRoadmapStore();
  const { addToast } = useUiStore();
  const navigate = useNavigate();
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleCreate = async () => {
    const name = newName.trim() || `Session ${new Date().toLocaleDateString()}`;
    setCreating(true);
    try {
      await createSession(name);
      setNewName("");
      clearRoadmap();
      navigate("/");
    } catch {
      addToast("Failed to create session.", "error");
    } finally {
      setCreating(false);
    }
  };

  const handleSelect = async (id: number) => {
    setActiveSessionId(id);
    clearRoadmap();
    onClose?.();
    try {
      const res = await roadmapApi.getBySession(id);
      // Session has a completed roadmap — load it directly
      setRoadmap(res.data);
      navigate("/roadmap");
    } catch {
      // No completed roadmap yet — go to home to generate one
      navigate("/");
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      await deleteSession(id);
      clearRoadmap();
      navigate("/");
    } catch {
      addToast("Failed to delete session.", "error");
    }
  };

  return (
    <aside className="w-56 flex-shrink-0 bg-blue-950 text-zinc-100 flex flex-col h-full">
      {/* Header */}
      <div className="px-5 pt-6 pb-4 flex items-start justify-between">
        <div>
          <p className="text-[10px] font-semibold text-sky-400 uppercase tracking-widest mb-1">
            Skill-Bridge
          </p>
          <h2 className="text-[13px] font-medium text-zinc-300">Sessions</h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="mt-0.5 text-zinc-500 hover:text-zinc-200 transition-colors"
            aria-label="Close menu"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <div className="mx-5 h-px bg-blue-800/60 mb-1" />

      {/* Session list */}
      <div className="flex-1 overflow-y-auto py-2">
        {loading && (
          <p className="text-[11px] text-zinc-500 px-5 py-3">Loading…</p>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            onClick={() => handleSelect(s.id)}
            className={`group relative flex items-center justify-between px-5 py-2.5 cursor-pointer
              transition-all duration-150
              ${activeSessionId === s.id
                ? "bg-white/10 text-zinc-100"
                : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200"
              }`}
          >
            {activeSessionId === s.id && (
              <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 bg-orange-500 rounded-r-full" />
            )}
            <span className="flex-1 min-w-0">
              <span className="block truncate text-[13px]">{s.name}</span>
              {sessionJobTitles[s.id] && (
                <span className="block truncate text-[10px] text-zinc-500 mt-0.5">
                  {sessionJobTitles[s.id]}
                </span>
              )}
            </span>
            <button
              onClick={(e) => handleDelete(e, s.id)}
              className="ml-2 opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400
                transition-all duration-150 flex-shrink-0"
              title="Delete session"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
        {!loading && sessions.length === 0 && (
          <p className="text-[11px] text-zinc-500 px-5 py-3">No sessions yet.</p>
        )}
      </div>

      {/* New session */}
      <div className="px-4 py-4 border-t border-blue-800/60">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          placeholder="Session name…"
          className="w-full bg-blue-900 text-zinc-200 text-[12px] rounded-lg px-3 py-2
            border border-blue-800 focus:outline-none focus:border-orange-500
            placeholder-zinc-600 transition-colors"
        />
        <button
          onClick={handleCreate}
          disabled={creating}
          className="mt-2 w-full bg-orange-500 hover:bg-orange-400 active:bg-orange-600
            disabled:opacity-40 text-white text-[12px] font-medium rounded-lg px-3 py-2
            transition-colors"
        >
          {creating ? "Creating…" : "+ New Session"}
        </button>
      </div>
    </aside>
  );
}
