import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import DashboardLayout from "@/components/DashboardLayout";
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer,
} from "recharts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type Severity = "all" | "critical" | "warning" | "info" | "insight";

interface Alert {
  id: number;
  severity: "critical" | "warning" | "info" | "insight";
  title: string;
  desc: string;
  action: string;
  time: string;
  is_read: boolean;
}

interface AlertsSummaryResponse {
  filter: string;
  unread_count: number;
  weekly_alerts: { week: string; count: number }[];
  alerts: Alert[];
}

const fetchApi = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      detail = body?.detail ?? detail;
    } catch {
      // Keep default HTTP status text.
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
};

const severityColors: Record<string, string> = {
  critical: "bg-error",
  warning: "bg-warning",
  info: "bg-success",
  insight: "bg-info",
};

const tabs: { label: string; value: Severity }[] = [
  { label: "All", value: "all" },
  { label: "Critical", value: "critical" },
  { label: "Warnings", value: "warning" },
  { label: "Info", value: "info" },
  { label: "Insights", value: "insight" },
];

const Alerts = () => {
  const [filter, setFilter] = useState<Severity>("all");

  const { data, isLoading, isFetching, isError, error, refetch } = useQuery({
    queryKey: ["alerts", "summary", filter],
    queryFn: () => fetchApi<AlertsSummaryResponse>(`/api/v1/alerts/summary?severity=${filter}&weeks=4`),
    staleTime: 15_000,
    refetchOnWindowFocus: false,
  });

  const weeklyAlerts = data?.weekly_alerts ?? [];
  const filtered = data?.alerts ?? [];

  const handleAction = async (alertId: number) => {
    try {
      await fetchApi(`/api/v1/alerts/${alertId}/read`, { method: "PATCH" });
      await refetch();
    } catch {
      // Non-blocking action
    }
  };

  return (
    <DashboardLayout title="Proactive Intelligence Alerts" subtitle="AI-powered anomaly detection and insights">
      {isError && (
        <div className="glass-card p-4 mb-6 border border-error/40">
          <p className="text-sm text-error mb-3">
            Failed to load alerts: {error instanceof Error ? error.message : "Unknown error"}
          </p>
          <button
            onClick={() => refetch()}
            className="text-xs px-3 py-1.5 rounded-md bg-surface-3 text-foreground hover:bg-surface-2 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b border-gold-muted">
        {tabs.map(t => (
          <button
            key={t.value}
            onClick={() => setFilter(t.value)}
            className={`px-4 py-2.5 text-sm font-medium transition-colors relative ${
              filter === t.value ? "text-primary" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
            {filter === t.value && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />}
          </button>
        ))}
      </div>

      {(isLoading || isFetching) && (
        <p className="text-xs text-muted-foreground mb-6">Refreshing alert intelligence...</p>
      )}

      {data && (
        <p className="text-xs text-muted-foreground mb-4">Unread alerts: {data.unread_count}</p>
      )}

      {/* Mini chart */}
      <div className="glass-card p-4 mb-6 max-w-xs">
        <p className="text-xs text-muted-foreground mb-2">Alerts per Week</p>
        <ResponsiveContainer width="100%" height={60}>
          <BarChart data={weeklyAlerts}>
            <XAxis dataKey="week" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
            <YAxis hide />
            <Bar dataKey="count" fill="#D4AF37" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Alert list */}
      <div className="space-y-3">
        {filtered.length === 0 && (
          <p className="text-sm text-muted-foreground">No alerts for the selected filter.</p>
        )}
        {filtered.map((a, i) => (
          <div key={i} className="glass-card-hover p-5 flex items-start gap-4">
            <div className={`w-2.5 h-2.5 rounded-full ${severityColors[a.severity]} mt-1.5 shrink-0`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-sm font-semibold text-foreground">{a.title}</h4>
                <span className="text-xs text-muted-foreground shrink-0 ml-4">{a.time}</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed mb-3">{a.desc}</p>
              <button
                onClick={() => handleAction(a.id)}
                className="text-xs px-4 py-1.5 rounded-lg border border-primary/30 text-primary hover:bg-primary/10 transition-colors"
              >
                {a.action}
              </button>
            </div>
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
};

export default Alerts;
