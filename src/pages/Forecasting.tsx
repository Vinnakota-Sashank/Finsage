import DashboardLayout from "@/components/DashboardLayout";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp, CheckCircle, BarChart3 } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid,
} from "recharts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type GoalProbability = {
  name: string;
  prob: number;
};

type NetWorthPoint = {
  month: string;
  assets: number;
  liabilities: number;
  net_worth: number;
};

type SpendingProjection = {
  historical: { month: string; spend: number }[];
  forecast: { month: string; forecast: number; upper: number; lower: number }[];
  combined: { month: string; spend?: number; forecast?: number; upper?: number; lower?: number }[];
  next_month_forecast: { forecast: number; upper: number; lower: number };
  avg_growth_pct: number;
  confidence_band_pct: number;
};

type ForecastOverviewResponse = {
  spending: SpendingProjection;
  goal_probabilities: GoalProbability[];
  net_worth_projection: NetWorthPoint[];
  insights: string[];
};

const insightIcons = [TrendingUp, CheckCircle, BarChart3];

const fetchApi = async <T,>(path: string): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`);
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

const renderBold = (text: string) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") ? <strong key={i} className="text-primary">{part.slice(2, -2)}</strong> : <span key={i}>{part}</span>
  );
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
      <p className="text-muted-foreground">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-primary">₹{Number(p.value).toLocaleString("en-IN")}</p>
      ))}
    </div>
  );
};

const Forecasting = () => {
  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["forecasting", "overview"],
    queryFn: () => fetchApi<ForecastOverviewResponse>("/api/v1/forecasting/overview"),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const spending = data?.spending;
  const combinedData = spending?.combined ?? [];
  const netWorthData = data?.net_worth_projection ?? [];
  const goalProbs = data?.goal_probabilities ?? [];
  const insights = data?.insights ?? [];

  const nextMonth = spending?.next_month_forecast;

  return (
    <DashboardLayout title="Forecasting & Predictions" subtitle="Prophet-driven time series analysis with confidence intervals">
      {isError && (
        <div className="glass-card p-4 mb-6 border border-error/40">
          <p className="text-sm text-error mb-3">
            Failed to load forecasting data: {error instanceof Error ? error.message : "Unknown error"}
          </p>
          <button
            onClick={() => refetch()}
            className="text-xs px-3 py-1.5 rounded-md bg-surface-3 text-foreground hover:bg-surface-2 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Spending Forecast */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-base font-semibold text-foreground mb-1">Spending Forecast — Next 3 Months</h3>
        <p className="text-xs text-muted-foreground mb-4">Historical data + AI predictions with 80% confidence interval</p>
        {combinedData.length === 0 ? (
          <p className="text-sm text-muted-foreground">No forecasting data available yet.</p>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={combinedData}>
              <defs>
                <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#D4AF37" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#D4AF37" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="confGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#D4AF37" stopOpacity={0.1} />
                  <stop offset="100%" stopColor="#D4AF37" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#6f6650" opacity={0.2} />
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} tickFormatter={(v) => `₹${v / 1000}K`} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="upper" stroke="none" fill="url(#confGrad)" />
              <Area type="monotone" dataKey="lower" stroke="none" fill="transparent" />
              <Area type="monotone" dataKey="spend" stroke="#D4AF37" strokeWidth={2} fill="url(#spendGrad)" />
              <Area type="monotone" dataKey="forecast" stroke="#D4AF37" strokeWidth={2} strokeDasharray="6 4" fill="url(#confGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
        <div className="glass-card p-4 mt-4">
          <p className="text-sm text-muted-foreground">
            Predicted total spend next month: <span className="text-primary font-semibold">₹{Math.round(nextMonth?.forecast ?? 0).toLocaleString("en-IN")}</span>
            {nextMonth && (
              <>
                {" "}(range: ₹{Math.round(nextMonth.lower).toLocaleString("en-IN")} – ₹{Math.round(nextMonth.upper).toLocaleString("en-IN")})
              </>
            )}
          </p>
        </div>
      </div>

      {(isLoading || isFetching) && (
        <p className="text-xs text-muted-foreground mb-6">Refreshing forecast models...</p>
      )}

      {/* Two columns */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        {/* Goal Probability */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-4">Goal Probability</h3>
          {goalProbs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No active goals available for probability modeling.</p>
          ) : (
            <div className="space-y-5">
              {goalProbs.map((g, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="relative w-16 h-16">
                    <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                      <circle cx="18" cy="18" r="15" fill="none" stroke="#222" strokeWidth="3" />
                      <circle cx="18" cy="18" r="15" fill="none" stroke="#D4AF37" strokeWidth="3" strokeLinecap="round"
                        strokeDasharray={`${g.prob * 0.942} 94.2`} />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-primary">{g.prob}%</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{g.name}</p>
                    <p className="text-xs text-muted-foreground">At current savings rate</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Net Worth Projection */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-4">Net Worth Projection</h3>
          {netWorthData.length === 0 ? (
            <p className="text-sm text-muted-foreground">No net-worth projection data available.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={netWorthData}>
                <defs>
                  <linearGradient id="assetGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D4AF37" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#D4AF37" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} tickFormatter={(v) => `₹${v / 100000}L`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="assets" stroke="#D4AF37" strokeWidth={2} fill="url(#assetGrad)" />
                <Area type="monotone" dataKey="liabilities" stroke="#555" strokeWidth={1} fill="rgba(85,85,85,0.1)" />
                <Line type="monotone" dataKey="net_worth" stroke="#FFD700" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
          <div className="bg-surface-3 rounded-lg p-3 mt-3">
            <p className="text-xs text-muted-foreground">
              Projected net worth in 12 months:{" "}
              <span className="text-primary font-semibold">
                ₹{Math.round(netWorthData.at(-1)?.net_worth ?? 0).toLocaleString("en-IN")}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {(insights.length ? insights : ["Forecast insights will appear after model initialization."]).map((text, i) => {
          const Icon = insightIcons[i % insightIcons.length];
          return (
          <div key={i} className="glass-card-hover p-5 flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <Icon size={18} className="text-primary" />
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{renderBold(text)}</p>
          </div>
        );})}
      </div>
    </DashboardLayout>
  );
};

export default Forecasting;
