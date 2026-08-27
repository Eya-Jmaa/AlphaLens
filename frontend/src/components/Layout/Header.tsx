import React from "react";
import { Moon, Sun } from "lucide-react";

type HeaderProps = {
  darkMode: boolean;
  onToggleDarkMode: () => void;
  title: string;
  subtitle?: string;
};

export const Header: React.FC<HeaderProps> = ({ darkMode, onToggleDarkMode, title, subtitle }) => {
  return (
    <header className="w-full border-b border-border bg-card/60 backdrop-blur sticky top-0 z-10">
      <div className="px-4 md:px-8 h-16 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold leading-tight">{title}</h1>
          {subtitle && <p className="text-xs text-muted-foreground leading-tight">{subtitle}</p>}
        </div>

        <button
          onClick={onToggleDarkMode}
          aria-label="Toggle dark mode"
          className="w-9 h-9 flex items-center justify-center rounded-md border border-border text-sm bg-background hover:bg-secondary transition"
        >
          {darkMode ? <Sun size={16} /> : <Moon size={16} />}
        </button>
      </div>
    </header>
  );
};
