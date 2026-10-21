import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Search,
  ShieldCheck,
  UserCheck,
} from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";

const capabilities = [
  {
    icon: Search,
    title: "Multi-agent planning",
    description:
      "Decomposes complex research questions into targeted sub-questions and search strategies.",
  },
  {
    icon: ShieldCheck,
    title: "Verify every claim",
    description:
      "Evaluates source reliability tiers and extracts verbatim empirical quotes before synthesis.",
  },
  {
    icon: UserCheck,
    title: "Human-in-the-loop control",
    description:
      "Inspect verified evidence, reliability scores, and authorize report synthesis with full operator oversight.",
  },
  {
    icon: CheckCircle2,
    title: "Grounded cited reports",
    description:
      "Assembles 7-section reports with traceable citations, evaluations, and 1-click multi-format export.",
  },
];

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <header className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 lg:px-8">
        <Link
          href="/"
          className="text-xl font-semibold tracking-tight"
        >
          Deepcite
        </Link>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link
            href="/login"
            className="hidden rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground sm:inline-flex"
          >
            Log in
          </Link>
          <Link
            href="/register"
            className="inline-flex h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Get started
          </Link>
        </div>
      </header>

      <section className="mx-auto grid w-full max-w-7xl gap-12 px-6 pb-20 pt-16 lg:grid-cols-[1.1fr_0.9fr] lg:px-8 lg:pb-28 lg:pt-24">
        <div className="flex flex-col justify-center">
          <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-primary">
            AI research you can inspect
          </p>

          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">
            Research reports built on evidence, not guesswork.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
            Deepcite coordinates planning, search, verification, reasoning,
            human-in-the-loop approval, and report generation into one traceable research
            workflow.
          </p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/register"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-lg bg-primary px-6 text-base font-medium text-primary-foreground hover:bg-primary/90"
            >
              Create your workspace
              <ArrowRight className="h-4 w-4" />
            </Link>

            <Link
              href="/login"
              className="inline-flex h-12 items-center justify-center rounded-lg border border-border px-6 text-base font-medium hover:bg-muted"
            >
              Sign in
            </Link>
          </div>
        </div>

        <div className="rounded-3xl border border-border bg-card p-6 shadow-2xl shadow-blue-950/10">
          <div className="rounded-2xl border border-border bg-muted p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center rounded-md bg-primary/10 px-2 py-0.5 text-xs font-semibold text-primary">
                    Workflow Preview
                  </span>
                  <p className="text-xs font-medium text-muted-foreground">
                    Example run
                  </p>
                </div>
                <h2 className="mt-1.5 text-lg font-semibold">
                  AI adoption and risk
                </h2>
              </div>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-500/20">
                Sample Output
              </span>
            </div>

            <div className="mt-6 space-y-3">
              {[
                "Planning & decomposition",
                "Parallel source research",
                "Evidence verification",
                "Human-in-the-loop approval",
                "Grounded cited report",
              ].map((step, index) => (
                <div
                  key={step}
                  className={`flex items-center gap-3 rounded-xl px-4 py-3 ${
                    index === 3
                      ? "bg-primary/10 border border-primary/20"
                      : "bg-card"
                  }`}
                >
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
                    {index + 1}
                  </span>
                  <span
                    className={`text-sm ${
                      index === 3 ? "font-semibold text-primary" : "font-medium"
                    }`}
                  >
                    {step}
                  </span>
                  {index === 3 ? (
                    <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-primary/20 px-2 py-0.5 text-[11px] font-semibold text-primary">
                      Operator gate
                    </span>
                  ) : (
                    <CheckCircle2 className="ml-auto h-4 w-4 text-emerald-500" />
                  )}
                </div>
              ))}
            </div>

            <p className="mt-4 text-center text-xs text-muted-foreground">
              Visual preview of the autonomous 5-stage agent execution pipeline.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-card">
        <div className="mx-auto grid w-full max-w-7xl gap-6 px-6 py-16 sm:grid-cols-2 lg:grid-cols-4 lg:px-8">
          {capabilities.map((capability) => {
            const Icon = capability.icon;

            return (
              <article key={capability.title} className="rounded-2xl border border-border p-6">
                <Icon className="h-6 w-6 text-primary" />
                <h2 className="mt-5 text-lg font-semibold">
                  {capability.title}
                </h2>
                <p className="mt-2 leading-7 text-muted-foreground">
                  {capability.description}
                </p>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}