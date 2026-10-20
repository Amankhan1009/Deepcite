"use client";

import Link from "next/link";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  Clock,
  FileText,
  FolderKanban,
  LogOut,
  Plus,
  Sparkles,
  Square,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ApiError, apiFetch } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

type Workspace = {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
};

type ResearchRun = {
  id: string;
  workspace_id: string;
  question: string;
  status: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
};

function formatDuration(
  startedAt?: string | null,
  completedAt?: string | null,
): string {
  if (!startedAt) return "";
  const start = new Date(startedAt).getTime();
  const end = completedAt ? new Date(completedAt).getTime() : Date.now();
  if (isNaN(start) || isNaN(end) || end < start) return "";

  const totalSeconds = Math.max(0, Math.floor((end - start) / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes === 0) {
    return `${seconds}s`;
  }
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
}

function formatElapsed(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

const progressSteps = [
  "Planning",
  "Researching sources",
  "Verifying evidence",
  "Human approval",
  "Generating report",
];

const ACTIVE_EXECUTION_STATUSES = [
  "planning",
  "researching",
  "verifying",
  "reasoning",
  "fact_checking",
  "awaiting_approval",
  "generating_report",
] as const;

const CANCELLABLE_STATUSES = [
  "researching",
  "verifying",
  "reasoning",
  "fact_checking",
  "awaiting_approval",
  "generating_report",
] as const;

const SAMPLE_RESEARCH_PROMPTS = [
  {
    label: "⚡ Speculative Decoding vs Medusa",
    query:
      "What are the latency, memory footprint, and throughput trade-offs of Speculative Decoding versus Medusa for serving open-weight LLMs in production?",
  },
  {
    label: "🔐 Post-Quantum TLS 1.3",
    query:
      "What are the network latency, packet fragmentation, and handshake overheads of deploying NIST's finalized post-quantum standards (ML-KEM and ML-DSA) in TLS 1.3?",
  },
  {
    label: "🧬 AlphaFold 3 vs ESMFold",
    query:
      "How do AlphaFold 3 and ESMFold compare in prediction accuracy for protein-ligand interactions and compute cost in drug discovery?",
  },
  {
    label: "🧠 Mixture of Agents (MoA)",
    query:
      "How does Mixture of Agents (MoA) architecture improve reasoning benchmarks compared to single frontier LLMs, and what are its token cost and latency trade-offs?",
  },
] as const;

const TERMINAL_STATUSES = ["completed", "cancelled", "failed"] as const;

function stageProgress(
  status: string,
  statusBeforeCancel: string | null,
): { completedThrough: number; activeIndex: number } {
  if (status === "cancelled") {
    const fallbackStatus =
      statusBeforeCancel && statusBeforeCancel !== "cancelled"
        ? statusBeforeCancel
        : "planning";
    const fallbackProgress = stageProgress(fallbackStatus, null);

    return {
      completedThrough: fallbackProgress.completedThrough,
      activeIndex: -1,
    };
  }

  if (status === "planning") {
    return {
      completedThrough: -1,
      activeIndex: 0,
    };
  }

  if (status === "researching") {
    return {
      completedThrough: 0,
      activeIndex: 1,
    };
  }

  if (
    status === "verifying" ||
    status === "reasoning" ||
    status === "fact_checking"
  ) {
    return {
      completedThrough: 1,
      activeIndex: 2,
    };
  }

  if (status === "awaiting_approval") {
    return {
      completedThrough: 2,
      activeIndex: 3,
    };
  }

  if (status === "generating_report") {
    return {
      completedThrough: 3,
      activeIndex: 4,
    };
  }

  if (status === "completed") {
    return {
      completedThrough: 4,
      activeIndex: -1,
    };
  }

  return {
    completedThrough: -1,
    activeIndex: 0,
  };
}

export default function DashboardPage() {
  const router = useRouter();

  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [workspaceDescription, setWorkspaceDescription] = useState("");
  const [question, setQuestion] = useState("");
  const [researchRun, setResearchRun] = useState<ResearchRun | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCreatingWorkspace, setIsCreatingWorkspace] = useState(false);
  const [isStartingResearch, setIsStartingResearch] = useState(false);
  const [isCancellingResearch, setIsCancellingResearch] = useState(false);
  const [lastNonCancelledStatus, setLastNonCancelledStatus] = useState<
    string | null
  >(null);
  const [elapsedSeconds, setElapsedSeconds] = useState<number | null>(null);

  useEffect(() => {
    if (!researchRun) return;
    const isActive =
      ACTIVE_EXECUTION_STATUSES.includes(
        researchRun.status as (typeof ACTIVE_EXECUTION_STATUSES)[number],
      ) && researchRun.status !== "awaiting_approval";

    if (!isActive) return;

    const startTimestamp = researchRun.started_at
      ? new Date(researchRun.started_at).getTime()
      : new Date(researchRun.created_at).getTime();

    const timerId = window.setInterval(() => {
      const now = Date.now();
      setElapsedSeconds(Math.max(0, Math.floor((now - startTimestamp) / 1000)));
    }, 1000);

    return () => window.clearInterval(timerId);
  }, [researchRun]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    async function loadWorkspaces() {
      try {
        const response = await apiFetch<Workspace[]>("/workspaces");
        setWorkspaces(response);

        if (response.length > 0) {
          setSelectedWorkspaceId(response[0].id);
        }
      } catch (requestError) {
        if (
          requestError instanceof ApiError &&
          requestError.status === 401
        ) {
          clearToken();
          router.replace("/login");
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "Unable to load workspaces",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadWorkspaces();
  }, [router]);

  useEffect(() => {
    if (!selectedWorkspaceId) return;

    let isSubscribed = true;

    async function loadWorkspaceActiveRun() {
      try {
        const runs = await apiFetch<ResearchRun[]>(
          `/workspaces/${selectedWorkspaceId}/research`,
        );
        if (!isSubscribed) return;

        // Auto-detect active run (running or awaiting approval)
        const activeRun = runs.find((r) =>
          ACTIVE_EXECUTION_STATUSES.includes(
            r.status as (typeof ACTIVE_EXECUTION_STATUSES)[number],
          ),
        );

        if (activeRun) {
          setResearchRun(activeRun);
          if (activeRun.status !== "cancelled") {
            setLastNonCancelledStatus(activeRun.status);
          }
        }
      } catch {
        // Silent recovery
      }
    }

    void loadWorkspaceActiveRun();

    return () => {
      isSubscribed = false;
    };
  }, [selectedWorkspaceId]);

  async function handleCreateWorkspace(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError("");
    setIsCreatingWorkspace(true);

    try {
      const workspace = await apiFetch<Workspace>("/workspaces", {
        method: "POST",
        body: {
          name: workspaceName,
          description: workspaceDescription || null,
        },
      });

      setWorkspaces((current) => [...current, workspace]);
      setSelectedWorkspaceId(workspace.id);
      setWorkspaceName("");
      setWorkspaceDescription("");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to create workspace",
      );
    } finally {
      setIsCreatingWorkspace(false);
    }
  }

  async function handleStartResearch(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();
    setError("");

    if (!selectedWorkspaceId) {
      setError("Create or select a workspace first.");
      return;
    }

    if (
      isStartingResearch ||
      researchRun?.status === "researching" ||
      researchRun?.status === "awaiting_approval"
    ) {
      setError(
        "A research run is already active. Wait for completion or approve it first.",
      );
      return;
    }

    setIsStartingResearch(true);
    setResearchRun(null);

    try {
      const run = await apiFetch<ResearchRun>("/research/start", {
        method: "POST",
        body: {
          workspace_id: selectedWorkspaceId,
          question,
        },
      });

      setResearchRun(run);
      if (run.status !== "cancelled") {
        setLastNonCancelledStatus(run.status);
      }
      router.push(`/research/${run.id}`);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to start research",
      );
    } finally {
      setIsStartingResearch(false);
    }
  }

  async function handleCancelResearch() {
    if (!researchRun) {
      return;
    }

    setError("");
    setIsCancellingResearch(true);

    const statusBeforeCancel = researchRun.status;

    try {
      const cancelledRun = await apiFetch<ResearchRun>(
        `/research/${researchRun.id}/cancel`,
        { method: "POST" },
      );

      setResearchRun(cancelledRun);

      if (cancelledRun.status === "cancelled") {
        setLastNonCancelledStatus(statusBeforeCancel);
      } else {
        setLastNonCancelledStatus(cancelledRun.status);
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to stop research",
      );
    } finally {
      setIsCancellingResearch(false);
    }
  }

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  const currentStageProgress = researchRun
    ? stageProgress(researchRun.status, lastNonCancelledStatus)
    : { completedThrough: -1, activeIndex: -1 };
  const isStartBlockedByRun =
    researchRun !== null &&
    ACTIVE_EXECUTION_STATUSES.includes(
      researchRun.status as (typeof ACTIVE_EXECUTION_STATUSES)[number],
    );
  const isStartDisabled =
    isStartingResearch ||
    isStartBlockedByRun ||
    !selectedWorkspaceId;
  const canStopResearch =
    researchRun !== null &&
    CANCELLABLE_STATUSES.includes(
      researchRun.status as (typeof CANCELLABLE_STATUSES)[number],
    );

  useEffect(() => {
    const currentResearchRunId = researchRun?.id;

    if (!currentResearchRunId) {
      return;
    }

    let isCancelled = false;
    let intervalId: number;

    async function pollResearchStatus() {
      if (isCancelled) {
        return;
      }

      try {
        const updatedRun = await apiFetch<ResearchRun>(`/research/${currentResearchRunId}`);

        if (!isCancelled) {
          setResearchRun(updatedRun);

          if (updatedRun.status !== "cancelled") {
            setLastNonCancelledStatus(updatedRun.status);
          }
        }

        if (
          !isCancelled &&
          TERMINAL_STATUSES.includes(
            updatedRun.status as (typeof TERMINAL_STATUSES)[number],
          )
        ) {
          window.clearInterval(intervalId);
        }
      } catch (requestError) {
        if (
          requestError instanceof ApiError &&
          requestError.status === 401
        ) {
          clearToken();
          router.replace("/login");
          return;
        }
      }
    }

    void pollResearchStatus();
    intervalId = window.setInterval(() => {
      void pollResearchStatus();
    }, 3000);

    return () => {
      isCancelled = true;
      window.clearInterval(intervalId);
    };
  }, [researchRun?.id, router]);

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link href="/" className="text-xl font-semibold">
            Deepcite
          </Link>

          <div className="flex items-center gap-3">
            <ThemeToggle />

            <Link
              href="/analytics"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <BarChart3 className="h-4 w-4" />
              Quality dashboards
            </Link>
            <Link
              href="/history"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <FileText className="h-4 w-4" />
              History
            </Link>

            <Link
              href="/settings"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <FolderKanban className="h-4 w-4" />
              Settings
            </Link>

            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              Log out
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
        <div>
          <p className="text-sm font-medium text-primary">Overview</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            Your research workspace
          </h1>
          <p className="mt-2 text-muted-foreground">
            Create a workspace and submit an evidence-backed research question.
          </p>
        </div>

        {error && (
          <p className="mt-6 rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        <div className="mt-8 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <section className="rounded-2xl border border-border bg-card p-6">
            <div className="flex items-center gap-3">
              <FolderKanban className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">Workspaces</h2>
            </div>

            {isLoading ? (
              <p className="mt-6 text-sm text-muted-foreground">
                Loading workspaces...
              </p>
            ) : (
              <>
                <select
                  value={selectedWorkspaceId}
                  onChange={(event) =>
                    setSelectedWorkspaceId(event.target.value)
                  }
                  className="mt-6 h-11 w-full rounded-lg border border-border bg-background px-3 text-sm"
                >
                  <option value="">Select a workspace</option>
                  {workspaces.map((workspace) => (
                    <option key={workspace.id} value={workspace.id}>
                      {workspace.name}
                    </option>
                  ))}
                </select>

                <form
                  onSubmit={handleCreateWorkspace}
                  className="mt-8 space-y-4 border-t border-border pt-6"
                >
                  <h3 className="font-medium">Create workspace</h3>

                  <input
                    value={workspaceName}
                    onChange={(event) => setWorkspaceName(event.target.value)}
                    required
                    placeholder="Workspace name"
                    className="h-11 w-full rounded-lg border border-border bg-background px-3 text-sm"
                  />

                  <input
                    value={workspaceDescription}
                    onChange={(event) =>
                      setWorkspaceDescription(event.target.value)
                    }
                    placeholder="Description (optional)"
                    className="h-11 w-full rounded-lg border border-border bg-background px-3 text-sm"
                  />

                  <Button
                    type="submit"
                    variant="outline"
                    disabled={isCreatingWorkspace}
                  >
                    <Plus className="h-4 w-4" />
                    {isCreatingWorkspace
                      ? "Creating..."
                      : "Create workspace"}
                  </Button>
                </form>
              </>
            )}
          </section>

          <section className="rounded-2xl border border-border bg-card p-6">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">
                Start research
              </h2>
            </div>

            <form onSubmit={handleStartResearch} className="mt-6 space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    Quick research topics
                  </span>
                  <span className="text-xs text-muted-foreground">Click to auto-fill</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {SAMPLE_RESEARCH_PROMPTS.map((sample) => (
                    <button
                      key={sample.label}
                      type="button"
                      onClick={() => setQuestion(sample.query)}
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-all ${
                        question === sample.query
                          ? "bg-primary text-primary-foreground shadow-sm"
                          : "bg-muted text-muted-foreground hover:bg-primary/10 hover:text-primary border border-border/60"
                      }`}
                    >
                      {sample.label}
                    </button>
                  ))}
                </div>
              </div>

              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                required
                minLength={10}
                rows={6}
                placeholder="What would you like to research?"
                className="w-full resize-none rounded-lg border border-border bg-background px-3 py-3 text-sm"
              />

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  type="submit"
                  disabled={isStartDisabled}
                >
                  <Activity className="h-4 w-4" />
                  {isStartingResearch
                    ? "Starting..."
                    : isStartBlockedByRun
                      ? "Research already running"
                    : "Start research"}
                </Button>

                {canStopResearch && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancelResearch}
                    disabled={isCancellingResearch}
                  >
                    <Square className="h-4 w-4" />
                    {isCancellingResearch ? "Stopping..." : "Stop research"}
                  </Button>
                )}
              </div>
            </form>

            {isStartingResearch && (
              <div className="mt-8 rounded-xl border border-border bg-muted p-5">
                <p className="font-medium">Research is running</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  The backend is executing the research graph. This may take
                  several minutes.
                </p>
              </div>
            )}

            {researchRun && (
              <div className="mt-8 rounded-xl border border-border bg-muted p-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium">Research status</p>
                    <div className="mt-1 flex flex-wrap items-center gap-2">
                      <span className="text-sm text-muted-foreground capitalize">
                        {researchRun.status.replace(/_/g, " ")}
                      </span>
                      {elapsedSeconds !== null && (
                        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                          <Clock
                            className="h-3 w-3 animate-spin"
                            style={{ animationDuration: "4s" }}
                          />
                          Elapsed: {formatElapsed(elapsedSeconds)}
                        </span>
                      )}
                      {researchRun.status === "completed" &&
                        formatDuration(
                          researchRun.started_at || researchRun.created_at,
                          researchRun.completed_at,
                        ) && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
                            <Clock className="h-3 w-3" />
                            {formatDuration(
                              researchRun.started_at || researchRun.created_at,
                              researchRun.completed_at,
                            )}
                          </span>
                        )}
                    </div>
                    {researchRun.status === "awaiting_approval" && (
                      <p className="mt-1 text-sm font-medium text-primary">
                        Waiting for your approval
                      </p>
                    )}
                    {researchRun.status === "cancelled" && (
                      <p className="mt-1 text-sm font-medium text-amber-600">
                        Research stopped by user
                      </p>
                    )}
                  </div>

                  <span className="rounded-full bg-primary/15 px-3 py-1 text-xs font-medium text-primary">
                    {researchRun.id.slice(0, 8)}
                  </span>
                </div>

                <div className="mt-4">
                  <Link
                    href={`/research/${researchRun.id}`}
                    className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm"
                  >
                    <Activity className="h-4 w-4" />
                    {researchRun.status === "completed"
                      ? "View Final Report →"
                      : researchRun.status === "awaiting_approval"
                        ? "Review Evidence & Approve →"
                        : "Open Live Research Room →"}
                  </Link>
                </div>

                <div className="mt-5 space-y-3">
                  {progressSteps.map((step, index) => {
                    const isCompleted =
                      index <= currentStageProgress.completedThrough;
                    const isActive =
                      index === currentStageProgress.activeIndex;

                    return (
                      <div
                        key={step}
                        className="flex items-center gap-3 text-sm"
                      >
                        <span
                          className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                            isCompleted || isActive
                              ? "bg-primary text-primary-foreground"
                              : "bg-background text-muted-foreground"
                          }`}
                        >
                          {index + 1}
                        </span>

                        <span
                          className={
                            isCompleted || isActive
                              ? "font-medium"
                              : "text-muted-foreground"
                          }
                        >
                          {step}
                        </span>

                        {isCompleted && (
                          <CheckCircle2 className="ml-auto h-4 w-4 text-emerald-500" />
                        )}

                        {isActive && (
                          <span className="ml-auto flex items-center gap-1.5 text-xs font-medium text-primary">
                            <span className="relative flex h-2 w-2">
                              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                            </span>
                            In progress
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}