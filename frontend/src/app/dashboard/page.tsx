"use client";

import Link from "next/link";
import {
  Activity,
  BarChart3,
  CheckCircle2,
  FileText,
  FolderKanban,
  LogOut,
  Plus,
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
};

const progressSteps = [
  "Planning",
  "Researching sources",
  "Verifying evidence",
  "Generating report",
];

function progressIndex(status: string) {
  if (status === "planning") return 0;
  if (
    status === "researching" ||
    status === "verifying" ||
    status === "reasoning" ||
    status === "fact_checking"
  ) {
    return 1;
  }
  if (status === "generating_report") return 3;
  if (status === "completed") return 3;
  return 0;
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
      setQuestion("");
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

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  const currentProgress = researchRun
    ? progressIndex(researchRun.status)
    : -1;

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
              <textarea
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                required
                minLength={10}
                rows={6}
                placeholder="What would you like to research?"
                className="w-full resize-none rounded-lg border border-border bg-background px-3 py-3 text-sm"
              />

              <Button
                type="submit"
                disabled={isStartingResearch || !selectedWorkspaceId}
              >
                <Activity className="h-4 w-4" />
                {isStartingResearch
                  ? "Research in progress..."
                  : "Start research"}
              </Button>
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
                    <p className="mt-1 text-sm text-muted-foreground">
                      {researchRun.status}
                    </p>
                  </div>

                  <span className="rounded-full bg-primary/15 px-3 py-1 text-xs font-medium text-primary">
                    {researchRun.id.slice(0, 8)}
                  </span>
                </div>
                <Link
                  href={`/research/${researchRun.id}`}
                  className="mt-6 inline-flex items-center text-sm font-medium text-primary"
                >
                  Review research and report →
                </Link>
                <div className="mt-5 space-y-3">
                  {progressSteps.map((step, index) => (
                    <div
                      key={step}
                      className="flex items-center gap-3 text-sm"
                    >
                      <span
                        className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                          index <= currentProgress
                            ? "bg-primary text-primary-foreground"
                            : "bg-background text-muted-foreground"
                        }`}
                      >
                        {index + 1}
                      </span>

                      <span
                        className={
                          index <= currentProgress
                            ? "font-medium"
                            : "text-muted-foreground"
                        }
                      >
                        {step}
                      </span>

                      {index <= currentProgress && (
                        <CheckCircle2 className="ml-auto h-4 w-4 text-emerald-500" />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}