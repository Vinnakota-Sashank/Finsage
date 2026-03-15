import DashboardLayout from "@/components/DashboardLayout";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from "recharts";

const section80C = [
  { name: "EPF", value: 86400, fill: "#B8860B" },
  { name: "ELSS SIP", value: 18000, fill: "#D4AF37" },
  { name: "PPF", value: 24000, fill: "#FFD700" },
  { name: "Remaining", value: 21600, fill: "#222" },
];

const epfData = Array.from({ length: 30 }, (_, i) => ({
  age: 30 + i,
  corpus: Math.round(560000 * Math.pow(1.0815, i)),
}));

const diwaliData = [
  { year: "2024", spend: 22000 },
  { year: "2025", spend: 25000 },
  { year: "2026 (est)", spend: 28000 },
];

const upiMerchants = [
  { name: "Swiggy", amount: 5200 },
  { name: "Amazon", amount: 4800 },
  { name: "Zomato", amount: 3100 },
  { name: "Uber", amount: 2100 },
  { name: "Flipkart", amount: 1900 },
];

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
  const used = 128400;
  const total = 150000;
  const pct = ((used / total) * 100).toFixed(1);

  return (
    <DashboardLayout title="India Financial Intelligence" subtitle="Tax optimization & India-specific insights">
      {/* Section 80C */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-base font-semibold text-foreground mb-1">Section 80C — Tax Saving Tracker (FY 2025-26)</h3>
        <p className="text-xs text-muted-foreground mb-4">Used: ₹{used.toLocaleString("en-IN")} / ₹{total.toLocaleString("en-IN")} ({pct}%) | Remaining: ₹{(total - used).toLocaleString("en-IN")}</p>
        
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
          <p className="text-sm text-foreground">💡 Invest ₹21,600 in ELSS before March 31 to save <span className="text-primary font-semibold">₹6,480</span> in tax (30% bracket)</p>
        </div>
      </div>

      {/* Two columns */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* 80D */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">Section 80D — Medical Insurance</h3>
          <p className="text-sm text-muted-foreground mb-3">Used: ₹0 / ₹25,000</p>
          <div className="w-full h-2 bg-surface-1 rounded-full mb-4">
            <div className="h-full bg-primary/30 rounded-full" style={{ width: "0%" }} />
          </div>
          <p className="text-sm text-muted-foreground">Consider health insurance for additional <span className="text-primary font-medium">₹7,500</span> tax saving</p>
        </div>

        {/* EPF */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">EPF Corpus Projection</h3>
          <p className="text-xs text-muted-foreground mb-3">Current ₹5.6L → ₹1.2Cr at age 60 @ 8.15%</p>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={epfData}>
              <XAxis dataKey="age" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} tickFormatter={(v) => `₹${(v / 100000).toFixed(0)}L`} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="corpus" stroke="#D4AF37" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Festival */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">🎆 Festival Budget Predictor</h3>
          <p className="text-sm text-primary font-semibold mb-1">Diwali 2026 Predicted Budget: ₹28,000</p>
          <p className="text-xs text-muted-foreground mb-3">Suggestion: Start saving ₹7,000/month from August</p>
          <ResponsiveContainer width="100%" height={100}>
            <BarChart data={diwaliData}>
              <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <YAxis hide />
              <Bar dataKey="spend" fill="#D4AF37" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* UPI */}
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-foreground mb-2">UPI Transaction Intelligence</h3>
          <p className="text-xs text-muted-foreground mb-4">Auto-categorized from 142 UPI transactions this month</p>
          <div className="space-y-3">
            {upiMerchants.map((m, i) => {
              const maxAmt = upiMerchants[0].amount;
              return (
                <div key={i} className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-16 shrink-0">{m.name}</span>
                  <div className="flex-1 h-4 bg-surface-1 rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${(m.amount / maxAmt) * 100}%` }} />
                  </div>
                  <span className="text-xs text-primary font-medium w-14 text-right">₹{m.amount.toLocaleString("en-IN")}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Tax;
