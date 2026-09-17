import React, { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { MarketTicker } from "./MarketTicker";
import { MobileNav } from "./MobileNav";
import { ErrorBoundary } from "../Common/ErrorBoundary";

const DARK_MODE_KEY = "alphalens:dark-mode";

function getInitialDarkMode(): boolean {
  try {
    const stored = localStorage.getItem(DARK_MODE_KEY);
    if (stored !== null) return stored === "true";
  } catch {
    // localStorage unavailable (private mode etc.) - fall through to the default below
  }
  // Default to the modern neo-fintech light aesthetic from the reference design
  return false;
}

type PageMeta = { title: string; subtitle?: string };

export const PageMetaContext = React.createContext<(meta: PageMeta) => void>(() => {});

export const AppShell: React.FC = () => {
  const [darkMode, setDarkMode] = useState(getInitialDarkMode);
  const [pageMeta, setPageMeta] = useState<PageMeta>({ title: "Overview" });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    try {
      localStorage.setItem(DARK_MODE_KEY, String(darkMode));
    } catch {
      // ignore
    }
  }, [darkMode]);

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <div className="no-print contents">
        <Sidebar />
      </div>
      <div className="flex-1 flex flex-col min-w-0">
        <div className="no-print">
          <Header
            darkMode={darkMode}
            onToggleDarkMode={() => setDarkMode((d) => !d)}
            title={pageMeta.title}
            subtitle={pageMeta.subtitle}
          />
          <MarketTicker />
        </div>
        <main className="flex-1 px-4 md:px-8 py-6 pb-20 md:pb-6 max-w-[1600px] w-full mx-auto">
          <ErrorBoundary>
            <PageMetaContext.Provider value={setPageMeta}>
              <Outlet />
            </PageMetaContext.Provider>
          </ErrorBoundary>
        </main>
      </div>

      <div className="no-print">
        <MobileNav />
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4500,
          style: {
            background: "hsl(var(--card))",
            color: "hsl(var(--foreground))",
            border: "1px solid hsl(var(--border))",
          },
        }}
      />
    </div>
  );
};

/** Lets a page set the header's title/subtitle without prop-drilling through the router. */
export function usePageMeta(meta: PageMeta) {
  const setPageMeta = React.useContext(PageMetaContext);
  useEffect(() => {
    setPageMeta(meta);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meta.title, meta.subtitle]);
}
