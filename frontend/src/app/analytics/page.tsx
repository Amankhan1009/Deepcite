"use client";

import Link from "next/link";
import {
  Activity,
  ArrowLeft,
  BarChart3,
  Database,
  DollarSign,
  Gauge,
  RefreshCw,
  Search,
  Server,
  TriangleAlert,
} from "lucide-react";
import type { FormEvent, ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ApiError, apiFetch } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

type EvaluationSummaryItem = {
  dimension: string;
  average_score: string | number;
  run_count: number;
};

type EvaluationSummary = {
  dimensions: EvaluationSummaryItem[];
};

type ObservabilitySummary = {
  research_run_count: number;
  trace_count: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  total_cost: string | number;
  total_latency_ms: number;
  total_retries: number;
  total_errors: number;
};

type Workspace = {
  id: string;
  name: string;
};

type ResearchRun = {
  id: string;
  workspace_id: string;
  question: string;
  status: string;
  created_at: string;
};

type Evaluation = {
  id: string;
  research_run_id: string;
  dimension: string;
  score: string | number;
  details: Record<string, unknown>;
  created_at: string;
};

type TraceRun = {
  id: string;
  agent_name: string;
  langsmith_run_id: string;
  tool_calls: Record<string, unknown>[];
  token_usage: Record<string, unknown>;
  latency_ms: number | null;
  status: string;
  error: string | null;
  created_at: string;
};

type ResearchTrace = {
  research_run_id: string;
  trace_count: number;
  total_tokens: number;
  total_cost: string | number;
  total_latency_ms: number;
  total_retries: number;
  total_errors: number;
  runs: TraceRun[];
};

function formatScore(value: string | number) {
  return Number(value).toFixed(4);
}

function formatNumber(value: number) {
  return value.toLocaleString();
}

function formatCost(value: string | number) {
  return `$${Number(value).toFixed(6)}`;
}

function formatLatency(milliseconds: number) {
  if (milliseconds < 1000) {
    return `${milliseconds.toLocaleString()} ms`;
  }

  return `${(milliseconds / 1000).toFixed(2)} s`;
}

function prettyDimension(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export default function AnalyticsPage() {
  const router = useRouter();

  const [evaluationSummary, setEvaluationSummary] =
    useState<EvaluationSummary | null>(null);

  const [observabilitySummary, setObservabilitySummary] =
    useState<ObservabilitySummary | null>(null);

  const [researchHistory, setResearchHistory] = useState<ResearchRun[]>([]);
  const [researchId, setResearchId] = useState("");

  const [runEvaluations, setRunEvaluations] = useState<Evaluation[] | null>(
    null,
  );

  const [runTrace, setRunTrace] = useState<ResearchTrace | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingRun, setIsLoadingRun] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    async function loadDashboardData() {
      try {
        const [
          evaluationData,
          observabilityData,
          workspaces,
        ] = await Promise.all([
          apiFetch<EvaluationSummary>("/evaluation/summary"),
          apiFetch<ObservabilitySummary>("/observability/summary"),
          apiFetch<Workspace[]>("/workspaces"),
        ]);

        const historyResponses = await Promise.all(
          workspaces.map((workspace) =>
            apiFetch<ResearchRun[]>(
              `/workspaces/${workspace.id}/research`,
            ),
          ),
        );

        const history = historyResponses
          .flat()
          .sort(
            (first, second) =>
              new Date(second.created_at).getTime() -
              new Date(first.created_at).getTime(),
          );

        setEvaluationSummary(evaluationData);
        setObservabilitySummary(observabilityData);
        setResearchHistory(history);

        if (history.length > 0) {
          setResearchId(history[0].id);
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
            : "Unable to load dashboard data",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboardData();
  }, [router]);

  async function handleLoadResearchRun(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setRunEvaluations(null);
    setRunTrace(null);

    if (!researchId) {
      setError("Select a research run first.");
      return;
    }

    setIsLoadingRun(true);

    try {
      const [evaluationData, traceData] = await Promise.all([
        apiFetch<Evaluation[]>(
          `/research/${researchId}/evaluation`,
        ),
        apiFetch<ResearchTrace>(
          `/research/${researchId}/trace`,
        ),
      ]);

      setRunEvaluations(evaluationData);
      setRunTrace(traceData);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to load research run metrics",
      );
    } finally {
      setIsLoadingRun(false);
    }
  }

  function handleRefresh() {
    window.location.reload();
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
              href="/history"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              History
            </Link>

            <Link
              href="/settings"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Settings
            </Link>

            <Link
              href="/dashboard"
              className="text-sm text-muted-foreground hover:text-foreground"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>

        <div className="mt-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <p className="text-sm font-medium text-primary">
              Quality and operations
            </p>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Evaluation and observability
            </h1>

            <p className="mt-2 max-w-2xl text-muted-foreground">
              Inspect research quality scores and operational agent behavior.
            </p>
          </div>

          <Button
            type="button"
            variant="outline"
            onClick={handleRefresh}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {error && (
          <p className="mt-6 rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {isLoading ? (
          <p className="mt-8 text-sm text-muted-foreground">
            Loading quality and observability data...
          </p>
        ) : (
          <>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard
                icon={<Database className="h-5 w-5" />}
                label="Research runs"
                value={
                  observabilitySummary
                    ? formatNumber(
                        observabilitySummary.research_run_count,
                      )
                    : "—"
                }
              />

              <MetricCard
                icon={<Activity className="h-5 w-5" />}
                label="Agent traces"
                value={
                  observabilitySummary
                    ? formatNumber(observabilitySummary.trace_count)
                    : "—"
                }
              />

              <MetricCard
                icon={<Gauge className="h-5 w-5" />}
                label="Total tokens"
                value={
                  observabilitySummary
                    ? formatNumber(observabilitySummary.total_tokens)
                    : "—"
                }
              />

              <MetricCard
                icon={<DollarSign className="h-5 w-5" />}
                label="Estimated cost"
                value={
                  observabilitySummary
                    ? formatCost(observabilitySummary.total_cost)
                    : "—"
                }
              />
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
              <section className="rounded-2xl border border-border bg-card p-6">
                <div className="flex items-center gap-3">
                  <BarChart3 className="h-5 w-5 text-primary" />

                  <div>
                    <h2 className="text-lg font-semibold">
                      Evaluation summary
                    </h2>

                    <p className="mt-1 text-sm text-muted-foreground">
                      Average scores across completed research runs.
                    </p>
                  </div>
                </div>

                {evaluationSummary &&
                evaluationSummary.dimensions.length > 0 ? (
                  <div className="mt-6 overflow-x-auto">
                    <table className="w-full min-w-[520px] text-left text-sm">
                      <thead className="border-b border-border text-muted-foreground">
                        <tr>
                          <th className="px-3 py-3 font-medium">
                            Dimension
                          </th>
                          <th className="px-3 py-3 font-medium">
                            Average score
                          </th>
                          <th className="px-3 py-3 font-medium">
                            Runs
                          </th>
                        </tr>
                      </thead>

                      <tbody>
                        {evaluationSummary.dimensions.map((item) => (
                          <tr
                            key={item.dimension}
                            className="border-b border-border last:border-0"
                          >
                            <td className="px-3 py-4 font-medium">
                              {prettyDimension(item.dimension)}
                            </td>

                            <td className="px-3 py-4 text-primary">
                              {formatScore(item.average_score)}
                            </td>

                            <td className="px-3 py-4 text-muted-foreground">
                              {item.run_count}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <EmptyState text="No evaluation data is available yet." />
                )}
              </section>

              <section className="rounded-2xl border border-border bg-card p-6">
                <div className="flex items-center gap-3">
                  <Server className="h-5 w-5 text-primary" />

                  <div>
                    <h2 className="text-lg font-semibold">
                      Runtime summary
                    </h2>

                    <p className="mt-1 text-sm text-muted-foreground">
                      Aggregate agent execution metrics.
                    </p>
                  </div>
                </div>

                {observabilitySummary ? (
                  <div className="mt-6 space-y-4">
                    <RuntimeMetric
                      label="Prompt tokens"
                      value={formatNumber(
                        observabilitySummary.prompt_tokens,
                      )}
                    />

                    <RuntimeMetric
                      label="Completion tokens"
                      value={formatNumber(
                        observabilitySummary.completion_tokens,
                      )}
                    />

                    <RuntimeMetric
                      label="Total latency"
                      value={formatLatency(
                        observabilitySummary.total_latency_ms,
                      )}
                    />

                    <RuntimeMetric
                      label="Retries"
                      value={formatNumber(
                        observabilitySummary.total_retries,
                      )}
                    />

                    <RuntimeMetric
                      label="Errors"
                      value={formatNumber(
                        observabilitySummary.total_errors,
                      )}
                      hasError={observabilitySummary.total_errors > 0}
                    />
                  </div>
                ) : (
                  <EmptyState text="No observability data is available yet." />
                )}
              </section>
            </div>

            <section className="mt-6 rounded-2xl border border-border bg-card p-6">
              <div className="flex items-center gap-3">
                <Search className="h-5 w-5 text-primary" />

                <div>
                  <h2 className="text-lg font-semibold">
                    Inspect a research run
                  </h2>

                  <p className="mt-1 text-sm text-muted-foreground">
                    Select a previous run to inspect its evaluations and traces.
                  </p>
                </div>
              </div>

              <form
  onSubmit={handleLoadResearchRun}
  className="mt-6 grid min-w-0 gap-3 md:grid-cols-[minmax(0,1fr)_auto]"
>
  <div className="min-w-0 overflow-hidden">
    <select
      value={researchId}
      onChange={(event) => setResearchId(event.target.value)}
      disabled={researchHistory.length === 0}
      className="block h-11 w-full min-w-0 max-w-full truncate rounded-lg border border-border bg-background px-3 text-sm"
    >
      {researchHistory.length === 0 ? (
        <option value="">No research runs available</option>
      ) : (
        researchHistory.map((run) => (
          <option key={run.id} value={run.id}>
            {run.question} — {run.status}
          </option>
        ))
      )}
    </select>
  </div>

  <Button
    type="submit"
    disabled={isLoadingRun || researchHistory.length === 0}
    className="shrink-0"
  >
    <Search className="h-4 w-4" />
    {isLoadingRun ? "Loading..." : "Inspect run"}
  </Button>
</form>

              {runEvaluations && runTrace && (
                <div className="mt-8 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
                  <section>
                    <h3 className="font-semibold">Run evaluations</h3>

                    <div className="mt-4 space-y-3">
                      {runEvaluations.length === 0 ? (
                        <EmptyState text="No evaluations found for this run." />
                      ) : (
                        runEvaluations.map((evaluation) => (
                          <div
                            key={evaluation.id}
                            className="rounded-xl border border-border bg-muted p-4"
                          >
                            <div className="flex items-center justify-between gap-3">
                              <p className="font-medium">
                                {prettyDimension(evaluation.dimension)}
                              </p>

                              <p className="font-semibold text-primary">
                                {formatScore(evaluation.score)}
                              </p>
                            </div>

                            <p className="mt-2 text-xs text-muted-foreground">
                              Created{" "}
                              {new Date(
                                evaluation.created_at,
                              ).toLocaleString()}
                            </p>
                          </div>
                        ))
                      )}
                    </div>
                  </section>

                  <section>
                    <h3 className="font-semibold">Run trace summary</h3>

                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <SmallMetric
                        label="Trace count"
                        value={formatNumber(runTrace.trace_count)}
                      />

                      <SmallMetric
                        label="Total tokens"
                        value={formatNumber(runTrace.total_tokens)}
                      />

                      <SmallMetric
                        label="Latency"
                        value={formatLatency(runTrace.total_latency_ms)}
                      />

                      <SmallMetric
                        label="Cost"
                        value={formatCost(runTrace.total_cost)}
                      />

                      <SmallMetric
                        label="Retries"
                        value={formatNumber(runTrace.total_retries)}
                      />

                      <SmallMetric
                        label="Errors"
                        value={formatNumber(runTrace.total_errors)}
                        hasError={runTrace.total_errors > 0}
                      />
                    </div>

                    <div className="mt-5 overflow-x-auto">
                      <table className="w-full min-w-[620px] text-left text-sm">
                        <thead className="border-b border-border text-muted-foreground">
                          <tr>
                            <th className="px-3 py-3 font-medium">
                              Agent
                            </th>
                            <th className="px-3 py-3 font-medium">
                              Status
                            </th>
                            <th className="px-3 py-3 font-medium">
                              Latency
                            </th>
                            <th className="px-3 py-3 font-medium">
                              Error
                            </th>
                          </tr>
                        </thead>

                        <tbody>
                          {runTrace.runs.map((trace) => (
                            <tr
                              key={trace.id}
                              className="border-b border-border last:border-0"
                            >
                              <td className="px-3 py-4 font-medium">
                                {trace.agent_name}
                              </td>

                              <td className="px-3 py-4">
                                {trace.status}
                              </td>

                              <td className="px-3 py-4 text-muted-foreground">
                                {trace.latency_ms === null
                                  ? "—"
                                  : formatLatency(trace.latency_ms)}
                              </td>

                              <td className="px-3 py-4">
                                {trace.error ? (
                                  <span className="inline-flex items-center gap-1 text-red-600">
                                    <TriangleAlert className="h-4 w-4" />
                                    {trace.error}
                                  </span>
                                ) : (
                                  <span className="text-emerald-600">
                                    None
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </div>
              )}
            </section>
          </>
        )}
      </section>
    </main>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5">
      <div className="flex items-center gap-3 text-primary">
        {icon}
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>

      <p className="mt-4 text-2xl font-semibold">{value}</p>
    </section>
  );
}

function RuntimeMetric({
  label,
  value,
  hasError = false,
}: {
  label: string;
  value: string;
  hasError?: boolean;
}) {
  return (
    <div className="flex items-center justify-between border-b border-border pb-3 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>

      <span
        className={
          hasError ? "font-semibold text-red-600" : "font-semibold"
        }
      >
        {value}
      </span>
    </div>
  );
}

function SmallMetric({
  label,
  value,
  hasError = false,
}: {
  label: string;
  value: string;
  hasError?: boolean;
}) {
  return (
    <div className="rounded-xl border border-border bg-muted p-4">
      <p className="text-xs text-muted-foreground">{label}</p>

      <p
        className={`mt-2 text-lg font-semibold ${
          hasError ? "text-red-600" : ""
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="mt-5 rounded-xl border border-dashed border-border p-5 text-sm text-muted-foreground">
      {text}
    </div>
  );
}