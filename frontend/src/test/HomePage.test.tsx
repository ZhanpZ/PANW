import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { HomePage } from "../pages/HomePage";

// ── Hoisted mocks (vi.mock is hoisted above variable declarations) ─────────────
const { mockAddToast, mockCreateSession, mockStartPolling, mockClearRoadmap, mockGenerate, mockNavigate } =
  vi.hoisted(() => ({
    mockAddToast: vi.fn(),
    mockCreateSession: vi.fn(),
    mockStartPolling: vi.fn(),
    mockClearRoadmap: vi.fn(),
    mockGenerate: vi.fn(),
    mockNavigate: vi.fn(),
  }));

// ── Store mocks ───────────────────────────────────────────────────────────────
vi.mock("../store/sessionStore", () => ({
  useSessionStore: () => ({
    activeSessionId: 1,
    createSession: mockCreateSession,
  }),
}));

vi.mock("../store/roadmapStore", () => ({
  useRoadmapStore: () => ({
    startPolling: mockStartPolling,
    clearRoadmap: mockClearRoadmap,
  }),
}));

vi.mock("../store/uiStore", () => ({
  useUiStore: () => ({
    addToast: mockAddToast,
  }),
}));

// ── API client mock ───────────────────────────────────────────────────────────
vi.mock("../api/client", () => ({
  roadmapApi: {
    generate: mockGenerate,
  },
}));

// ── react-router-dom navigate mock ────────────────────────────────────────────
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

// ── pdfjs-dist mock (web worker unavailable in jsdom) ────────────────────────
vi.mock("pdfjs-dist", () => ({
  default: { GlobalWorkerOptions: { workerSrc: "" } },
  GlobalWorkerOptions: { workerSrc: "" },
  getDocument: vi.fn(),
}));

// ── mammoth mock ──────────────────────────────────────────────────────────────
vi.mock("mammoth", () => ({
  default: { extractRawText: vi.fn() },
}));

// ── Helper ────────────────────────────────────────────────────────────────────
function renderHomePage() {
  return render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("HomePage form", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Happy path ----------------------------------------------------------------

  it("renders the resume section and submit button", () => {
    renderHomePage();
    expect(screen.getByText("Resume")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Generate My Roadmap" })
    ).toBeInTheDocument();
  });

  it("calls roadmapApi.generate and navigates when form is filled and submitted", async () => {
    mockGenerate.mockResolvedValueOnce({ data: { job_id: 42, status: "pending" } });

    renderHomePage();

    const textareas = screen.getAllByRole("textbox");
    fireEvent.change(textareas[0], {
      target: { value: "Software engineer with 5 years of experience in Python." },
    });

    fireEvent.click(screen.getByRole("button", { name: "Generate My Roadmap" }));

    await waitFor(() => {
      expect(mockGenerate).toHaveBeenCalledOnce();
    });
    expect(mockStartPolling).toHaveBeenCalledWith(42);
    expect(mockNavigate).toHaveBeenCalledWith("/roadmap");
  });

  // Edge case -----------------------------------------------------------------

  it("shows an error toast when resume is empty on submit", async () => {
    renderHomePage();

    fireEvent.click(screen.getByRole("button", { name: "Generate My Roadmap" }));

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith(
        "Please provide your resume (paste or upload a file).",
        "error"
      );
    });
    expect(mockGenerate).not.toHaveBeenCalled();
  });

  // Standardized --------------------------------------------------------------

  it("shows an error toast when custom job title is blank on submit", async () => {
    renderHomePage();

    const textareas = screen.getAllByRole("textbox");
    fireEvent.change(textareas[0], { target: { value: "My resume content" } });

    const select = screen.getByRole("combobox");
    fireEvent.change(select, { target: { value: "__custom__" } });

    // Leave custom title blank and submit
    fireEvent.click(screen.getByRole("button", { name: "Generate My Roadmap" }));

    await waitFor(() => {
      expect(mockAddToast).toHaveBeenCalledWith("Please enter a job title.", "error");
    });
    expect(mockGenerate).not.toHaveBeenCalled();
  });
});
