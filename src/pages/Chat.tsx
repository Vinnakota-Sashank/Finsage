import { useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { Send, Sparkles } from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, LineChart, Line,
} from "recharts";

const GOLD_COLORS = ["#D4AF37", "#FFD700", "#B8860B", "#DAA520"];

const foodBreakdown = [
  { name: "Swiggy", value: 5200 },
  { name: "Zomato", value: 3100 },
  { name: "Dining Out", value: 4200 },
  { name: "Groceries", value: 2300 },
];

const comparisonData = [
  { cat: "Swiggy", this: 5200, last: 4800 },
  { cat: "Zomato", this: 3100, last: 2600 },
  { cat: "Dining", this: 4200, last: 2400 },
  { cat: "Groceries", this: 2300, last: 2200 },
];

const savingsTrajectory = [
  { month: "Jan", actual: 18000, target: 50000 },
  { month: "Feb", actual: 24000, target: 50000 },
  { month: "Mar", actual: 32000, target: 50000 },
  { month: "Apr", actual: 36000 },
  { month: "May", actual: 41000 },
  { month: "Jun", actual: 46200, target: 50000 },
];

const miniMetrics = [
  { label: "Income", value: "₹1,20,000" },
  { label: "Spend", value: "₹98,400" },
  { label: "Savings", value: "18%" },
  { label: "Score", value: "742" },
  { label: "Net Worth", value: "₹12.4L" },
];

const miniGoals = [
  { name: "Goa Trip", pct: 64 },
  { name: "Emergency Fund", pct: 68 },
  { name: "New Laptop", pct: 37.5 },
];

const ChartTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
      <p className="text-foreground font-medium">{payload[0].name || payload[0].payload?.name || payload[0].payload?.cat}</p>
      <p className="text-primary">₹{Number(payload[0].value).toLocaleString("en-IN")}</p>
    </div>
  );
};

interface ChatMessage {
  role: "user" | "ai";
  text: string;
  chart?: "donut" | "bar" | "trajectory";
  chips?: string[];
}

const messages: ChatMessage[] = [
  { role: "user", text: "How much did I spend on food this month?" },
  {
    role: "ai",
    text: "You spent **₹14,800** on food this month. Here's the breakdown by source:",
    chart: "donut",
    chips: ["Compare with last month", "Show 3-month trend", "Set food budget"],
  },
  { role: "user", text: "Compare it with last month" },
  {
    role: "ai",
    text: "Food spending **increased 23%** month-over-month. Dining out saw the biggest jump (+₹1,800). Here's the comparison:",
    chart: "bar",
    chips: ["Why did dining increase?", "Forecast next month", "Show all categories"],
  },
  { role: "user", text: "Am I on track for my Goa trip savings?" },
  {
    role: "ai",
    text: "Your **Goa Trip** goal: ₹50,000 by June 2026. Current savings: ₹32,000 (64%). At your current rate, you'll reach **₹46,200** by June — **₹3,800 short**. ⚠️ Recommendation: Reduce dining by ₹2,000/month to stay on track.",
    chart: "trajectory",
    chips: ["What if I save ₹5K more?", "Adjust goal", "Show all goals"],
  },
];

const renderBold = (text: string) => {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-primary font-semibold">{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
};

const Chat = () => {
  const [input, setInput] = useState("");

  return (
    <DashboardLayout title="AI Financial Advisor" subtitle="Conversational intelligence powered by function-calling AI">
      <div className="flex gap-6 h-[calc(100vh-8rem)]">
        {/* Left context panel */}
        <div className="w-64 shrink-0 space-y-4">
          <div className="glass-card p-4">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Financial Snapshot</h4>
            <div className="space-y-2.5">
              {miniMetrics.map((m, i) => (
                <div key={i} className="flex justify-between items-center">
                  <span className="text-xs text-muted-foreground">{m.label}</span>
                  <span className="text-sm font-semibold text-primary">{m.value}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="glass-card p-4">
            <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Goals</h4>
            <div className="space-y-3">
              {miniGoals.map((g, i) => (
                <div key={i}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">{g.name}</span>
                    <span className="text-primary">{g.pct}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-surface-1 rounded-full">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${g.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Chat panel */}
        <div className="flex-1 glass-card flex flex-col">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gold-muted flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
              <Sparkles size={16} className="text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">FinSage AI</h3>
              <p className="text-xs text-success">AI Engine Active</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-lg ${
                  msg.role === "user"
                    ? "bg-surface-3 border border-primary/20 rounded-2xl rounded-br-md px-4 py-3"
                    : "bg-surface-2 border-l-2 border-primary rounded-2xl rounded-bl-md px-4 py-3"
                }`}>
                  <p className="text-sm text-foreground/90 leading-relaxed">{renderBold(msg.text)}</p>

                  {msg.chart === "donut" && (
                    <div className="mt-3">
                      <ResponsiveContainer width="100%" height={180}>
                        <PieChart>
                          <Pie data={foodBreakdown} cx="50%" cy="50%" innerRadius={40} outerRadius={70} paddingAngle={3} dataKey="value">
                            {foodBreakdown.map((_, j) => <Cell key={j} fill={GOLD_COLORS[j]} />)}
                          </Pie>
                          <Tooltip content={<ChartTooltip />} />
                        </PieChart>
                      </ResponsiveContainer>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {foodBreakdown.map((f, j) => (
                          <span key={j} className="text-[10px] text-muted-foreground flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full" style={{ background: GOLD_COLORS[j] }} />
                            {f.name} ₹{f.value.toLocaleString("en-IN")}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {msg.chart === "bar" && (
                    <div className="mt-3">
                      <ResponsiveContainer width="100%" height={160}>
                        <BarChart data={comparisonData}>
                          <XAxis dataKey="cat" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
                          <Tooltip content={<ChartTooltip />} />
                          <Bar dataKey="this" fill="#D4AF37" radius={[4, 4, 0, 0]} name="This Month" />
                          <Bar dataKey="last" fill="#333" radius={[4, 4, 0, 0]} name="Last Month" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {msg.chart === "trajectory" && (
                    <div className="mt-3">
                      {/* Gauge */}
                      <div className="flex justify-center mb-3">
                        <div className="relative w-24 h-12 overflow-hidden">
                          <svg viewBox="0 0 100 50" className="w-full h-full">
                            <path d="M 5 50 A 45 45 0 0 1 95 50" fill="none" stroke="#222" strokeWidth="8" strokeLinecap="round" />
                            <path d="M 5 50 A 45 45 0 0 1 95 50" fill="none" stroke="#D4AF37" strokeWidth="8" strokeLinecap="round" strokeDasharray={`${64 * 1.41} 141`} />
                          </svg>
                          <span className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs font-bold text-primary">64%</span>
                        </div>
                      </div>
                      <ResponsiveContainer width="100%" height={120}>
                        <LineChart data={savingsTrajectory}>
                          <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
                          <Line type="monotone" dataKey="actual" stroke="#D4AF37" strokeWidth={2} dot={false} />
                          <Line type="monotone" dataKey="target" stroke="#D4AF37" strokeWidth={1} strokeDasharray="5 5" dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {msg.chips && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {msg.chips.map((chip, j) => (
                        <button key={j} className="text-xs px-3 py-1 rounded-full border border-primary/30 text-primary hover:bg-primary/10 transition-colors">
                          {chip}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Input */}
          <div className="px-6 py-4 border-t border-gold-muted">
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask FinSage anything about your finances..."
                className="flex-1 bg-surface-3 border border-gold-muted rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
              />
              <button className="p-3 bg-primary text-primary-foreground rounded-xl hover:brightness-110 transition-all">
                <Send size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Chat;
