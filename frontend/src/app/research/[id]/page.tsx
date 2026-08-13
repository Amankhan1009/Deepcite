"use client";

import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  FileText,
  Send,
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
  };
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

  if (status === "generating_report" || status === "completed") {
    return 3;
  }

  return 0;
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

export default function ResearchDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const researchId = params.id;

  const [researchRun, setResearchRun] = useState<ResearchRun | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [decision, setDecision] = useState("");
  const [rating, setRating] = useState("");
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isApproving, setIsApproving] = useState(false);
  const [isResuming, setIsResuming] = useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [isDownloading, setIsDownloading] = useState("");

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
      await loadCompletedReport();
    }
  }, [loadCompletedReport, researchId]);

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
        await loadCompletedReport();
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
        await loadCompletedReport();
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
    ? progressIndex(researchRun.status)
    : -1;

  const reportQuality = evaluations.find(
    (evaluation) => evaluation.dimension === "report_quality",
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
              <p className="mt-2 text-sm text-muted-foreground">
                Status: {researchRun.status}
              </p>
            </div>

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
                <h2 className="text-xl font-semibold">Approval required</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                  The research evidence has been assembled. Approve this run
                  to resume report generation.
                </p>
                <Button
                  className="mt-5"
                  onClick={handleApprove}
                  disabled={isApproving}
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {isApproving ? "Approving..." : "Approve research"}
                </Button>
              </section>
            )}

            {!report &&
              !["awaiting_approval", "paused", "failed"].includes(
                researchRun.status,
              ) && (
                <section className="mt-8 rounded-2xl border border-border bg-card p-6">
                  <h2 className="font-semibold">Research progress</h2>
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
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {index + 1}
                        </span>
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

            {report && (
              <div className="mt-8 grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
                <article className="rounded-2xl border border-border bg-card p-6">
                  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-primary" />
                      <h2 className="text-xl font-semibold">
                        Research report
                      </h2>
                    </div>

                    <div className="flex flex-wrap gap-2">
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
                    <h2 className="font-semibold">Report quality</h2>
                    <p className="mt-4 text-3xl font-semibold text-primary">
                      {formatScore(reportQuality?.score)}
                    </p>
                    {reportQuality ? (
                      <p className="mt-1 text-sm text-muted-foreground">
                        {reportQuality.details.word_count ?? 0} /{" "}
                        {reportQuality.details.target_word_count ?? 1200} words
                        {" · "}
                        {reportQuality.details.citation_count ?? 0} citation markers
                      </p>
                    ) : (
                      <p className="mt-1 text-sm text-muted-foreground">
                        Evaluation is unavailable for this run.
                      </p>
                    )}
                  </section>

                  <section className="rounded-2xl border border-border bg-card p-6">
                    <h2 className="font-semibold">Internal confidence</h2>
                    <p className="mt-4 text-3xl font-semibold text-primary">
                      {formatScore(report.overall_confidence_score)}
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Internal score derived from fact-check outcomes and source
                      reliability. It is deterministic and project-specific,
                      not a universal benchmark.
                    </p>
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
            )}
          </>
        )}
      </section>
    </main>
  );
}
