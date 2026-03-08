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
  "Mobile Engineer",
  "Security Engineer",
];

type InputMode = "paste" | "file";

async function extractTextFromFile(file: File): Promise<string> {
  const ext = file.name.split(".").pop()?.toLowerCase();

  if (ext === "json") {
    const text = await file.text();
    try {
      const parsed = JSON.parse(text);
      // If it's an object/array, pretty-print it so the LLM can read it
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
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="block text-sm font-medium text-gray-700">
          {label} {required && <span className="text-red-500">*</span>}
          {!required && <span className="text-gray-400 font-normal"> (optional)</span>}
        </label>
        {/* Toggle */}
        <div className="flex rounded-md border border-gray-300 overflow-hidden text-xs">
          <button
            type="button"
            onClick={() => onModeChange("paste")}
            className={`px-3 py-1 transition-colors ${
              mode === "paste"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Paste Text
          </button>
          <button
            type="button"
            onClick={() => { onModeChange("file"); fileRef.current?.click(); }}
            className={`px-3 py-1 border-l border-gray-300 transition-colors ${
              mode === "file"
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Upload File
          </button>
        </div>
      </div>

      {/* Hidden file input */}
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
          className="w-full border-2 border-dashed border-gray-300 rounded-lg px-4 py-8
            flex flex-col items-center justify-center gap-2 cursor-pointer
            hover:border-blue-400 hover:bg-blue-50 transition-colors"
        >
          {parsing ? (
            <p className="text-sm text-blue-600 animate-pulse">Parsing file…</p>
          ) : fileName ? (
            <>
              <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <p className="text-sm font-medium text-gray-700">{fileName}</p>
              <p className="text-xs text-gray-400">Click to replace</p>
            </>
          ) : (
            <>
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              <p className="text-sm text-gray-600">
                {fileLabel ?? "Click to upload"}
              </p>
              <p className="text-xs text-gray-400">.json, .pdf, .doc, .docx</p>
            </>
          )}
        </div>
      ) : (
        <textarea
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          rows={textRows}
          placeholder={textPlaceholder}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y font-mono"
        />
      )}

      {/* Show extracted preview when file mode has content */}
      {mode === "file" && text && !parsing && (
        <details className="mt-2">
          <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
            Preview extracted text ({text.length} chars)
          </summary>
          <pre className="mt-1 text-xs text-gray-600 bg-gray-100 rounded p-2 max-h-32 overflow-y-auto whitespace-pre-wrap">
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
  const [customJobTitle, setCustomJobTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const effectiveJobTitle = jobTitle === "__custom__" ? customJobTitle.trim() : jobTitle;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeText.trim()) {
      addToast("Please provide your resume (paste or upload a file).", "error");
      return;
    }
    if (!effectiveJobTitle) {
      addToast("Please enter a job title.", "error");
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
        job_title: effectiveJobTitle,
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
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 bg-gray-50">
      <div className="max-w-2xl mx-auto w-full">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">
          Skill-Bridge Career Navigator
        </h1>
        <p className="text-gray-500 text-sm mb-8">
          Paste or upload your resume and GitHub summaries, choose a target role, and get a
          personalized skill-gap roadmap.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Resume */}
          <FileInputField
            label="Resume"
            required
            mode={resumeMode}
            onModeChange={setResumeMode}
            text={resumeText}
            onTextChange={setResumeText}
            textPlaceholder="Describe your resume: education, work experience, projects"
            textRows={10}
            fileLabel="Click to upload your resume"
            onFileError={(msg) => addToast(msg, "error")}
          />

          {/* GitHub summaries */}
          <FileInputField
            label="GitHub Project Summaries"
            mode={githubMode}
            onModeChange={setGithubMode}
            text={githubSummaries}
            onTextChange={setGithubSummaries}
            textPlaceholder="Describe your GitHub repos: tech stack, what the project does, your role…"
            textRows={5}
            fileLabel="Click to upload GitHub summaries"
            onFileError={(msg) => addToast(msg, "error")}
          />

          {/* Job title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Target Job Title <span className="text-red-500">*</span>
            </label>
            <select
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            >
              {JOB_TITLES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
              <option value="__custom__">Other (type below)…</option>
            </select>
            {jobTitle === "__custom__" && (
              <input
                type="text"
                value={customJobTitle}
                onChange={(e) => setCustomJobTitle(e.target.value)}
                placeholder="e.g. Embedded Systems Engineer"
                className="mt-2 w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            )}
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50
              text-white font-semibold rounded-lg px-4 py-3 transition-colors text-sm"
          >
            {submitting ? "Starting…" : "Generate My Roadmap"}
          </button>
        </form>
      </div>
    </div>
  );
}
