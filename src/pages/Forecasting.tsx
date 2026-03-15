import DashboardLayout from "@/components/DashboardLayout";
import { TrendingUp, CheckCircle, BarChart3 } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from "recharts";

const historicalData = [
  { month: "Apr", spend: 92000 },
  { month: "May", spend: 88000 },
  { month: "Jun", spend: 105000 },
  { month: "Jul", spend: 95000 },
  { month: "Aug", spend: 110000 },
  { month: "Sep", spend: 98400 },
];

const forecastData = [
  { month: "Oct", forecast: 102400, upper: 111000, lower: 94000 },
  { month: "Nov", forecast: 99800, upper: 108000, lower: 91000 },
  { month: "Dec", forecast: 106200, upper: 116000, lower: 97000 },
];

const combinedData = [
  ...historicalData.map(d => ({ month: d.month, spend: d.spend })),
  ...forecastData.map(d => ({ month: d.month, forecast: d.forecast, upper: d.upper, lower: d.lower })),
];

const netWorthData = Array.from({ length: 12 }, (_, i) => ({
  month: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][i],
  assets: 1400000 + i * 35000,
  liabilities: 160000 - i * 2000,
}));

const goalProbs = [
  { name: "Goa Trip", prob: 62 },
  { name: "Emergency Fund", prob: 78 },
  { name: "New Laptop", prob: 34 },
];

const insights = [
  { icon: TrendingUp, text: 'At current trajectory, Emergency Fund target reached by **Nov 2026**' },
  { icon: CheckCircle, text: 'Student loan projected payoff: **March 2029** — 2 months ahead of schedule' },
  { icon: BarChart3, text: 'Mutual fund SIP corpus at 5 years: **₹12.4L** (expected CAGR 12.5%)' },
];

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
  return (
    <DashboardLayout title="Forecasting & Predictions" subtitle="Prophet-driven time series analysis with confidence intervals">
      {/* Spending Forecast */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-base font-semibold text-foreground mb-1">Spending Forecast — Next 3 Months</h3>
        <p className="text-xs text-muted-foreground mb-4">Historical data + AI predictions with 80% confidence interval</p>
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
            <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} tickFormatter={(v) => `₹${v / 1000}K`} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="upper" stroke="none" fill="url(#confGrad)" />
            <Area type="monotone" dataKey="lower" stroke="none" fill="transparent" />
            <Area type="monotone" dataKey="spend" stroke="#D4AF37" strokeWidth={2} fill="url(#spendGrad)" />
            <Area type="monotone" dataKey="forecast" stroke="#D4AF37" strokeWidth={2} strokeDasharray="6 4" fill="url(#confGrad)" />
          </AreaChart>
        </ResponsiveContainer>
        <div className="glass-card p-4 mt-4">
          <p className="text-sm text-muted-foreground">
            Predicted total spend next month: <span className="text-primary font-semibold">₹1,02,400</span> (range: ₹94,000 – ₹1,11,000)
          </p>
        </div>
      </div>

      {/* Two columns */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Goal Probability */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-4">Goal Probability</h3>
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
        </div>

        {/* Net Worth Projection */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-4">Net Worth Projection</h3>
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
            </AreaChart>
          </ResponsiveContainer>
          <div className="bg-surface-3 rounded-lg p-3 mt-3">
            <p className="text-xs text-muted-foreground">
              Projected net worth in 12 months: <span className="text-primary font-semibold">₹15,80,000</span> (+₹3,40,000 from today)
            </p>
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="grid grid-cols-3 gap-4">
        {insights.map((ins, i) => (
          <div key={i} className="glass-card-hover p-5 flex items-start gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <ins.icon size={18} className="text-primary" />
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{renderBold(ins.text)}</p>
          </div>
        ))}
      </div>
    </DashboardLayout>
  );
};

export default Forecasting;
