import DashboardLayout from "@/components/DashboardLayout";
import MetricCard from "@/components/MetricCard";
import { apiUrl } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import {
  AreaChart, Area, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

type DashboardSummary = {
  monthly_income: number;
  total_spending: number;
  savings_rate: number;
  credit_score: number;
  net_worth: number;
  unread_alerts: number;
};

type SpendingTrendPoint = {
  month: string;
  month_key: string;
  amount: number;
  rolling_average: number;
  vs_rolling_pct: number;
};

type SpendingTrendResponse = {
  months: number;
  rolling_window: number;
  period_total: number;
  latest: SpendingTrendPoint;
  trend: SpendingTrendPoint[];
};

type CategoryBreakdownResponse = {
  categories: { name: string; value: number }[];
};

type GoalsResponse = {
  goals: {
    id: number;
    name: string;
    current: number;
    target: number;
    deadline: string;
    pct: number;
    probability: number | null;
  }[];
};

type RecentAlertsResponse = {
  alerts: {
    id: number;
    severity: "critical" | "warning" | "info" | "insight";
    title: string;
    description: string;
    is_read: boolean;
    created_at: string;
  }[];
};

type DashboardData = {
  summary: DashboardSummary;
  trend: SpendingTrendResponse;
  categories: CategoryBreakdownResponse;
  goals: GoalsResponse;
  alerts: RecentAlertsResponse;
};

const GOLD_COLORS = ["#D4AF37", "#FFD700", "#B8860B", "#DAA520", "#C5A028", "#8B7536", "#A0892C", "#997A1E"];

const SEVERITY_COLOR_MAP: Record<string, string> = {
  critical: "bg-error",
  warning: "bg-warning",
  info: "bg-success",
  insight: "bg-primary",
};

const fetchApi = async <T,>(path: string): Promise<T> => {
  const response = await fetch(apiUrl(path));
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

const formatCurrency = (v: number) => `₹${(v / 1000).toFixed(0)}K`;
const formatCurrencyFull = (v: number) => `₹${Math.round(v).toLocaleString("en-IN")}`;
const formatMonth = (isoDate: string) =>
  new Date(isoDate).toLocaleDateString("en-IN", { month: "short", year: "numeric" });
const clampPct = (value: number) => Math.max(0, Math.min(100, value));
const shorten = (text: string, limit = 80) => (text.length > limit ? `${text.slice(0, limit - 1)}…` : text);

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const spendPoint = payload.find((p: any) => p.dataKey === "amount");
  const rollingPoint = payload.find((p: any) => p.dataKey === "rolling_average");

  return (
    <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
      <p className="text-muted-foreground">{label}</p>
      {spendPoint && <p className="text-primary font-semibold">Spend: ₹{Number(spendPoint.value).toLocaleString("en-IN")}</p>}
      {rollingPoint && <p className="text-muted-foreground">Rolling Avg: ₹{Number(rollingPoint.value).toLocaleString("en-IN")}</p>}
    </div>
  );
};

const Dashboard = () => {
  const {
    data,
    isLoading,
    isError,
    isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey: ["dashboard", "pulse"],
    queryFn: async (): Promise<DashboardData> => {
      const [summary, trend, categories, goals, alerts] = await Promise.all([
        fetchApi<DashboardSummary>("/api/v1/dashboard/summary"),
        fetchApi<SpendingTrendResponse>("/api/v1/dashboard/spending-trend?months=6&rolling_window=3"),
        fetchApi<CategoryBreakdownResponse>("/api/v1/dashboard/category-breakdown"),
        fetchApi<GoalsResponse>("/api/v1/dashboard/goals"),
        fetchApi<RecentAlertsResponse>("/api/v1/dashboard/recent-alerts?limit=4"),
      ]);

      return { summary, trend, categories, goals, alerts };
    },
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const summary = data?.summary;
  const trendData = data?.trend.trend ?? [];
  const categoryData = data?.categories.categories ?? [];
  const goals = data?.goals.goals ?? [];
  const alerts = data?.alerts.alerts ?? [];

  const rollingWindow = data?.trend.rolling_window ?? 3;
  const latestVsRolling = data?.trend.latest?.vs_rolling_pct ?? 0;
  const spendingPositive = latestVsRolling <= 0;
  const spendingChange = summary
    ? `${Math.abs(latestVsRolling).toFixed(1)}% ${spendingPositive ? "below" : "above"} ${rollingWindow}M avg`
    : "Calculating trend";

  return (
    <DashboardLayout>
      {isError && (
        <div className="glass-card p-4 mb-6 border border-error/40">
          <p className="text-sm text-error mb-3">
            Could not load dashboard data: {error instanceof Error ? error.message : "Unknown error"}
          </p>
          <button
            onClick={() => refetch()}
            className="text-xs px-3 py-1.5 rounded-md bg-surface-3 text-foreground hover:bg-surface-2 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
        <MetricCard
          label="Monthly Income"
          value={summary ? formatCurrencyFull(summary.monthly_income) : "Loading..."}
          change="Live month snapshot"
          positive
        />
        <MetricCard
          label="Total Spending"
          value={summary ? formatCurrencyFull(summary.total_spending) : "Loading..."}
          change={spendingChange}
          positive={spendingPositive}
        />
        <MetricCard
          label="Savings Rate"
          value={summary ? `${summary.savings_rate.toFixed(1)}%` : "Loading..."}
          change={summary ? `${formatCurrencyFull(summary.monthly_income - summary.total_spending)} saved` : "Calculating"}
          positive={(summary?.savings_rate ?? 0) >= 0}
        />
        <MetricCard
          label="Credit Score"
          value={summary ? summary.credit_score.toString() : "Loading..."}
          change="Model placeholder"
          positive
        />
        <MetricCard
          label="Net Worth"
          value={summary ? formatCurrencyFull(summary.net_worth) : "Loading..."}
          change={summary ? `${summary.unread_alerts} unread alert${summary.unread_alerts === 1 ? "" : "s"}` : "Loading alerts"}
          positive
        />
      </div>

      {(isLoading || isFetching) && (
        <p className="text-xs text-muted-foreground mb-6">Refreshing your financial pulse...</p>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
        {/* Left column */}
        <div className="xl:col-span-3 space-y-6">
          {/* Spending Trend */}
          <div className="glass-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-foreground">Spending Trend</h3>
              <p className="text-xs text-muted-foreground">vs {rollingWindow}M rolling average</p>
            </div>
            {trendData.length === 0 ? (
              <p className="text-sm text-muted-foreground">No spending trend data yet.</p>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#D4AF37" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#D4AF37" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#6f6650" opacity={0.2} />
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} tickFormatter={formatCurrency} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="amount" stroke="#D4AF37" strokeWidth={2} fill="url(#goldGradient)" />
                  <Line type="monotone" dataKey="rolling_average" stroke="#8B7536" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Category Breakdown */}
          <div className="glass-card p-6">
            <h3 className="text-base font-semibold text-foreground mb-4">Category Breakdown</h3>
            {categoryData.length === 0 ? (
              <p className="text-sm text-muted-foreground">No category data yet for this month.</p>
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="45%" innerRadius={60} outerRadius={100} paddingAngle={2} dataKey="value">
                    {categoryData.map((_, i) => (
                      <Cell key={i} fill={GOLD_COLORS[i % GOLD_COLORS.length]} />
                    ))}
                  </Pie>
                  <Legend
                    verticalAlign="bottom"
                    formatter={(value: string) => <span className="text-xs text-muted-foreground">{value}</span>}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      return (
                        <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
                          <p className="text-foreground font-medium">{payload[0].name}</p>
                          <p className="text-primary">₹{Number(payload[0].value).toLocaleString("en-IN")}</p>
                        </div>
                      );
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Right column */}
        <div className="xl:col-span-2 space-y-6">
          {/* Goals */}
          <div className="glass-card p-6">
            <h3 className="text-base font-semibold text-foreground mb-4">Active Goals</h3>
            {goals.length === 0 ? (
              <p className="text-sm text-muted-foreground">No active goals found.</p>
            ) : (
              <div className="space-y-4">
                {goals.map((g) => (
                  <div key={g.id} className="bg-surface-3 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2 gap-2">
                      <span className="text-sm font-medium text-foreground">{g.name}</span>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">by {formatMonth(g.deadline)}</span>
                    </div>
                    <div className="w-full h-2 bg-surface-1 rounded-full mb-2">
                      <div
                        className="h-full bg-primary rounded-full transition-all duration-500"
                        style={{ width: `${clampPct(g.pct)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">
                        {formatCurrencyFull(g.current)} / {formatCurrencyFull(g.target)}
                      </span>
                      <span className="text-primary font-medium">{g.pct.toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Alerts */}
          <div className="glass-card p-6">
            <h3 className="text-base font-semibold text-foreground mb-4">Recent Alerts</h3>
            {alerts.length === 0 ? (
              <p className="text-sm text-muted-foreground">No alerts right now.</p>
            ) : (
              <div className="space-y-3">
                {alerts.map((a) => (
                  <div key={a.id} className="flex items-start gap-3 bg-surface-3 rounded-lg p-3">
                    <div className={`w-2 h-2 mt-1.5 rounded-full ${SEVERITY_COLOR_MAP[a.severity] ?? "bg-primary"} shrink-0`} />
                    <div>
                      <p className="text-sm text-foreground font-medium">{a.title}</p>
                      <p className="text-xs text-muted-foreground">{shorten(a.description)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
