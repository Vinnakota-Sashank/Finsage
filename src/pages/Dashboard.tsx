import DashboardLayout from "@/components/DashboardLayout";
import MetricCard from "@/components/MetricCard";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const spendingData = [
  { month: "Apr", amount: 92000 },
  { month: "May", amount: 88000 },
  { month: "Jun", amount: 105000 },
  { month: "Jul", amount: 95000 },
  { month: "Aug", amount: 110000 },
  { month: "Sep", amount: 98400 },
];

const categoryData = [
  { name: "Rent", value: 22000 },
  { name: "Food", value: 14800 },
  { name: "EMI", value: 8500 },
  { name: "Shopping", value: 7000 },
  { name: "SIP", value: 15000 },
  { name: "Transport", value: 4500 },
  { name: "Utilities", value: 3200 },
  { name: "Others", value: 23400 },
];

const GOLD_COLORS = ["#D4AF37", "#FFD700", "#B8860B", "#DAA520", "#C5A028", "#8B7536", "#A0892C", "#997A1E"];

const goals = [
  { name: "Goa Trip", current: 32000, target: 50000, date: "Jun 2026", pct: 64 },
  { name: "Emergency Fund", current: 245000, target: 360000, date: "Dec 2026", pct: 68 },
  { name: "New Laptop", current: 45000, target: 120000, date: "Aug 2026", pct: 37.5 },
];

const alerts = [
  { text: "Shopping spike 3.1× average", color: "bg-error" },
  { text: "Credit utilization 68%", color: "bg-warning" },
  { text: "SIP debit tomorrow", color: "bg-success" },
];

const formatCurrency = (v: number) => `₹${(v / 1000).toFixed(0)}K`;

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
      <p className="text-muted-foreground">{label}</p>
      <p className="text-primary font-semibold">₹{payload[0].value.toLocaleString("en-IN")}</p>
    </div>
  );
};

const Dashboard = () => {
  return (
    <DashboardLayout>
      {/* Metrics */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <MetricCard label="Monthly Income" value="₹1,20,000" change="+₹5,200" positive />
        <MetricCard label="Total Spending" value="₹98,400" change="-2.3%" positive={false} />
        <MetricCard label="Savings Rate" value="18%" change="+1.2%" positive />
        <MetricCard label="Credit Score" value="742" change="+12 pts" positive />
        <MetricCard label="Net Worth" value="₹12,40,000" change="+₹38,000" positive />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-5 gap-6">
        {/* Left column */}
        <div className="col-span-3 space-y-6">
          {/* Spending Trend */}
          <div className="glass-card p-6">
            <h3 className="text-base font-semibold text-foreground mb-4">Spending Trend</h3>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={spendingData}>
                <defs>
                  <linearGradient id="goldGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#D4AF37" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#D4AF37" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 12 }} tickFormatter={formatCurrency} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="amount" stroke="#D4AF37" strokeWidth={2} fill="url(#goldGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Category Breakdown */}
          <div className="glass-card p-6">
            <h3 className="text-base font-semibold text-foreground mb-4">Category Breakdown</h3>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={categoryData} cx="50%" cy="45%" innerRadius={60} outerRadius={100} paddingAngle={2} dataKey="value">
                  {categoryData.map((_, i) => (
                    <Cell key={i} fill={GOLD_COLORS[i]} />
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
          </div>
        </div>

        {/* Right column */}
        <div className="col-span-2 space-y-6">
          {/* Goals */}
          <div className="glass-card p-6">
            <h3 className="text-base font-semibold text-foreground mb-4">Active Goals</h3>
            <div className="space-y-4">
              {goals.map((g, i) => (
                <div key={i} className="bg-surface-3 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-foreground">{g.name}</span>
                    <span className="text-xs text-muted-foreground">by {g.date}</span>
                  </div>
                  <div className="w-full h-2 bg-surface-1 rounded-full mb-2">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-500"
                      style={{ width: `${g.pct}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">
                      ₹{g.current.toLocaleString("en-IN")} / ₹{g.target.toLocaleString("en-IN")}
                    </span>
                    <span className="text-primary font-medium">{g.pct}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Alerts */}
          <div className="glass-card p-6">
            <h3 className="text-base font-semibold text-foreground mb-4">Recent Alerts</h3>
            <div className="space-y-3">
              {alerts.map((a, i) => (
                <div key={i} className="flex items-center gap-3 bg-surface-3 rounded-lg p-3">
                  <div className={`w-2 h-2 rounded-full ${a.color} shrink-0`} />
                  <span className="text-sm text-muted-foreground">{a.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
