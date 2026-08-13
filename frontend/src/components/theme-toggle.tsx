"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  useEffect(() => {
    const storedTheme = window.localStorage.getItem("theme");
    const shouldUseDark =
      storedTheme === "dark" ||
      (!storedTheme &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);

    document.documentElement.classList.toggle("dark", shouldUseDark);
  }, []);

  function toggleTheme() {
    const nextIsDark =
      !document.documentElement.classList.contains("dark");

    document.documentElement.classList.toggle("dark", nextIsDark);
    window.localStorage.setItem(
      "theme",
      nextIsDark ? "dark" : "light",
    );
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label="Toggle color theme"
    >
      <Sun className="hidden h-4 w-4 dark:block" />
      <Moon className="block h-4 w-4 dark:hidden" />
    </Button>
  );
}