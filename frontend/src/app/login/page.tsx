"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import { saveToken } from "@/lib/auth";

type TokenResponse = {
  access_token: string;
  token_type: string;
};

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      const response = await apiFetch<TokenResponse>("/auth/login", {
        method: "POST",
        body: { email, password },
      });

      saveToken(response.access_token);
      router.push("/dashboard");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to sign in",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-12">
      <div className="w-full max-w-md">
        <Link href="/" className="text-xl font-semibold">
          Deepcite
        </Link>

        <div className="mt-8 rounded-2xl border border-border bg-card p-8 shadow-xl shadow-slate-950/5">
          <h1 className="text-2xl font-semibold">Welcome back</h1>

          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to continue your research.
          </p>

          {error && (
            <p className="mt-5 rounded-lg bg-red-100 px-3 py-2 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
              {error}
            </p>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <label className="block">
              <span className="text-sm font-medium">Email</span>
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
                className="mt-2 h-11 w-full rounded-lg border border-border bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-primary"
                placeholder="you@example.com"
              />
            </label>

            <div>
              <div className="flex items-center justify-between">
                <label htmlFor="password-input" className="text-sm font-medium">
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="text-xs font-medium text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1"
                >
                  {showPassword ? (
                    <>
                      <EyeOff className="h-3.5 w-3.5" />
                      Hide password
                    </>
                  ) : (
                    <>
                      <Eye className="h-3.5 w-3.5" />
                      Show password
                    </>
                  )}
                </button>
              </div>
              <div className="relative mt-2">
                <input
                  id="password-input"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  className="h-11 w-full rounded-lg border border-border bg-background pl-3 pr-10 text-sm outline-none focus:ring-2 focus:ring-primary"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  title={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Do not have an account?{" "}
            <Link
              href="/register"
              className="font-medium text-primary hover:underline"
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}