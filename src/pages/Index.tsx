import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { MessageSquare, TrendingUp, Bell, IndianRupee, ArrowRight, Sparkles } from "lucide-react";
import FinSageLogo from "@/components/FinSageLogo";

const features = [
  {
    icon: MessageSquare,
    title: "AI Chat Intelligence",
    desc: "Ask anything about your finances. Get computed answers, not guesses.",
  },
  {
    icon: TrendingUp,
    title: "Predictive Forecasting",
    desc: "Prophet-powered spending forecasts with confidence intervals.",
  },
  {
    icon: Bell,
    title: "Proactive Alerts",
    desc: "Anomaly detection warns you before problems arise.",
  },
  {
    icon: IndianRupee,
    title: "India-Specific Intelligence",
    desc: "Section 80C optimization, UPI analytics, EPF projections.",
  },
];

const steps = [
  { num: "01", title: "Ask a Question", desc: "Type any financial question in plain English" },
  { num: "02", title: "AI Analyzes Your Data", desc: "FinSage processes transactions, goals & patterns" },
  { num: "03", title: "Get Insights + Visualizations", desc: "Receive precise answers with interactive charts" },
];

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 max-w-7xl mx-auto">
        <FinSageLogo size="md" />
        <button
          onClick={() => navigate("/dashboard")}
          className="px-5 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-semibold hover:brightness-110 transition-all"
        >
          Launch Dashboard
        </button>
      </nav>

      {/* Hero */}
      <section className="max-w-7xl mx-auto px-8 pt-20 pb-32 text-center relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] pointer-events-none" />
        
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="relative z-10"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-gold-muted bg-surface-2 mb-8">
            <Sparkles size={14} className="text-primary" />
            <span className="text-xs font-medium text-muted-foreground">AI-Powered Personal Finance</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold leading-tight mb-6 text-balance">
            <span className="text-foreground">Where AI meets</span>
            <br />
            <span className="gold-gradient-text">Personal Finance</span>
          </h1>

          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10 text-balance leading-relaxed">
            FinSage is your AI-powered personal CFO. Ask questions in plain English. Get precise, data-backed answers with intelligent visualizations — not generic advice.
          </p>

          <div className="flex items-center justify-center gap-4">
            <button
              onClick={() => navigate("/dashboard")}
              className="px-8 py-3.5 bg-primary text-primary-foreground rounded-xl text-sm font-bold hover:brightness-110 transition-all gold-glow-sm flex items-center gap-2"
            >
              Launch Dashboard <ArrowRight size={16} />
            </button>
            <button
              onClick={() => document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth" })}
              className="px-8 py-3.5 border border-primary/40 text-primary rounded-xl text-sm font-bold hover:bg-primary/10 transition-all"
            >
              See How It Works
            </button>
          </div>
        </motion.div>

        {/* Dashboard mockup */}
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.3 }}
          className="relative mt-20 max-w-4xl mx-auto"
        >
          <div className="glass-card p-6 gold-glow animate-float">
            <div className="grid grid-cols-5 gap-3 mb-4">
              {["₹1,20,000", "₹98,400", "18%", "742", "₹12,40,000"].map((v, i) => (
                <div key={i} className="bg-surface-3 rounded-lg p-3 text-center">
                  <p className="text-[10px] text-muted-foreground uppercase">
                    {["Income", "Spending", "Savings", "Score", "Net Worth"][i]}
                  </p>
                  <p className="text-sm font-bold text-primary mt-1">{v}</p>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="col-span-2 bg-surface-3 rounded-lg h-32 flex items-center justify-center">
                <div className="flex items-end gap-1.5 h-16">
                  {[40, 60, 45, 70, 55, 80].map((h, i) => (
                    <div key={i} className="w-8 rounded-t bg-gradient-to-t from-gold-dark to-primary" style={{ height: `${h}%` }} />
                  ))}
                </div>
              </div>
              <div className="bg-surface-3 rounded-lg h-32 flex items-center justify-center">
                <div className="w-16 h-16 rounded-full border-4 border-primary border-t-transparent animate-spin" style={{ animationDuration: "3s" }} />
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-8 py-24">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl font-bold text-foreground mb-3">Intelligent by Design</h2>
          <p className="text-muted-foreground">Four pillars of financial intelligence</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map((f, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="glass-card-hover p-6"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                <f.icon size={22} className="text-primary" />
              </div>
              <h3 className="text-base font-semibold text-foreground mb-2">{f.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="max-w-7xl mx-auto px-8 py-24">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl font-bold text-foreground mb-3">How It Works</h2>
          <p className="text-muted-foreground">Three steps to financial clarity</p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {steps.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.15 }}
              className="text-center"
            >
              <div className="w-16 h-16 rounded-full border-2 border-primary bg-primary/10 flex items-center justify-center mx-auto mb-5">
                <span className="text-xl font-bold text-primary">{s.num}</span>
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">{s.title}</h3>
              <p className="text-sm text-muted-foreground">{s.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gold-muted py-10 mt-10">
        <div className="max-w-7xl mx-auto px-8 flex items-center justify-between">
          <FinSageLogo size="sm" />
          <p className="text-xs text-muted-foreground">Built for Indian professionals</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
