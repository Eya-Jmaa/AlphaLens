import React from "react";
import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/Layout/AppShell";
import { Dashboard } from "./components/Dashboard/Dashboard";
import { AnalysisPage } from "./components/Analysis/AnalysisPage";
import { PortfolioPage } from "./components/Portfolio/PortfolioPage";
import { ReportsPage } from "./components/Reports/ReportsPage";

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Dashboard />} />
        <Route path="analyze" element={<AnalysisPage />} />
        <Route path="portfolio" element={<PortfolioPage />} />
        <Route path="reports" element={<ReportsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
