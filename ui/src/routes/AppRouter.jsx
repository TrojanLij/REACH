import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "../layouts/AppLayout";
import { DashboardPage } from "../pages/DashboardPage";
import { PluginsPage } from "../pages/PluginsPage";
import { RouteCreatePage } from "../pages/RouteCreatePage";
import { RoutesListPage } from "../pages/RoutesListPage";
import { LogsConsolePage } from "../pages/LogsConsolePage";
import { PlaygroundPage } from "../pages/PlaygroundPage";
import { RuleBuilderPage } from "../pages/RuleBuilderPage";
import { DnsZonesPage } from "../pages/DnsZonesPage";
import { NotFoundPage } from "../pages/NotFoundPage";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="plugins" element={<PluginsPage />} />
        <Route path="logs" element={<LogsConsolePage />} />
        <Route path="playground" element={<PlaygroundPage />} />
        <Route path="rules" element={<RuleBuilderPage />} />
        <Route path="dns" element={<DnsZonesPage />} />
        <Route path="routes" element={<RoutesListPage />} />
        <Route path="routes/new" element={<RouteCreatePage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
