import DashboardLayout from "@/components/DashboardLayout";
import { apiUrl } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from "recharts";

type TaxOverviewResponse = {
  section80c: {
    used: number;
    total: number;
    remaining: number;
    pct: number;
    breakdown: { name: string; value: number; fill: string }[];
    tax_saving_opportunity: number;
  };
  section80d: {
    used: number;
    total: number;
    remaining: number;
    tax_saving_opportunity: number;
    recommendation: string;
  };
  epf_projection: { age: number; corpus: number }[];
  festival_predictor: {
    predicted_budget: number;
    recommended_monthly_saving: number;
    start_month: string;
    data: { year: string; spend: number }[];
  };
  upi_merchants: { name: string; amount: number }[];
  highlights: string[];
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

const formatCurrency = (value: number) => `₹${Math.round(value).toLocaleString("en-IN")}`;

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
      <p className="text-muted-foreground">{label}</p>
      <p className="text-primary">₹{Number(payload[0].value).toLocaleString("en-IN")}</p>
    </div>
  );
};

const Tax = () => {
  const { data, isLoading, isFetching, isError, error, refetch } = useQuery({
    queryKey: ["tax", "overview"],
    queryFn: () => fetchApi<TaxOverviewResponse>("/api/v1/tax/overview"),
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });

  const section80C = data?.section80c.breakdown ?? [];
  const epfData = data?.epf_projection ?? [];
  const diwaliData = data?.festival_predictor.data ?? [];
  const upiMerchants = data?.upi_merchants ?? [];

  const used = data?.section80c.used ?? 0;
  const total = data?.section80c.total ?? 150000;
  const pct = data?.section80c.pct?.toFixed(1) ?? "0.0";

  return (
    <DashboardLayout title="India Financial Intelligence" subtitle="Tax optimization & India-specific insights">
      {isError && (
        <div className="glass-card p-4 mb-6 border border-error/40">
          <p className="text-sm text-error mb-3">
            Failed to load tax intelligence: {error instanceof Error ? error.message : "Unknown error"}
          </p>
          <button
            onClick={() => refetch()}
            className="text-xs px-3 py-1.5 rounded-md bg-surface-3 text-foreground hover:bg-surface-2 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Section 80C */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-base font-semibold text-foreground mb-1">Section 80C — Tax Saving Tracker (FY 2025-26)</h3>
        <p className="text-xs text-muted-foreground mb-4">Used: ₹{used.toLocaleString("en-IN")} / ₹{total.toLocaleString("en-IN")} ({pct}%) | Remaining: ₹{(data?.section80c.remaining ?? 0).toLocaleString("en-IN")}</p>
        
        {/* Stacked bar */}
        <div className="w-full h-8 rounded-lg overflow-hidden flex mb-4">
          {section80C.map((s, i) => (
            <div
              key={i}
              className={`h-full flex items-center justify-center text-[10px] font-medium ${i === 3 ? "border border-dashed border-muted-foreground/30 text-muted-foreground" : "text-primary-foreground"}`}
              style={{ width: `${(s.value / total) * 100}%`, background: s.fill }}
            >
              {s.value > 15000 && s.name}
            </div>
          ))}
        </div>
        <div className="flex gap-4 mb-4">
          {section80C.map((s, i) => (
            <span key={i} className="text-xs text-muted-foreground flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded" style={{ background: s.fill, border: i === 3 ? "1px dashed #666" : "none" }} />
              {s.name}: ₹{s.value.toLocaleString("en-IN")}
            </span>
          ))}
        </div>

        <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
          <p className="text-sm text-foreground">
            💡 Invest {formatCurrency(data?.section80c.remaining ?? 0)} in ELSS before March 31 to save
            <span className="text-primary font-semibold"> {formatCurrency(data?.section80c.tax_saving_opportunity ?? 0)}</span> in tax (30% bracket)
          </p>
        </div>
      </div>

      {(isLoading || isFetching) && (
        <p className="text-xs text-muted-foreground mb-6">Refreshing tax intelligence...</p>
      )}

      {/* Two columns */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        {/* 80D */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">Section 80D — Medical Insurance</h3>
          <p className="text-sm text-muted-foreground mb-3">Used: ₹{Math.round(data?.section80d.used ?? 0).toLocaleString("en-IN")} / ₹{Math.round(data?.section80d.total ?? 25000).toLocaleString("en-IN")}</p>
          <div className="w-full h-2 bg-surface-1 rounded-full mb-4">
            <div
              className="h-full bg-primary/30 rounded-full"
              style={{ width: `${((data?.section80d.used ?? 0) / (data?.section80d.total ?? 1)) * 100}%` }}
            />
          </div>
          <p className="text-sm text-muted-foreground">
            {data?.section80d.recommendation ?? "No recommendation available"} for additional
            <span className="text-primary font-medium"> {formatCurrency(data?.section80d.tax_saving_opportunity ?? 0)}</span> tax saving
          </p>
        </div>

        {/* EPF */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">EPF Corpus Projection</h3>
          <p className="text-xs text-muted-foreground mb-3">Current ₹5.6L → ₹1.2Cr at age 60 @ 8.15%</p>
          {epfData.length === 0 ? (
            <p className="text-sm text-muted-foreground">No EPF projection data available.</p>
          ) : (
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={epfData}>
                <XAxis dataKey="age" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="corpus" stroke="#D4AF37" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Festival */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">🎆 Festival Budget Predictor</h3>
          <p className="text-sm text-primary font-semibold mb-1">Diwali 2026 Predicted Budget: {formatCurrency(data?.festival_predictor.predicted_budget ?? 0)}</p>
          <p className="text-xs text-muted-foreground mb-3">
            Suggestion: Start saving {formatCurrency(data?.festival_predictor.recommended_monthly_saving ?? 0)}/month from {data?.festival_predictor.start_month ?? "Aug"}
          </p>
          {diwaliData.length === 0 ? (
            <p className="text-sm text-muted-foreground">No historical festival data available.</p>
          ) : (
            <ResponsiveContainer width="100%" height={100}>
              <BarChart data={diwaliData}>
                <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
                <YAxis hide />
                <Bar dataKey="spend" fill="#D4AF37" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* UPI */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">UPI Transaction Intelligence</h3>
          <p className="text-xs text-muted-foreground mb-4">Auto-categorized from live UPI transaction patterns this month</p>
          <div className="space-y-3">
            {upiMerchants.length === 0 && (
              <p className="text-sm text-muted-foreground">No UPI merchant activity available yet.</p>
            )}
            {upiMerchants.map((m, i) => {
              const maxAmt = upiMerchants[0]?.amount ?? 1;
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-16 shrink-0">{m.name}</span>
                  <div className="flex-1 h-4 bg-surface-1 rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${(m.amount / maxAmt) * 100}%` }} />
                  </div>
                  <span className="text-xs text-primary font-medium w-20 text-right">{formatCurrency(m.amount)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {data?.highlights?.length ? (
        <div className="glass-card p-6 mt-6">
          <h3 className="text-base font-semibold text-foreground mb-3">Highlights</h3>
          <div className="space-y-2">
            {data.highlights.map((item, index) => (
              <p key={index} className="text-sm text-muted-foreground">• {item}</p>
            ))}
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  );
};

export default Tax;
