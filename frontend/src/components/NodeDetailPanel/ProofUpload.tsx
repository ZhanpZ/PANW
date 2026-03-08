import { useRef, useState } from "react";
import { uploadApi } from "../../api/client";
import type { ProofUpload as ProofUploadType } from "../../types";
import { useUiStore } from "../../store/uiStore";

interface Props {
  nodeId: number;
  uploads: ProofUploadType[];
  onUploaded: (upload: ProofUploadType) => void;
  onDeleted: (uploadId: number) => void;
}

export function ProofUpload({ nodeId, uploads, onUploaded, onDeleted }: Props) {
  const { addToast } = useUiStore();
  const fileRef = useRef<HTMLInputElement>(null);
  const [notes, setNotes] = useState("");
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await uploadApi.upload(nodeId, file, notes);
      onUploaded(res.data);
      setNotes("");
      addToast("Proof uploaded.", "success");
    } catch {
      addToast("Upload failed.", "error");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleDelete = async (uploadId: number) => {
    try {
      await uploadApi.delete(uploadId);
      onDeleted(uploadId);
      addToast("Upload removed.", "info");
    } catch {
      addToast("Failed to delete upload.", "error");
    }
  };

  return (
    <div className="space-y-3">
      {/* Existing uploads */}
      {uploads.length > 0 && (
        <ul className="space-y-1.5">
          {uploads.map((u) => (
            <li
              key={u.id}
              className="flex items-center justify-between bg-zinc-50 border border-zinc-200
                rounded-lg px-3 py-2"
            >
              <div className="flex items-center gap-2 min-w-0">
                <svg className="w-3.5 h-3.5 text-zinc-400 flex-shrink-0" fill="none"
                  viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                </svg>
                <span className="truncate text-[12px] text-zinc-600">{u.filename ?? "file"}</span>
              </div>
              <button
                onClick={() => handleDelete(u.id)}
                className="ml-2 text-[11px] text-zinc-400 hover:text-rose-500 transition-colors flex-shrink-0"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}

      {/* Upload new */}
      <input
        type="text"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Notes (optional)"
        className="w-full text-[12px] border border-zinc-200 rounded-lg px-3 py-2
          focus:outline-none focus:ring-1 focus:ring-violet-400 focus:border-violet-400
          placeholder-zinc-400 transition-all"
      />
      <label
        className={`flex items-center gap-2 cursor-pointer text-[12px] font-medium
          px-3 py-2 rounded-lg border transition-all
          ${uploading
            ? "opacity-40 cursor-default border-zinc-200 text-zinc-500"
            : "border-zinc-300 text-zinc-600 hover:bg-zinc-50 hover:border-zinc-400"
          }`}
      >
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          onChange={handleUpload}
          disabled={uploading}
        />
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        {uploading ? "Uploading…" : "Upload proof of work"}
      </label>
    </div>
  );
}
