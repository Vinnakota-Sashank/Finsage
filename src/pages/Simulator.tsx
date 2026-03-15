import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { ArrowUp, Play } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";

const histogramData = [
  { bucket: "₹16L", freq: 12 },
  { bucket: "₹17L", freq: 28 },
  { bucket: "₹18L", freq: 65 },
  { bucket: "₹19L", freq: 98 },
  { bucket: "₹20L", freq: 142 },
  { bucket: "₹21L", freq: 168 },
  { bucket: "₹22L", freq: 185 },
  { bucket: "₹23L", freq: 152 },
  { bucket: "₹24L", freq: 78 },
  { bucket: "₹25L", freq: 42 },
  { bucket: "₹26L", freq: 18 },
  { bucket: "₹27L", freq: 8 },
  { bucket: "₹28L", freq: 4 },
];

const resultMetrics = [
  { label: "Expected Corpus (5yr)", value: "₹22.4L", color: "text-primary" },
  { label: "Best Case (P90)", value: "₹28.7L", color: "text-success" },
  { label: "Worst Case (P10)", value: "₹18.1L", color: "text-warning" },
  { label: "Improvement vs Current", value: "+₹6.8L (+44%)", color: "text-primary", icon: true },
];

const tradeoffs = [
  "Monthly discretionary budget drops: ₹28,000 → ₹23,000",
  "Emergency fund timeline unaffected",
  "Goa trip goal: probability increases 62% → 94%",
];

const Simulator = () => {
  const [scenario] = useState("What if I increase my SIP to ₹25,000 per month?");

  return (
    <DashboardLayout title="What-If Scenario Engine" subtitle="Simulate financial decisions with 1,000 Monte Carlo scenarios">
      {/* Input */}
      <div className="glass-card p-6 mb-6 border-primary/30">
        <p className="text-sm text-muted-foreground mb-3">Describe your scenario:</p>
        <div className="flex gap-3">
          <input
            type="text"
            defaultValue={scenario}
            className="flex-1 bg-surface-3 border border-gold-muted rounded-xl px-4 py-3 text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
          />
          <button className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:brightness-110 transition-all flex items-center gap-2">
            <Play size={16} /> Run Simulation
          </button>
        </div>
      </div>

      {/* Result Metrics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {resultMetrics.map((m, i) => (
          <div key={i} className="glass-card p-5">
            <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">{m.label}</p>
            <p className={`text-2xl font-bold ${m.color} flex items-center gap-1`}>
              {m.icon && <ArrowUp size={20} />}
              {m.value}
            </p>
          </div>
        ))}
      </div>

      {/* Histogram */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-base font-semibold text-foreground mb-1">Probability Distribution (1,000 Simulations)</h3>
        <p className="text-xs text-muted-foreground mb-4">Distribution of projected corpus outcomes</p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={histogramData}>
            <defs>
              <linearGradient id="barGold" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#FFD700" />
                <stop offset="100%" stopColor="#B8860B" />
              </linearGradient>
            </defs>
            <XAxis dataKey="bucket" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 11 }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 11 }} />
            <Tooltip content={({ active, payload, label }: any) => {
              if (!active || !payload?.length) return null;
              return (
                <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
                  <p className="text-foreground">{label}</p>
                  <p className="text-primary">{payload[0].value} simulations</p>
                </div>
              );
            }} />
            <ReferenceLine x="₹22L" stroke="#D4AF37" strokeDasharray="5 5" label={{ value: "Median", fill: "#D4AF37", fontSize: 11 }} />
            <Bar dataKey="freq" fill="url(#barGold)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Comparison + Trade-offs */}
      <div className="grid grid-cols-3 gap-6">
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Current Plan</h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">SIP</span><span className="text-foreground">₹15,000/mo</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Savings Rate</span><span className="text-foreground">18%</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">5yr Corpus</span><span className="text-foreground">₹15.6L</span></div>
          </div>
        </div>
        <div className="glass-card p-6 border-primary/30 gold-glow-sm">
          <h4 className="text-sm font-semibold text-primary mb-4 uppercase tracking-wider">Proposed Plan</h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">SIP</span><span className="text-primary font-semibold">₹25,000/mo</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Savings Rate</span><span className="text-primary font-semibold">26.3%</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">5yr Corpus</span><span className="text-primary font-semibold">₹22.4L</span></div>
          </div>
        </div>
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Trade-off Analysis</h4>
          <div className="space-y-3">
            {tradeoffs.map((t, i) => (
              <p key={i} className="text-sm text-muted-foreground leading-relaxed">• {t}</p>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Simulator;
