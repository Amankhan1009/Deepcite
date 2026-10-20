"use client";

import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  Check,
  CheckCircle2,
  Clock,
  Compass,
  Copy,
  Download,
  ExternalLink,
  FileText,
  HelpCircle,
  MinusCircle,
  RefreshCw,
  Send,
  Share2,
  XCircle,
} from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ApiError, apiDownload, apiFetch } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

type ResearchRun = {
  id: string;
  workspace_id: string;
  question: string;
  status: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
};

type ResearchPlan = {
  id: string;
  research_run_id: string;
  strategy: string;
  sub_questions: string[];
  created_at: string;
};

type ResearchEvidenceItem = {
  id: string;
  source_id?: string | null;
  source_title?: string | null;
  source_url: string;
  source_reliability_score?: number | null;
  claim_text?: string | null;
  supporting_evidence?: string | null;
  verification_status: string;
  confidence_score?: number | null;
};


type Citation = {
  id: string;
  inline_marker: string;
  claim_id: string;
  claim_text: string;
  confidence_score: number;
  fact_check_status: string;
  source_id: string;
  source_url: string;
  source_title: string | null;
  source_reliability_score: number | null;
};

type Report = {
  id: string;
  research_run_id: string;
  content_markdown: string;
  executive_summary: string | null;
  overall_confidence_score: string | number | null;
  citations: Citation[];
  created_at: string;
  updated_at: string;
};

type Evaluation = {
  id: string;
  research_run_id: string;
  dimension: string;
  score: string | number;
  details: {
    word_count?: number;
    target_word_count?: number;
    citation_count?: number;
    missing_sections?: string[];
    present_sections?: string[];
    present_section_count?: number;
    required_section_count?: number;
    metric_name?: string;
    total_claims?: number;
    supported_count?: number;
    partially_supported_count?: number;
    unsupported_count?: number;
    contradicted_count?: number;
  };
  created_at: string;
};

const ACTIVE_EXECUTION_STATUSES = [
  "planning",
  "researching",
  "verifying",
  "reasoning",
  "fact_checking",
  "generating_report",
] as const;

const detailedProgressSteps = [
  {
    statusKey: "planning",
    label: "Supervisor & Planning Agent",
    description:
      "Decomposes the research question into targeted sub-questions and formulates strategy.",
  },
  {
    statusKey: "researching",
    label: "Research Agent (Tavily MCP)",
    description:
      "Searches the live web and extracts authoritative external sources across domains.",
  },
  {
    statusKey: "verifying",
    label: "Verification & Evidence Agent",
    description:
      "Evaluates source reliability scores and extracts verbatim empirical evidence.",
  },
  {
    statusKey: "reasoning",
    label: "Reasoning & Fact-Checking Agents",
    description:
      "Synthesizes multi-source conclusions and performs claim verification.",
  },
  {
    statusKey: "awaiting_approval",
    label: "Human-in-the-Loop Approval Gate",
    description:
      "Operator reviews verified claims and evidence before authorizing final report generation.",
  },
  {
    statusKey: "generating_report",
    label: "Report & Evaluation Agents",
    description:
      "Assembles deep 7-section report, maps citations, and scores groundedness & completeness.",
  },
];

function getActiveStepIndex(status: string): number {
  switch (status) {
    case "planning":
      return 0;
    case "researching":
      return 1;
    case "verifying":
      return 2;
    case "reasoning":
    case "fact_checking":
      return 3;
    case "awaiting_approval":
      return 4;
    case "generating_report":
      return 5;
    case "completed":
      return 6;
    default:
      return 1;
  }
}

function getStepMeta(status: string): { title: string; subtitle: string } {
  switch (status) {
    case "planning":
      return {
        title: "Planning Research Strategy",
        subtitle:
          "Analyzing question, setting constraints, and decomposing into sub-questions...",
      };
    case "researching":
      return {
        title: "Gathering Authoritative Sources",
        subtitle:
          "Running web & Tavily MCP search across academic and industry domains...",
      };
    case "verifying":
      return {
        title: "Verifying Sources & Evidence",
        subtitle:
          "Assessing domain authority, SSL certificates, and extracting verified evidence...",
      };
    case "reasoning":
      return {
        title: "Synthesizing Cross-Source Findings",
        subtitle:
          "Correlating multi-source findings and formulating synthesized conclusions...",
      };
    case "fact_checking":
      return {
        title: "Calibrated Claim Fact-Checking",
        subtitle:
          "Verifying each reasoning conclusion against extracted evidence snippets...",
      };
    case "awaiting_approval":
      return {
        title: "Human-in-the-Loop Approval Gate",
        subtitle:
          "Research complete. Waiting for your review and approval before generating report.",
      };
    case "generating_report":
      return {
        title: "Generating Comprehensive Research Report",
        subtitle:
          "Synthesizing executive summary, findings, analysis, and citations...",
      };
    case "completed":
      return {
        title: "Research Completed & Verified",
        subtitle:
          "Full report generated with inline citations and evaluation scores.",
      };
    default:
      return {
        title: "Executing Research",
        subtitle: "Deepcite agents are processing the research run...",
      };
  }
}

function formatElapsed(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

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

function formatScore(score: string | number | null | undefined) {
  if (score === null || score === undefined) {
    return "—";
  }

  const value = Number(score);

  return Number.isFinite(value) ? value.toFixed(4) : "—";
}

function filterReportCitationMarkers(
  markdown: string,
  citations: Citation[],
) {
  const allowedMarkers = new Set(
    citations
      .map((citation) =>
        citation.inline_marker.match(/\[Source\s+(\d+)\]/i)?.[1],
      )
      .filter((marker): marker is string => Boolean(marker)),
  );

  return markdown.replace(
    /\[Source\s+(\d+)\]/gi,
    (match, marker: string) => (
      allowedMarkers.has(marker) ? `[Source ${marker}]` : ""
    ),
  );
}

function getStatusBadge(status?: string | null) {
  const norm = (status || "").toLowerCase().trim();
  if (norm === "supported" || norm === "verified") {
    return {
      label: "Verified Support",
      icon: CheckCircle2,
      className:
        "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-500/20",
    };
  }
  if (norm === "partially_supported") {
    return {
      label: "Partially Supported",
      icon: AlertCircle,
      className:
        "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 border border-amber-500/20",
    };
  }
  if (norm === "uncertain") {
    return {
      label: "Uncertain",
      icon: HelpCircle,
      className:
        "bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-400/20",
    };
  }
  if (norm === "contradicted") {
    return {
      label: "Contradicted",
      icon: XCircle,
      className:
        "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-500/20",
    };
  }
  if (norm === "unsupported") {
    return {
      label: "Unsupported",
      icon: XCircle,
      className:
        "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300 border border-rose-500/20",
    };
  }
  if (norm === "irrelevant") {
    return {
      label: "Irrelevant",
      icon: MinusCircle,
      className:
        "bg-slate-100 text-slate-700 dark:bg-slate-900 dark:text-slate-400 border border-slate-500/20",
    };
  }
  return {
    label:
      norm
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase()) || "Unverified",
    icon: HelpCircle,
    className: "bg-muted text-muted-foreground border border-border",
  };
}

function ResearchPlanCard({ plan }: { plan: ResearchPlan | null }) {
  if (!plan) return null;

  return (
    <div className="rounded-2xl border border-primary/20 bg-gradient-to-br from-primary/5 via-card to-transparent p-6 dark:bg-primary/10 transition-all shadow-sm">
      <div className="flex items-center gap-2.5 text-primary">
        <Compass className="h-5 w-5 shrink-0" />
        <h3 className="font-semibold text-base text-foreground">
          Research Plan & Strategy
        </h3>
        <span className="ml-auto rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary border border-primary/20">
          Decomposition Strategy
        </span>
      </div>

      <div className="mt-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Supervisor Approach
        </p>
        <p className="mt-1 text-sm leading-relaxed text-foreground font-medium bg-background/80 p-3.5 rounded-xl border border-border/60">
          {plan.strategy}
        </p>
      </div>

      {plan.sub_questions && plan.sub_questions.length > 0 && (
        <div className="mt-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
            Targeted Sub-Questions ({plan.sub_questions.length})
          </p>
          <div className="space-y-2">
            {plan.sub_questions.map((subQuestion, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 rounded-xl border border-border/60 bg-background/80 p-3 text-sm text-foreground transition-colors hover:border-primary/40"
              >
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-bold text-primary mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-snug">{subQuestion}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ResearchDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const researchId = params.id;

  const [researchRun, setResearchRun] = useState<ResearchRun | null>(null);
  const [evidenceItems, setEvidenceItems] = useState<ResearchEvidenceItem[]>([]);
  const [isLoadingEvidence, setIsLoadingEvidence] = useState(false);
  const [plan, setPlan] = useState<ResearchPlan | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState<number | null>(null);

  const loadEvidence = useCallback(async () => {
    setIsLoadingEvidence(true);
    try {
      const items = await apiFetch<ResearchEvidenceItem[]>(
        `/research/${researchId}/evidence`,
      );
      setEvidenceItems(items);
    } catch {
      setEvidenceItems([]);
    } finally {
      setIsLoadingEvidence(false);
    }
  }, [researchId]);

  const loadPlan = useCallback(async () => {
    try {
      const loadedPlan = await apiFetch<ResearchPlan | null>(
        `/research/${researchId}/plan`,
      );
      setPlan(loadedPlan);
    } catch {
      setPlan(null);
    }
  }, [researchId]);

  const [report, setReport] = useState<Report | null>(null);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [decision, setDecision] = useState("");
  const [rating, setRating] = useState("");
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);

  async function handleCancel() {
    setError("");
    setIsCancelling(true);

    try {
      const run = await apiFetch<ResearchRun>(
        `/research/${researchId}/cancel`,
        { method: "POST" },
      );

      setResearchRun(run);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to cancel research",
      );
    } finally {
      setIsCancelling(false);
    }
  }

  const [isResuming, setIsResuming] = useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [isDownloading, setIsDownloading] = useState("");
  const [isCopiedMarkdown, setIsCopiedMarkdown] = useState(false);
  const [isCopiedLink, setIsCopiedLink] = useState(false);

  const loadCompletedReport = useCallback(async () => {
    const loadedReport = await apiFetch<Report>(
      `/research/${researchId}/report`,
    );
    setReport(loadedReport);

    try {
      const loadedEvaluations = await apiFetch<Evaluation[]>(
        `/research/${researchId}/evaluation`,
      );
      setEvaluations(loadedEvaluations);
    } catch {
      setEvaluations([]);
    }
  }, [researchId]);

  const loadResearch = useCallback(async () => {
    const run = await apiFetch<ResearchRun>(`/research/${researchId}`);
    setResearchRun(run);

    if (run.status === "completed") {
      await Promise.all([loadCompletedReport(), loadPlan()]);
    } else if (run.status === "awaiting_approval") {
      await Promise.all([loadEvidence(), loadPlan()]);
    } else {
      void loadPlan();
    }
  }, [loadCompletedReport, loadEvidence, loadPlan, researchId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    async function load() {
      try {
        await loadResearch();
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
            : "Unable to load research",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void load();
  }, [loadResearch, router]);

  async function handleResume() {
    setError("");
    setIsResuming(true);

    try {
      const run = await apiFetch<ResearchRun>(
        `/research/${researchId}/resume`,
        { method: "POST" },
      );

      setResearchRun(run);

      if (run.status === "completed") {
        await Promise.all([loadCompletedReport(), loadPlan()]);
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to resume research",
      );
    } finally {
      setIsResuming(false);
    }
  }

  async function handleApprove() {
    setError("");
    setIsApproving(true);

    try {
      const run = await apiFetch<ResearchRun>(
        `/research/${researchId}/approve`,
        { method: "POST" },
      );

      setResearchRun(run);

      if (run.status === "completed") {
        await Promise.all([loadCompletedReport(), loadPlan()]);
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to approve research",
      );
    } finally {
      setIsApproving(false);
    }
  }

  // Auto-polling while research execution is active
  useEffect(() => {
    if (!researchRun) return;
    const isActive = ACTIVE_EXECUTION_STATUSES.includes(
      researchRun.status as (typeof ACTIVE_EXECUTION_STATUSES)[number],
    );
    if (!isActive) return;

    let isSubscribed = true;
    const intervalId = window.setInterval(async () => {
      try {
        const updated = await apiFetch<ResearchRun>(`/research/${researchId}`);
        if (!isSubscribed) return;
        setResearchRun(updated);

        if (updated.status === "completed") {
          window.clearInterval(intervalId);
          await Promise.all([loadCompletedReport(), loadPlan()]);
        } else if (updated.status === "awaiting_approval") {
          window.clearInterval(intervalId);
          await Promise.all([loadEvidence(), loadPlan()]);
        } else if (
          updated.status === "cancelled" ||
          updated.status === "failed"
        ) {
          window.clearInterval(intervalId);
        } else {
          if (!plan) {
            void loadPlan();
          }
        }
      } catch {
        // network retry
      }
    }, 2000);

    return () => {
      isSubscribed = false;
      window.clearInterval(intervalId);
    };
  }, [
    researchId,
    researchRun,
    loadCompletedReport,
    loadEvidence,
    loadPlan,
    plan,
  ]);

  // Live stopwatch while research is actively running
  useEffect(() => {
    if (!researchRun) return;
    const isActive = ACTIVE_EXECUTION_STATUSES.includes(
      researchRun.status as (typeof ACTIVE_EXECUTION_STATUSES)[number],
    );
    if (!isActive) return;

    const startTimestamp = researchRun.started_at
      ? new Date(researchRun.started_at).getTime()
      : new Date(researchRun.created_at).getTime();

    const updateTimer = () => {
      const now = Date.now();
      setElapsedSeconds(Math.max(0, Math.floor((now - startTimestamp) / 1000)));
    };

    updateTimer();
    const timerId = window.setInterval(updateTimer, 1000);
    return () => window.clearInterval(timerId);
  }, [researchRun]);

  async function handleDownload(
    exportFormat: "markdown" | "pdf" | "docx",
  ) {
    if (!report) return;

    setError("");
    setIsDownloading(exportFormat);

    try {
      const extension =
        exportFormat === "markdown" ? "md" : exportFormat;

      await apiDownload(
        `/reports/${report.id}/export?format=${exportFormat}`,
        `deepcite-report-${report.id}.${extension}`,
      );
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to download report",
      );
    } finally {
      setIsDownloading("");
    }
  }

  async function handleCopyMarkdown() {
    const textToCopy = renderedReportMarkdown || report?.content_markdown;
    if (!textToCopy) return;
    try {
      await navigator.clipboard.writeText(textToCopy);
      setIsCopiedMarkdown(true);
      setTimeout(() => setIsCopiedMarkdown(false), 2000);
    } catch {
      // clipboard fallback
    }
  }

  async function handleCopyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setIsCopiedLink(true);
      setTimeout(() => setIsCopiedLink(false), 2000);
    } catch {
      // clipboard fallback
    }
  }

  // Dynamic browser tab title notifications
  useEffect(() => {
    if (!researchRun) {
      document.title = "Deepcite";
      return;
    }

    if (researchRun.status === "awaiting_approval") {
      document.title = "🔔 Approval Needed - Deepcite";
    } else if (researchRun.status === "completed") {
      document.title = "✅ Report Ready - Deepcite";
    } else if (researchRun.status === "cancelled") {
      document.title = "Cancelled - Deepcite";
    } else if (researchRun.status === "failed") {
      document.title = "Failed - Deepcite";
    } else {
      const timerStr =
        elapsedSeconds !== null ? `(${formatElapsed(elapsedSeconds)}) ` : "";
      const stepName =
        researchRun.status.charAt(0).toUpperCase() +
        researchRun.status.slice(1).replace(/_/g, " ");
      document.title = `⏳ ${timerStr}Deepcite - ${stepName}`;
    }

    return () => {
      document.title = "Deepcite";
    };
  }, [researchRun, elapsedSeconds]);

  async function handleFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setFeedbackSubmitted(false);

    if (!report) return;

    if (!decision && !rating && !comment.trim()) {
      setError("Choose a decision, rating, or enter a comment.");
      return;
    }

    setIsSubmittingFeedback(true);

    try {
      await apiFetch(`/reports/${report.id}/feedback`, {
        method: "POST",
        body: {
          decision: decision || null,
          rating: rating ? Number(rating) : null,
          comment: comment.trim() || null,
        },
      });

      setFeedbackSubmitted(true);
      setComment("");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to submit feedback",
      );
    } finally {
      setIsSubmittingFeedback(false);
    }
  }

  const currentProgress = researchRun
    ? getActiveStepIndex(researchRun.status)
    : -1;

  const reportQuality = evaluations.find(
    (evaluation) => evaluation.dimension === "report_quality",
  );
  const claimSupport = evaluations.find(
    (evaluation) => evaluation.dimension === "claim_support",
  );
  const renderedReportMarkdown = report
    ? filterReportCitationMarkers(
        report.content_markdown,
        report.citations,
      )
    : "";

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/dashboard" className="text-xl font-semibold">
            Deepcite
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-6 py-10">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>

        {isLoading && (
          <p className="mt-8 text-muted-foreground">
            Loading research...
          </p>
        )}

        {error && (
          <p className="mt-6 rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
            {error}
          </p>
        )}

        {researchRun && (
          <>
            <div className="mt-8">
              <p className="text-sm font-medium text-primary">
                Research review
              </p>
              <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                {researchRun.question}
              </h1>

              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary border border-primary/20">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      ACTIVE_EXECUTION_STATUSES.includes(
                        researchRun.status as (typeof ACTIVE_EXECUTION_STATUSES)[number],
                      )
                        ? "bg-amber-500 animate-pulse"
                        : researchRun.status === "completed"
                          ? "bg-emerald-500"
                          : "bg-muted-foreground"
                    }`}
                  />
                  Status: {researchRun.status.replace(/_/g, " ")}
                </span>

                {/* Active stopwatch timer */}
                {ACTIVE_EXECUTION_STATUSES.includes(
                  researchRun.status as (typeof ACTIVE_EXECUTION_STATUSES)[number],
                ) &&
                  elapsedSeconds !== null && (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 px-3 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400 border border-amber-500/20">
                      <Clock
                        className="h-3.5 w-3.5 animate-spin"
                        style={{ animationDuration: "4s" }}
                      />
                      Elapsed: {formatElapsed(elapsedSeconds)}
                    </span>
                  )}

                {/* Completed total duration */}
                {researchRun.status === "completed" &&
                  formatDuration(
                    researchRun.started_at || researchRun.created_at,
                    researchRun.completed_at || report?.created_at,
                  ) && (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
                      <Clock className="h-3.5 w-3.5" />
                      Duration:{" "}
                      {formatDuration(
                        researchRun.started_at || researchRun.created_at,
                        researchRun.completed_at || report?.created_at,
                      )}
                    </span>
                  )}

                <span className="text-xs text-muted-foreground">
                  Created {new Date(researchRun.created_at).toLocaleString()}
                </span>
              </div>
            </div>

            {researchRun.status === "cancelled" && (
              <section className="mt-8 rounded-2xl border border-destructive/30 bg-card p-6">
                <h2 className="text-xl font-semibold text-destructive">
                  Research cancelled
                </h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  This research run was rejected or cancelled. You can return to the
                  dashboard to submit a new research question.
                </p>
                <Link href="/dashboard" className="mt-5 inline-flex">
                  <Button variant="outline">
                    <ArrowLeft className="h-4 w-4" />
                    Start new research
                  </Button>
                </Link>
              </section>
            )}

            {(researchRun.status === "paused" ||
              researchRun.status === "failed") && (
              <section className="mt-8 rounded-2xl border border-amber-500/30 bg-card p-6">
                <h2 className="text-xl font-semibold">Research paused</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  This research run was interrupted. Resume it from the latest
                  saved checkpoint to continue processing.
                </p>
                <Button
                  className="mt-5"
                  onClick={handleResume}
                  disabled={isResuming}
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {isResuming ? "Resuming..." : "Resume research"}
                </Button>
              </section>
            )}

            {researchRun.status === "awaiting_approval" && (
              <section className="mt-8 rounded-2xl border border-primary/30 bg-card p-6">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold">
                      Research Evidence Review
                    </h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Deepcite has completed research and evidence verification.
                      Review the collected evidence before approving the research.
                    </p>
                  </div>
                  {evidenceItems.length > 0 && (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary border border-primary/20 shrink-0">
                      {
                        evidenceItems.filter(
                          (i) =>
                            i.verification_status === "verified" ||
                            i.verification_status === "supported",
                        ).length
                      }{" "}
                      of {evidenceItems.length} Verified
                    </span>
                  )}
                </div>

                <div className="mt-6">
                  <ResearchPlanCard plan={plan} />
                </div>

                {isLoadingEvidence ? (
                  <p className="mt-6 text-sm text-muted-foreground">
                    Loading evidence for review...
                  </p>
                ) : evidenceItems.length > 0 ? (
                  <div className="mt-6 space-y-4">
                    {evidenceItems.map((item, idx) => {
                      const statusInfo = getStatusBadge(item.verification_status);
                      const StatusIcon = statusInfo.icon;

                      return (
                        <div
                          key={item.id || idx}
                          className="rounded-xl border border-border bg-muted/30 p-5 transition-colors"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
                            <div className="flex items-center gap-2">
                              <span
                                className={`inline-flex items-center gap-1 text-xs font-semibold rounded-full px-2.5 py-0.5 ${statusInfo.className}`}
                              >
                                <StatusIcon className="h-3.5 w-3.5" />
                                {statusInfo.label}
                              </span>
                              {item.source_title && (
                                <span className="text-sm font-medium text-foreground">
                                  {item.source_title}
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-3 text-xs text-muted-foreground">
                              {item.source_reliability_score !== null &&
                                item.source_reliability_score !== undefined && (
                                  <span>
                                    Reliability:{" "}
                                    {item.source_reliability_score.toFixed(2)}
                                  </span>
                                )}
                              {item.confidence_score !== null &&
                                item.confidence_score !== undefined && (
                                  <span>
                                    Confidence:{" "}
                                    {item.confidence_score.toFixed(2)}
                                  </span>
                                )}
                            </div>
                          </div>

                          {item.source_url && (
                            <div className="mt-3">
                              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                Source URL
                              </span>
                              <a
                                href={item.source_url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-0.5 flex items-center gap-1 break-words text-sm text-primary hover:underline"
                              >
                                {item.source_url}
                                <ExternalLink className="h-3 w-3 shrink-0" />
                              </a>
                            </div>
                          )}

                          {item.claim_text && (
                            <div className="mt-4">
                              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                Finding / Claim
                              </span>
                              <p className="mt-1 text-sm font-medium text-foreground leading-relaxed">
                                {item.claim_text}
                              </p>
                            </div>
                          )}

                          {item.supporting_evidence && (
                            <div className="mt-4">
                              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                                Supporting Evidence
                              </span>
                              <div className="mt-1.5 rounded-lg bg-card p-3.5 border border-border text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap">
                                {item.supporting_evidence}
                              </div>
                            </div>
                          )}

                          <div className="mt-4 flex items-center justify-between pt-3 border-t border-border/50 text-xs text-muted-foreground">
                            <span>
                              Status: {statusInfo.label}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="mt-6 rounded-xl border border-dashed border-border p-4 text-center text-sm text-muted-foreground">
                    The research evidence has been assembled. Review and approve to proceed to report generation.
                  </div>
                )}

                <div className="mt-6 pt-6 border-t border-border flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-foreground">
                      Approve Research
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      Approve this run to resume report generation.
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-3 shrink-0">
                    <Button
                      type="button"
                      variant="outline"
                      className="border-destructive/50 text-destructive hover:bg-destructive/10"
                      onClick={handleCancel}
                      disabled={isCancelling || isApproving}
                    >
                      <XCircle className="h-4 w-4" />
                      {isCancelling ? "Rejecting..." : "Reject research"}
                    </Button>
                    <Button
                      type="button"
                      onClick={handleApprove}
                      disabled={isApproving || isCancelling}
                    >
                      <CheckCircle2 className="h-4 w-4" />
                      {isApproving ? "Approving..." : "Approve research"}
                    </Button>
                  </div>
                </div>
              </section>
            )}

            {!report &&
              !["awaiting_approval", "paused", "failed", "cancelled"].includes(
                researchRun.status,
              ) && (
                <section className="mt-8 rounded-2xl border border-border bg-card p-6 shadow-sm">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-border pb-4">
                    <div className="flex items-center gap-3">
                      <div className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
                      </div>
                      <div>
                        <h2 className="font-semibold text-lg">
                          {getStepMeta(researchRun.status).title}
                        </h2>
                        <p className="text-sm text-muted-foreground mt-0.5">
                          {getStepMeta(researchRun.status).subtitle}
                        </p>
                      </div>
                    </div>
                    {elapsedSeconds !== null && (
                      <div className="inline-flex items-center gap-2 rounded-full bg-muted px-3.5 py-1.5 text-xs font-medium text-foreground border border-border shrink-0">
                        <Clock className="h-3.5 w-3.5 text-primary" />
                        <span>Elapsed: <strong>{formatElapsed(elapsedSeconds)}</strong></span>
                      </div>
                    )}
                  </div>

                  {plan && (
                    <div className="mt-5">
                      <ResearchPlanCard plan={plan} />
                    </div>
                  )}

                  <div className="mt-6 space-y-3">
                    {detailedProgressSteps.map((step, index) => {
                      const activeIndex = getActiveStepIndex(researchRun.status);
                      const isCompleted = index < activeIndex;
                      const isCurrent = index === activeIndex;

                      return (
                        <div
                          key={step.statusKey}
                          className={`flex items-start gap-3.5 p-3.5 rounded-xl transition-all border ${
                            isCurrent
                              ? "bg-primary/10 border-primary/30 shadow-sm"
                              : isCompleted
                                ? "bg-muted/40 border-border/40"
                                : "border-transparent opacity-60"
                          }`}
                        >
                          <span
                            className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                              isCurrent
                                ? "bg-primary text-primary-foreground animate-pulse"
                                : isCompleted
                                  ? "bg-emerald-500 text-white"
                                  : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {isCompleted ? (
                              <CheckCircle2 className="h-4 w-4" />
                            ) : (
                              index + 1
                            )}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <span
                                className={`text-sm font-medium ${
                                  isCurrent ? "text-primary font-semibold" : ""
                                }`}
                              >
                                {step.label}
                              </span>
                              {isCurrent && (
                                <span className="text-xs text-primary font-medium flex items-center gap-1">
                                  <RefreshCw className="h-3 w-3 animate-spin" /> In progress
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground mt-0.5">
                              {step.description}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </section>
              )}

            {report && (
              <>
                <div className="mt-8">
                  <ResearchPlanCard plan={plan} />
                </div>

                <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
                <article className="rounded-2xl border border-border bg-card p-6">
                  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-primary" />
                      <h2 className="text-xl font-semibold">
                        Research report
                      </h2>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleCopyMarkdown}
                        className="gap-1.5"
                      >
                        {isCopiedMarkdown ? (
                          <>
                            <Check className="h-4 w-4 text-emerald-500" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4" />
                            Copy Report
                          </>
                        )}
                      </Button>

                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={handleCopyLink}
                        className="gap-1.5"
                      >
                        {isCopiedLink ? (
                          <>
                            <Check className="h-4 w-4 text-emerald-500" />
                            Link Copied!
                          </>
                        ) : (
                          <>
                            <Share2 className="h-4 w-4" />
                            Share
                          </>
                        )}
                      </Button>

                      {(["markdown", "pdf", "docx"] as const).map(
                        (format) => (
                          <Button
                            key={format}
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => handleDownload(format)}
                            disabled={isDownloading !== ""}
                          >
                            <Download className="h-4 w-4" />
                            {isDownloading === format
                              ? "Downloading..."
                              : format === "docx"
                                ? "DOCX"
                                : format === "pdf"
                                  ? "PDF"
                                  : "Markdown"}
                          </Button>
                        ),
                      )}
                    </div>
                  </div>

                  {report.executive_summary && (
                    <div className="mt-6 rounded-xl bg-muted p-5">
                      <h3 className="font-semibold">Executive summary</h3>
                      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                        {report.executive_summary}
                      </p>
                    </div>
                  )}

                  <pre className="mt-6 whitespace-pre-wrap font-sans text-sm leading-7">
                    {renderedReportMarkdown}
                  </pre>
                </article>

                <aside className="space-y-6">
                  <section className="rounded-2xl border border-border bg-card p-6">
                    <h2 className="font-semibold">Report completeness</h2>
                    <p className="mt-4 text-3xl font-semibold text-primary">
                      {formatScore(reportQuality?.score)}
                    </p>
                    {reportQuality ? (
                      <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                        <p>
                          {reportQuality.details.word_count ?? 0} /{" "}
                          {reportQuality.details.target_word_count ?? 1500} words
                          {" · "}
                          {reportQuality.details.present_section_count ?? 0} /{" "}
                          {reportQuality.details.required_section_count ?? 7} sections
                          {" · "}
                          {reportQuality.details.citation_count ?? 0} citations
                        </p>
                        <p className="text-xs text-muted-foreground/80">
                          Deterministic structural completeness: word count, section coverage, and citation presence. Evaluates formatting structure, not factual truth.
                        </p>
                      </div>
                    ) : (
                      <p className="mt-1 text-sm text-muted-foreground">
                        Evaluation is unavailable for this run.
                      </p>
                    )}
                  </section>

                  <section className="rounded-2xl border border-border bg-card p-6">
                    <h2 className="font-semibold">Claim support & confidence</h2>
                    <p className="mt-4 text-3xl font-semibold text-primary">
                      {formatScore(
                        claimSupport?.score ?? report.overall_confidence_score,
                      )}
                    </p>
                    <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                      {claimSupport?.details &&
                      claimSupport.details.total_claims ? (
                        <p>
                          {claimSupport.details.supported_count ?? 0} supported
                          {" · "}
                          {claimSupport.details.partially_supported_count ?? 0}{" "}
                          partially supported
                          {" · "}
                          {claimSupport.details.unsupported_count ?? 0} unsupported
                        </p>
                      ) : null}
                      <p className="text-xs text-muted-foreground/80">
                        Derived from fact-check verification and source
                        reliability. This reflects internal evidence matching,
                        not absolute real-world truth.
                      </p>
                    </div>
                  </section>

                  <section className="rounded-2xl border border-border bg-card p-6">
                    <h2 className="font-semibold">
                      Evidence links ({report.citations.length})
                    </h2>

                    <div className="mt-4 space-y-5">
                      {report.citations.map((citation) => (
                        <div
                          key={citation.id}
                          className="border-t border-border pt-4 first:border-t-0 first:pt-0"
                        >
                          <p className="font-medium">
                            {citation.inline_marker}
                          </p>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {citation.claim_text}
                          </p>
                          <a
                            href={citation.source_url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-1 block break-words text-sm text-primary"
                          >
                            {citation.source_title ?? citation.source_url}
                          </a>
                          <p className="mt-1 text-xs text-muted-foreground">
                            Reliability:{" "}
                            {citation.source_reliability_score?.toFixed(2) ??
                              "—"}
                            {" · "}
                            Confidence: {citation.confidence_score.toFixed(2)}
                          </p>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section className="rounded-2xl border border-border bg-card p-6">
                    <h2 className="font-semibold">Your feedback</h2>

                    <form
                      onSubmit={handleFeedback}
                      className="mt-4 space-y-4"
                    >
                      <select
                        value={decision}
                        onChange={(event) =>
                          setDecision(event.target.value)
                        }
                        className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
                      >
                        <option value="">Decision (optional)</option>
                        <option value="approved">Approve report</option>
                        <option value="rejected">Reject report</option>
                      </select>

                      <select
                        value={rating}
                        onChange={(event) => setRating(event.target.value)}
                        className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm"
                      >
                        <option value="">Rating (optional)</option>
                        <option value="1">1 / 5</option>
                        <option value="2">2 / 5</option>
                        <option value="3">3 / 5</option>
                        <option value="4">4 / 5</option>
                        <option value="5">5 / 5</option>
                      </select>

                      <textarea
                        value={comment}
                        onChange={(event) => setComment(event.target.value)}
                        rows={4}
                        maxLength={2000}
                        placeholder="Add a comment"
                        className="w-full resize-none rounded-lg border border-border bg-background px-3 py-3 text-sm"
                      />

                      <Button
                        type="submit"
                        disabled={isSubmittingFeedback}
                      >
                        <Send className="h-4 w-4" />
                        {isSubmittingFeedback
                          ? "Submitting..."
                          : "Submit feedback"}
                      </Button>

                      {feedbackSubmitted && (
                        <p className="text-sm text-emerald-600">
                          Feedback submitted.
                        </p>
                      )}
                    </form>
                  </section>
                </aside>
              </div>
            </>
          )}
          </>
        )}
      </section>
    </main>
  );
}
