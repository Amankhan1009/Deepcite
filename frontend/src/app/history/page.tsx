"use client";

import Link from "next/link";
import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Clock3,
  FileText,
  Settings,
} from "lucide-react";
import type { MouseEvent } from "react";
import { useEffect, useState } from "react";
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

type HistoryItem = ResearchRun & {
  workspace_name: string;
};

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

function statusLabel(status: string) {
  return status.replaceAll("_", " ");
}

export default function HistoryPage() {
  const router = useRouter();

  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [resumingRunId, setResumingRunId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    async function loadHistory() {
      try {
        const workspaces = await apiFetch<Workspace[]>("/workspaces");

        const workspaceHistory = await Promise.all(
          workspaces.map(async (workspace) => {
            const runs = await apiFetch<ResearchRun[]>(
              `/workspaces/${workspace.id}/research`,
            );

            return runs.map((run) => ({
              ...run,
              workspace_name: workspace.name,
            }));
          }),
        );

        const combinedHistory = workspaceHistory
          .flat()
          .sort(
            (first, second) =>
              new Date(second.created_at).getTime() -
              new Date(first.created_at).getTime(),
          );

        setHistory(combinedHistory);
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
            : "Unable to load research history",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadHistory();
  }, [router]);

  async function handleResume(
    event: MouseEvent<HTMLButtonElement>,
    researchRunId: string,
  ) {
    event.preventDefault();
    event.stopPropagation();

    setError("");
    setResumingRunId(researchRunId);

    try {
      const updatedRun = await apiFetch<ResearchRun>(
        `/research/${researchRunId}/resume`,
        {
          method: "POST",
        },
      );

      setHistory((current) =>
        current.map((run) =>
          run.id === researchRunId
            ? {
                ...run,
                status: updatedRun.status,
              }
            : run,
        ),
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to resume research",
      );
    } finally {
      setResumingRunId("");
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-8">
          <Link href="/" className="text-xl font-semibold">
            Deepcite
          </Link>

          <div className="flex items-center gap-4">
            <ThemeToggle />

            <Link
              href="/analytics"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <BarChart3 className="h-4 w-4" />
              Analytics
            </Link>

            <Link
              href="/settings"
              className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
            >
              <Settings className="h-4 w-4" />
              Settings
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>

        <div className="mt-8">
          <p className="text-sm font-medium text-primary">
            Workspace history
          </p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            Research history
          </h1>

          <p className="mt-2 text-muted-foreground">
            Review previous research runs across all your workspaces.
          </p>
        </div>

        {error && (
          <p className="mt-6 rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {isLoading && (
          <div className="mt-8 rounded-xl border border-border bg-card p-8 text-muted-foreground">
            Loading research history...
          </div>
        )}

        {!isLoading && !error && history.length === 0 && (
          <div className="mt-8 rounded-xl border border-dashed border-border bg-card p-10 text-center">
            <FileText className="mx-auto h-10 w-10 text-muted-foreground" />

            <h2 className="mt-4 text-lg font-semibold">
              No research runs yet
            </h2>

            <p className="mt-2 text-muted-foreground">
              Start your first research run from the dashboard.
            </p>

            <Link
              href="/dashboard"
              className="mt-6 inline-flex rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            >
              Start research
            </Link>
          </div>
        )}

        <div className="mt-8 space-y-4">
          {history.map((run) => (
            <div
              key={run.id}
              className="rounded-xl border border-border bg-card p-6"
            >
              <div className="flex flex-col justify-between gap-5 md:flex-row md:items-start">
                <Link
                  href={`/research/${run.id}`}
                  className="min-w-0 flex-1 transition-colors hover:text-primary"
                >
                  <p className="text-lg font-semibold">
                    {run.question}
                  </p>

                  <p className="mt-2 text-sm text-muted-foreground">
                    Workspace: {run.workspace_name}
                  </p>

                  <div className="mt-5 flex items-center gap-2 text-sm text-muted-foreground">
                    <Clock3 className="h-4 w-4" />
                    {formatDate(run.created_at)}
                  </div>
                </Link>

                <div className="flex shrink-0 flex-col items-start gap-3 md:items-end">
                  <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium capitalize text-primary">
                    {statusLabel(run.status)}
                  </span>

                  {(run.status === "paused" ||
                    run.status === "failed") && (
                    <Button
                      type="button"
                      size="sm"
                      onClick={(event) =>
                        handleResume(event, run.id)
                      }
                      disabled={resumingRunId === run.id}
                    >
                      <CheckCircle2 className="h-4 w-4" />

                      {resumingRunId === run.id
                        ? "Resuming..."
                        : "Resume research"}
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}