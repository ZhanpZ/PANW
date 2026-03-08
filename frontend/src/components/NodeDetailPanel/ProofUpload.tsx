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
    <div>
      {/* Existing uploads */}
      {uploads.length > 0 && (
        <ul className="mb-3 space-y-1">
          {uploads.map((u) => (
            <li key={u.id} className="flex items-center justify-between text-sm bg-gray-50 rounded px-2 py-1">
              <span className="truncate text-gray-700">{u.filename ?? "file"}</span>
              <button
                onClick={() => handleDelete(u.id)}
                className="ml-2 text-xs text-red-400 hover:text-red-600 flex-shrink-0"
              >
                remove
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
        className="w-full text-xs border border-gray-200 rounded px-2 py-1 mb-2 focus:outline-none focus:ring-1 focus:ring-blue-400"
      />
      <label className={`inline-flex items-center gap-2 cursor-pointer text-xs font-medium
        px-3 py-1.5 rounded border transition-colors
        ${uploading ? "opacity-50 cursor-default" : "hover:bg-gray-100 border-gray-300"}`}>
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          onChange={handleUpload}
          disabled={uploading}
        />
        {uploading ? "Uploading…" : "Upload proof of work"}
      </label>
    </div>
  );
}
