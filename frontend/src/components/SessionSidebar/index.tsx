import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useSessionStore } from "../../store/sessionStore";
import { useRoadmapStore } from "../../store/roadmapStore";
import { useUiStore } from "../../store/uiStore";

export function SessionSidebar({ onClose }: { onClose?: () => void }) {
  const { sessions, activeSessionId, loading, loadSessions, createSession, deleteSession, setActiveSessionId } =
    useSessionStore();
  const { clearRoadmap } = useRoadmapStore();
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

  const handleSelect = (id: number) => {
    setActiveSessionId(id);
    clearRoadmap();
    navigate("/");
    onClose?.();
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
    <aside className="w-56 flex-shrink-0 bg-gray-900 text-gray-100 flex flex-col h-full">
      <div className="px-4 py-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
          Sessions
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-200 transition-colors p-0.5"
            aria-label="Close menu"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Session list */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <p className="text-xs text-gray-500 px-4 py-3">Loading…</p>
        )}
        {sessions.map((s) => (
          <div
            key={s.id}
            onClick={() => handleSelect(s.id)}
            className={`group flex items-center justify-between px-4 py-3 cursor-pointer text-sm
              transition-colors hover:bg-gray-800
              ${activeSessionId === s.id ? "bg-gray-800 text-white" : "text-gray-300"}`}
          >
            <span className="truncate flex-1">{s.name}</span>
            <button
              onClick={(e) => handleDelete(e, s.id)}
              className="ml-2 opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-opacity text-xs"
              title="Delete session"
            >
              ✕
            </button>
          </div>
        ))}
        {!loading && sessions.length === 0 && (
          <p className="text-xs text-gray-500 px-4 py-3">No sessions yet.</p>
        )}
      </div>

      {/* New session input */}
      <div className="px-3 py-3 border-t border-gray-700">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          placeholder="New session name…"
          className="w-full bg-gray-800 text-gray-200 text-xs rounded px-2 py-1.5 outline-none
            border border-gray-700 focus:border-blue-500 placeholder-gray-600"
        />
        <button
          onClick={handleCreate}
          disabled={creating}
          className="mt-2 w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50
            text-white text-xs font-medium rounded px-2 py-1.5 transition-colors"
        >
          {creating ? "Creating…" : "+ New Session"}
        </button>
      </div>
    </aside>
  );
}
