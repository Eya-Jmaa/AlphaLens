import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutDashboard, TrendingUp, PieChart, FileClock } from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/analyze", label: "Research", icon: TrendingUp },
  { to: "/portfolio", label: "Portfolio", icon: PieChart },
  { to: "/reports", label: "Archive", icon: FileClock },
];

export const MobileNav: React.FC = () => (
  <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 flex border-t border-border bg-card/95 backdrop-blur-md">
    {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
      <NavLink
        key={to}
        to={to}
        end={end}
        className={({ isActive }) =>
          clsx(
            "flex-1 flex flex-col items-center gap-1 py-2 text-[10px] font-mono uppercase tracking-wider font-semibold transition-colors",
            isActive ? "text-primary" : "text-muted-foreground hover:text-foreground"
          )
        }
      >
        <Icon size={16} strokeWidth={2.2} />
        {label}
      </NavLink>
    ))}
  </nav>
);
