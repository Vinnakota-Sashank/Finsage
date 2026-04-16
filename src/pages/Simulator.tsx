import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import DashboardLayout from "@/components/DashboardLayout";
import { ArrowUp, Play } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type SimulatorResponse = {
  scenario: string;
  metrics: {
    expected_corpus: number;
    best_case_p90: number;
    worst_case_p10: number;
    improvement_value: number;
    improvement_pct: number;
    median: number;
  };
  histogram: { bucket: string; freq: number }[];
  comparison: {
    current: { sip: number; savings_rate: number; corpus: number };
    proposed: { sip: number; savings_rate: number; corpus: number };
  };
  tradeoffs: string[];
};

const formatCurrency = (value: number) => `₹${Math.round(value).toLocaleString("en-IN")}`;

const runSimulation = async (scenario: string): Promise<SimulatorResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/v1/simulator/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario, years: 5, runs: 1000 }),
  });

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

  return response.json() as Promise<SimulatorResponse>;
};

const Simulator = () => {
  const [scenarioInput, setScenarioInput] = useState("What if I increase my SIP to ₹25,000 per month?");
  const [submittedScenario, setSubmittedScenario] = useState("What if I increase my SIP to ₹25,000 per month?");

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["simulator", submittedScenario],
    queryFn: () => runSimulation(submittedScenario),
    staleTime: 0,
    refetchOnWindowFocus: false,
  });

  const metrics = data?.metrics;
  const histogramData = data?.histogram ?? [];
  const comparison = data?.comparison;
  const tradeoffs = data?.tradeoffs ?? [];

  const resultMetrics = [
    { label: "Expected Corpus (5yr)", value: formatCurrency(metrics?.expected_corpus ?? 0), color: "text-primary" },
    { label: "Best Case (P90)", value: formatCurrency(metrics?.best_case_p90 ?? 0), color: "text-success" },
    { label: "Worst Case (P10)", value: formatCurrency(metrics?.worst_case_p10 ?? 0), color: "text-warning" },
    {
      label: "Improvement vs Current",
      value: `${metrics?.improvement_value && metrics.improvement_value >= 0 ? "+" : ""}${formatCurrency(metrics?.improvement_value ?? 0)} (${metrics?.improvement_pct ?? 0}%)`,
      color: "text-primary",
      icon: true,
    },
  ];

  return (
    <DashboardLayout title="What-If Scenario Engine" subtitle="Simulate financial decisions with 1,000 Monte Carlo scenarios">
      {isError && (
        <div className="glass-card p-4 mb-6 border border-error/40">
          <p className="text-sm text-error mb-3">
            Simulation failed: {error instanceof Error ? error.message : "Unknown error"}
          </p>
          <button
            onClick={() => refetch()}
            className="text-xs px-3 py-1.5 rounded-md bg-surface-3 text-foreground hover:bg-surface-2 transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* Input */}
      <div className="glass-card p-6 mb-6 border-primary/30">
        <p className="text-sm text-muted-foreground mb-3">Describe your scenario:</p>
        <div className="flex gap-3">
          <input
            type="text"
            value={scenarioInput}
            onChange={(e) => setScenarioInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                setSubmittedScenario(scenarioInput.trim() || submittedScenario);
              }
            }}
            className="flex-1 bg-surface-3 border border-gold-muted rounded-xl px-4 py-3 text-sm text-foreground focus:outline-none focus:border-primary transition-colors"
          />
          <button
            onClick={() => setSubmittedScenario(scenarioInput.trim() || submittedScenario)}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-semibold text-sm hover:brightness-110 transition-all flex items-center gap-2"
          >
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

      {(isLoading || isFetching) && (
        <p className="text-xs text-muted-foreground mb-6">Running 1,000 scenario simulations...</p>
      )}

      {/* Histogram */}
      <div className="glass-card p-6 mb-6">
        <h3 className="text-base font-semibold text-foreground mb-1">Probability Distribution (1,000 Simulations)</h3>
        <p className="text-xs text-muted-foreground mb-4">Distribution of projected corpus outcomes</p>
        {histogramData.length === 0 ? (
          <p className="text-sm text-muted-foreground">No simulation histogram data yet.</p>
        ) : (
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
              <ReferenceLine x={histogramData[Math.floor(histogramData.length / 2)]?.bucket} stroke="#D4AF37" strokeDasharray="5 5" label={{ value: "Median", fill: "#D4AF37", fontSize: 11 }} />
              <Bar dataKey="freq" fill="url(#barGold)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Comparison + Trade-offs */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Current Plan</h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">SIP</span><span className="text-foreground">{formatCurrency(comparison?.current.sip ?? 0)}/mo</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Savings Rate</span><span className="text-foreground">{comparison?.current.savings_rate ?? 0}%</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">5yr Corpus</span><span className="text-foreground">{formatCurrency(comparison?.current.corpus ?? 0)}</span></div>
          </div>
        </div>
        <div className="glass-card p-6 border-primary/30 gold-glow-sm">
          <h4 className="text-sm font-semibold text-primary mb-4 uppercase tracking-wider">Proposed Plan</h4>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">SIP</span><span className="text-primary font-semibold">{formatCurrency(comparison?.proposed.sip ?? 0)}/mo</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">Savings Rate</span><span className="text-primary font-semibold">{comparison?.proposed.savings_rate ?? 0}%</span></div>
            <div className="flex justify-between"><span className="text-muted-foreground">5yr Corpus</span><span className="text-primary font-semibold">{formatCurrency(comparison?.proposed.corpus ?? 0)}</span></div>
          </div>
        </div>
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Trade-off Analysis</h4>
          <div className="space-y-3">
            {(tradeoffs.length ? tradeoffs : ["No trade-off insights available yet."]).map((t, i) => (
              <p key={i} className="text-sm text-muted-foreground leading-relaxed">• {t}</p>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Simulator;
