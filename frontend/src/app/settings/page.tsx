"use client";

import Link from "next/link";
import { ArrowLeft, BarChart3, Save } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ThemeToggle } from "@/components/theme-toggle";
import { Button } from "@/components/ui/button";
import { ApiError, apiFetch } from "@/lib/api";
import { clearToken, getToken } from "@/lib/auth";

type UserSettings = {
  id: string;
  user_id: string;
  display_name: string | null;
  timezone: string;
  theme: string;
  created_at: string;
  updated_at: string;
};

export default function SettingsPage() {
  const router = useRouter();

  const [displayName, setDisplayName] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [theme, setTheme] = useState("system");

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }

    async function loadSettings() {
      try {
        const settings = await apiFetch<UserSettings>("/settings");

        setDisplayName(settings.display_name ?? "");
        setTimezone(settings.timezone);
        setTheme(settings.theme);
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
            : "Unable to load settings",
        );
      } finally {
        setIsLoading(false);
      }
    }

    void loadSettings();
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setMessage("");
    setIsSaving(true);

    try {
      await apiFetch<UserSettings>("/settings", {
        method: "PATCH",
        body: {
          display_name: displayName.trim() || null,
          timezone,
          theme,
        },
      });

      setMessage("Settings saved successfully.");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to save settings",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6 lg:px-8">
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
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-3xl px-6 py-10 lg:px-8">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-sm text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to dashboard
        </Link>

        <div className="mt-8">
          <p className="text-sm font-medium text-primary">Preferences</p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight">
            Settings
          </h1>

          <p className="mt-2 text-muted-foreground">
            Manage your profile and application preferences.
          </p>
        </div>

        {isLoading ? (
          <div className="mt-8 rounded-xl border border-border bg-card p-8 text-muted-foreground">
            Loading settings...
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="mt-8 space-y-6 rounded-xl border border-border bg-card p-6"
          >
            {error && (
              <p className="rounded-lg bg-red-100 px-4 py-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
                {error}
              </p>
            )}

            {message && (
              <p className="rounded-lg bg-green-100 px-4 py-3 text-sm text-green-700 dark:bg-green-950 dark:text-green-300">
                {message}
              </p>
            )}

            <label className="block">
              <span className="text-sm font-medium">Display name</span>

              <input
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                placeholder="Your name"
                className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-primary"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium">Timezone</span>

              <select
                value={timezone}
                onChange={(event) => setTimezone(event.target.value)}
                className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-primary"
              >
                <option value="UTC">UTC</option>
                <option value="Asia/Kolkata">Asia/Kolkata</option>
                <option value="America/New_York">America/New_York</option>
                <option value="Europe/London">Europe/London</option>
                <option value="Asia/Singapore">Asia/Singapore</option>
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium">Theme</span>

              <select
                value={theme}
                onChange={(event) => setTheme(event.target.value)}
                className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 outline-none focus:border-primary"
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </label>

            <Button type="submit" disabled={isSaving}>
              <Save className="h-4 w-4" />
              {isSaving ? "Saving..." : "Save settings"}
            </Button>
          </form>
        )}
      </section>
    </main>
  );
}