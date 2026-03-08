import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as pdfjsLib from "pdfjs-dist";
import mammoth from "mammoth";
import { roadmapApi } from "../api/client";
import { useSessionStore } from "../store/sessionStore";
import { useRoadmapStore } from "../store/roadmapStore";
import { useUiStore } from "../store/uiStore";

// Use local worker bundled by Vite
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.mjs",
  import.meta.url
).toString();

const JOB_TITLES = [
  "Cloud Engineer",
  "Data Engineer",
  "Full Stack Engineer",
  "Backend Engineer",
  "Frontend Engineer",
  "ML Engineer",
  "DevOps Engineer",
  "Site Reliability Engineer",
];

type InputMode = "paste" | "file";

async function extractTextFromFile(file: File): Promise<string> {
  const ext = file.name.split(".").pop()?.toLowerCase();

  if (ext === "json") {
    const text = await file.text();
    try {
      const parsed = JSON.parse(text);
      return typeof parsed === "string" ? parsed : JSON.stringify(parsed, null, 2);
    } catch {
      return text;
    }
  }

  if (ext === "pdf") {
    const arrayBuffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    const pages: string[] = [];
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i);
      const content = await page.getTextContent();
      pages.push(content.items.map((item: unknown) => (item as { str: string }).str).join(" "));
    }
    return pages.join("\n");
  }

  if (ext === "doc" || ext === "docx") {
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.extractRawText({ arrayBuffer });
    return result.value;
  }

  throw new Error(`Unsupported file type: .${ext}`);
}

interface FileInputFieldProps {
  label: string;
  required?: boolean;
  mode: InputMode;
  onModeChange: (m: InputMode) => void;
  text: string;
  onTextChange: (t: string) => void;
  textPlaceholder: string;
  textRows: number;
  fileLabel?: string;
  onFileError: (msg: string) => void;
}

function FileInputField({
  label,
  required,
  mode,
  onModeChange,
  text,
  onTextChange,
  textPlaceholder,
  textRows,
  fileLabel,
  onFileError,
}: FileInputFieldProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [parsing, setParsing] = useState(false);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setParsing(true);
    try {
      const extracted = await extractTextFromFile(file);
      onTextChange(extracted);
      setFileName(file.name);
    } catch (err: unknown) {
      onFileError((err as Error).message ?? "Failed to parse file.");
    } finally {
      setParsing(false);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-[13px] font-medium text-zinc-700">
          {label}
          {required
            ? <span className="ml-1 text-rose-500">*</span>
            : <span className="ml-1 text-zinc-400 font-normal text-[12px]">optional</span>
          }
        </label>
        {/* Mode toggle */}
        <div className="flex rounded-lg border border-zinc-200 overflow-hidden text-[11px] font-medium">
          <button
            type="button"
            onClick={() => onModeChange("paste")}
            className={`px-3 py-1 transition-colors ${
              mode === "paste"
                ? "bg-blue-950 text-white"
                : "bg-white text-zinc-500 hover:text-zinc-800"
            }`}
          >
            Paste
          </button>
          <button
            type="button"
            onClick={() => { onModeChange("file"); fileRef.current?.click(); }}
            className={`px-3 py-1 border-l border-zinc-200 transition-colors ${
              mode === "file"
                ? "bg-blue-950 text-white"
                : "bg-white text-zinc-500 hover:text-zinc-800"
            }`}
          >
            Upload
          </button>
        </div>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".json,.pdf,.doc,.docx"
        className="hidden"
        onChange={handleFile}
      />

      {mode === "file" ? (
        <div
          onClick={() => fileRef.current?.click()}
          className="w-full border border-dashed border-zinc-300 rounded-xl px-4 py-8
            flex flex-col items-center justify-center gap-2 cursor-pointer
            hover:border-orange-500 hover:bg-orange-50/40 transition-all duration-200"
        >
          {parsing ? (
            <p className="text-[13px] text-orange-500 animate-pulse">Parsing file…</p>
          ) : fileName ? (
            <>
              <div className="w-9 h-9 rounded-full bg-emerald-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-[13px] font-medium text-zinc-700">{fileName}</p>
              <p className="text-[11px] text-zinc-400">Click to replace</p>
            </>
          ) : (
            <>
              <div className="w-9 h-9 rounded-full bg-zinc-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
              </div>
              <p className="text-[13px] text-zinc-600">{fileLabel ?? "Click to upload"}</p>
              <p className="text-[11px] text-zinc-400">.pdf, .doc, .docx, .json</p>
            </>
          )}
        </div>
      ) : (
        <textarea
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          rows={textRows}
          placeholder={textPlaceholder}
          className="w-full border border-zinc-200 rounded-xl px-4 py-3 text-[13px] text-zinc-800
            focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500
            resize-y font-mono leading-relaxed placeholder-zinc-400 transition-all"
        />
      )}

      {mode === "file" && text && !parsing && (
        <details className="mt-1">
          <summary className="text-[11px] text-zinc-400 cursor-pointer hover:text-zinc-600 transition-colors">
            Preview extracted text ({text.length} chars)
          </summary>
          <pre className="mt-1 text-[11px] text-zinc-500 bg-zinc-50 border border-zinc-200 rounded-lg
            p-3 max-h-28 overflow-y-auto whitespace-pre-wrap">
            {text.slice(0, 800)}{text.length > 800 ? "\n…" : ""}
          </pre>
        </details>
      )}
    </div>
  );
}

export function HomePage() {
  const { activeSessionId, createSession } = useSessionStore();
  const { startPolling, clearRoadmap } = useRoadmapStore();
  const { addToast } = useUiStore();
  const navigate = useNavigate();

  const [resumeText, setResumeText] = useState("");
  const [resumeMode, setResumeMode] = useState<InputMode>("paste");
  const [githubSummaries, setGithubSummaries] = useState("");
  const [githubMode, setGithubMode] = useState<InputMode>("paste");
  const [jobTitle, setJobTitle] = useState("Cloud Engineer");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeText.trim()) {
      addToast("Please provide your resume (paste or upload a file).", "error");
      return;
    }
    if (!jobTitle) {
      addToast("Please select a job title.", "error");
      return;
    }

    setSubmitting(true);
    try {
      let sessionId = activeSessionId;
      if (!sessionId) {
        const s = await createSession(`Session ${new Date().toLocaleDateString()}`);
        sessionId = s.id;
      }

      clearRoadmap();
      const res = await roadmapApi.generate({
        session_id: sessionId,
        resume_text: resumeText,
        github_summaries: githubSummaries,
        job_title: jobTitle,
      });

      startPolling(res.data.job_id);
      navigate("/roadmap");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Failed to start roadmap generation.";
      addToast(msg, "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-white">
      {/* Hero */}
      <div className="border-b border-zinc-100 px-8 py-10">
        <p className="text-[11px] font-semibold text-orange-500 uppercase tracking-widest mb-2">
          Career Navigator
        </p>
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 mb-2">
          Build your skill roadmap
        </h1>
        <p className="text-[13px] text-zinc-500 max-w-md leading-relaxed">
          Upload your resume and GitHub summaries, pick a target role, and get a personalized
          skill-gap roadmap — instantly.
        </p>
      </div>

      {/* Form */}
      <div className="px-8 py-8">
        <div className="max-w-xl w-full">
          <form onSubmit={handleSubmit} className="space-y-7">
            <FileInputField
              label="Resume"
              required
              mode={resumeMode}
              onModeChange={setResumeMode}
              text={resumeText}
              onTextChange={setResumeText}
              textPlaceholder="Describe your education, work experience, and projects…"
              textRows={9}
              fileLabel="Click to upload your resume"
              onFileError={(msg) => addToast(msg, "error")}
            />

            <FileInputField
              label="GitHub Project Summaries"
              mode={githubMode}
              onModeChange={setGithubMode}
              text={githubSummaries}
              onTextChange={setGithubSummaries}
              textPlaceholder="Describe your repos: tech stack, what the project does, your role…"
              textRows={4}
              fileLabel="Click to upload GitHub summaries"
              onFileError={(msg) => addToast(msg, "error")}
            />

            {/* Job title */}
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-zinc-700">
                Target Job Title <span className="text-rose-500">*</span>
              </label>
              <select
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                className="w-full border border-zinc-200 rounded-xl px-4 py-3 text-[13px] text-zinc-800
                  focus:outline-none focus:ring-2 focus:ring-orange-500/30 focus:border-orange-500
                  bg-white appearance-none transition-all"
              >
                {JOB_TITLES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-orange-500 hover:bg-orange-600 active:bg-orange-700 disabled:opacity-40
                text-white font-medium rounded-xl px-4 py-3 transition-colors text-[13px]
                tracking-wide"
            >
              {submitting ? "Starting…" : "Generate Roadmap"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
