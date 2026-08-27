import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, Sparkles, PieChart, FileClock, ShieldAlert } from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/analyze", label: "Analysis", icon: Sparkles },
  { to: "/portfolio", label: "Portfolio", icon: PieChart },
  { to: "/reports", label: "Reports", icon: FileClock },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="hidden md:flex w-60 shrink-0 flex-col border-r border-border bg-sidebar h-screen sticky top-0">
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-border">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-blue-500 flex items-center justify-center text-white font-bold text-sm">
          FA
        </div>
        <div>
          <div className="text-sm font-semibold leading-tight">FinAgent</div>
          <div className="text-[11px] text-muted-foreground leading-tight">Multi-Agent Research</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              )
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-border">
        <div className="flex items-start gap-2 rounded-lg bg-secondary/60 p-3 text-[11px] text-muted-foreground leading-relaxed">
          <ShieldAlert size={14} className="mt-0.5 shrink-0" />
          <span>Informational research only &mdash; not personalized financial advice.</span>
        </div>
      </div>
    </aside>
  );
};
