import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { roadmapApi } from "../api/client";
import { useSessionStore } from "../store/sessionStore";
import { useRoadmapStore } from "../store/roadmapStore";
import { useUiStore } from "../store/uiStore";

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

export function HomePage() {
  const { activeSessionId, createSession } = useSessionStore();
  const { startPolling, clearRoadmap } = useRoadmapStore();
  const { addToast } = useUiStore();
  const navigate = useNavigate();

  const [resumeText, setResumeText] = useState("");
  const [githubSummaries, setGithubSummaries] = useState("");
  const [jobTitle, setJobTitle] = useState("Cloud Engineer");
  const [customJobTitle, setCustomJobTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const effectiveJobTitle = jobTitle === "__custom__" ? customJobTitle.trim() : jobTitle;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resumeText.trim()) {
      addToast("Please paste your resume text.", "error");
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
    <div className="flex-1 overflow-y-auto p-8 bg-gray-50">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-800 mb-1">
          Skill-Bridge Career Navigator
        </h1>
        <p className="text-gray-500 text-sm mb-8">
          Paste your resume and GitHub summaries, choose a target role, and get a
          personalized skill-gap roadmap.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Resume */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resume <span className="text-red-500">*</span>
            </label>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={10}
              placeholder="Paste your resume text here…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y font-mono"
            />
          </div>

          {/* GitHub summaries */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              GitHub Project Summaries{" "}
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              value={githubSummaries}
              onChange={(e) => setGithubSummaries(e.target.value)}
              rows={5}
              placeholder="Describe your GitHub repos: tech stack, what the project does, your role…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </div>

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
