import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer,
} from "recharts";

const weeklyAlerts = [
  { week: "W1", count: 2 },
  { week: "W2", count: 5 },
  { week: "W3", count: 3 },
  { week: "W4", count: 4 },
];

type Severity = "all" | "critical" | "warning" | "info" | "insight";

interface Alert {
  severity: "critical" | "warning" | "info" | "insight";
  title: string;
  desc: string;
  action: string;
  time: string;
}

const alerts: Alert[] = [
  {
    severity: "critical",
    title: "Unusual Spending Spike Detected",
    desc: "Shopping spend this week: ₹12,400 — that's 3.1× your weekly average of ₹4,000. Primary transactions: Amazon ₹6,200, Flipkart ₹4,800.",
    action: "Review Transactions",
    time: "2 hours ago",
  },
  {
    severity: "warning",
    title: "Credit Utilization Rising",
    desc: "Credit card utilization at 68% (₹24,000 / ₹35,000 limit). Credit scores typically drop when utilization exceeds 30%. Pay ₹15,000 before March 20 billing cycle.",
    action: "Set Payment Reminder",
    time: "5 hours ago",
  },
  {
    severity: "warning",
    title: "Dining Budget Almost Exhausted",
    desc: "Dining budget: ₹7,400 / ₹8,000 used (92%) with 11 days remaining this month.",
    action: "Adjust Budget",
    time: "Yesterday",
  },
  {
    severity: "info",
    title: "Upcoming Auto-Debit",
    desc: "SIP auto-debit of ₹15,000 scheduled for tomorrow (March 13). Current savings account balance: ₹2,45,000 — sufficient.",
    action: "View Schedule",
    time: "Yesterday",
  },
  {
    severity: "insight",
    title: "Missing Recurring Transaction",
    desc: "Netflix subscription (₹649) was not charged this billing cycle. Last charge: Feb 10. Subscription may have been cancelled or card expired.",
    action: "Check Subscription",
    time: "2 days ago",
  },
  {
    severity: "warning",
    title: "Goal At Risk",
    desc: "Goa Trip savings: At current savings rate, projected to reach ₹46,200 by June — ₹3,800 short of your ₹50,000 target.",
    action: "Adjust Savings Plan",
    time: "3 days ago",
  },
];

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
  const filtered = filter === "all" ? alerts : alerts.filter(a => a.severity === filter);

  return (
    <DashboardLayout title="Proactive Intelligence Alerts" subtitle="AI-powered anomaly detection and insights">
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
        {filtered.map((a, i) => (
          <div key={i} className="glass-card-hover p-5 flex items-start gap-4">
            <div className={`w-2.5 h-2.5 rounded-full ${severityColors[a.severity]} mt-1.5 shrink-0`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <h4 className="text-sm font-semibold text-foreground">{a.title}</h4>
                <span className="text-xs text-muted-foreground shrink-0 ml-4">{a.time}</span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed mb-3">{a.desc}</p>
              <button className="text-xs px-4 py-1.5 rounded-lg border border-primary/30 text-primary hover:bg-primary/10 transition-colors">
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
