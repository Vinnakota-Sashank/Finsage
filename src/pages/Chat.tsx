import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import DashboardLayout from "@/components/DashboardLayout";
import { apiUrl } from "@/lib/api";
import { Send, Sparkles } from "lucide-react";
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, LineChart, Line,
} from "recharts";

const CONVERSATION_STORAGE_KEY = "finsage-chat-conversation-id";
const GOLD_COLORS = ["#D4AF37", "#FFD700", "#B8860B", "#DAA520", "#C5A028", "#8B7536"];

type ChartType = "donut" | "bar" | "trajectory" | "line";

interface DashboardSummary {
  monthly_income: number;
  total_spending: number;
  savings_rate: number;
  credit_score: number;
  net_worth: number;
}

interface GoalsResponse {
  goals: {
    id: number;
    name: string;
    pct: number;
  }[];
}

interface ChatHealthResponse {
  ready: boolean;
  gemini_configured: boolean;
  mode: string;
}

interface ApiChatMessagePayload {
  role: "user" | "assistant";
  content: string;
  chart_type?: ChartType | null;
  chart_data?: unknown;
  suggestions?: string[];
}

interface ChatMessageResponse {
  conversation_id: number;
  assistant: ApiChatMessagePayload;
}

interface ConversationMessagesResponse {
  conversation_id: number;
  messages: ApiChatMessagePayload[];
}

interface ChatMessage {
  role: "user" | "ai";
  text: string;
  chartType?: ChartType;
  chartData?: unknown;
  chips?: string[];
}

const defaultAssistantMessage: ChatMessage = {
  role: "ai",
  text: "Ask me about your spending, compare this month vs last month, or check if your Goa goal is on track.",
  chips: [
    "How much did I spend on food this month?",
    "Compare food with last month",
    "Am I on track for Goa trip?",
  ],
};

const fetchApi = async <T,>(path: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(apiUrl(path), init);
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

const mapApiMessageToUi = (message: ApiChatMessagePayload): ChatMessage => ({
  role: message.role === "assistant" ? "ai" : "user",
  text: message.content,
  chartType: message.chart_type ?? undefined,
  chartData: message.chart_data,
  chips: message.suggestions ?? [],
});

const formatCurrency = (value: number) => `₹${Math.round(value).toLocaleString("en-IN")}`;

const ChartTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface-3 border border-gold-muted rounded-lg px-3 py-2 text-xs">
      <p className="text-foreground font-medium">{payload[0].name || payload[0].payload?.name || payload[0].payload?.cat}</p>
      <p className="text-primary">₹{Number(payload[0].value).toLocaleString("en-IN")}</p>
    </div>
  );
};

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
  const [messages, setMessages] = useState<ChatMessage[]>([defaultAssistantMessage]);
  const [conversationId, setConversationId] = useState<number | null>(() => {
    if (typeof window === "undefined") return null;
    const raw = window.localStorage.getItem(CONVERSATION_STORAGE_KEY);
    const parsed = raw ? Number(raw) : NaN;
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
  });

  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const { data: summary } = useQuery({
    queryKey: ["chat", "summary"],
    queryFn: () => fetchApi<DashboardSummary>("/api/v1/dashboard/summary"),
    staleTime: 60_000,
  });

  const { data: goalsData } = useQuery({
    queryKey: ["chat", "goals"],
    queryFn: () => fetchApi<GoalsResponse>("/api/v1/dashboard/goals"),
    staleTime: 60_000,
  });

  const { data: chatHealth } = useQuery({
    queryKey: ["chat", "health"],
    queryFn: () => fetchApi<ChatHealthResponse>("/api/v1/chat/health"),
    staleTime: 60_000,
  });

  const miniMetrics = useMemo(
    () => [
      { label: "Income", value: summary ? formatCurrency(summary.monthly_income) : "--" },
      { label: "Spend", value: summary ? formatCurrency(summary.total_spending) : "--" },
      { label: "Savings", value: summary ? `${summary.savings_rate.toFixed(1)}%` : "--" },
      { label: "Score", value: summary ? summary.credit_score.toString() : "--" },
      { label: "Net Worth", value: summary ? formatCurrency(summary.net_worth) : "--" },
    ],
    [summary],
  );

  const miniGoals = useMemo(
    () => (goalsData?.goals ?? []).slice(0, 3),
    [goalsData],
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  useEffect(() => {
    if (!conversationId) {
      setMessages([defaultAssistantMessage]);
      return;
    }

    let disposed = false;

    const loadHistory = async () => {
      setIsHistoryLoading(true);
      setError(null);
      try {
        const data = await fetchApi<ConversationMessagesResponse>(
          `/api/v1/chat/conversations/${conversationId}/messages`,
        );
        if (disposed) return;

        if (data.messages.length > 0) {
          setMessages(data.messages.map(mapApiMessageToUi));
        } else {
          setMessages([defaultAssistantMessage]);
        }
      } catch {
        if (disposed) return;

        setConversationId(null);
        window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
        setMessages([defaultAssistantMessage]);
      } finally {
        if (!disposed) {
          setIsHistoryLoading(false);
        }
      }
    };

    void loadHistory();

    return () => {
      disposed = true;
    };
  }, [conversationId]);

  const sendMessage = async (rawText: string) => {
    const text = rawText.trim();
    if (!text || isSending) return;

    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", text }]);
    setIsSending(true);

    try {
      const response = await fetchApi<ChatMessageResponse>("/api/v1/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
        }),
      });

      if (conversationId !== response.conversation_id) {
        setConversationId(response.conversation_id);
        window.localStorage.setItem(CONVERSATION_STORAGE_KEY, String(response.conversation_id));
      }

      setMessages((prev) => [...prev, mapApiMessageToUi(response.assistant)]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown chat error";
      setError(`Chat request failed: ${message}`);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: "I hit an error while processing that query. Please try again in a moment.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleNewChat = () => {
    setConversationId(null);
    window.localStorage.removeItem(CONVERSATION_STORAGE_KEY);
    setMessages([defaultAssistantMessage]);
    setError(null);
  };

  const renderChart = (message: ChatMessage) => {
    if (!message.chartType || !message.chartData) return null;

    if (message.chartType === "donut") {
      const donutData = Array.isArray(message.chartData) ? message.chartData : [];
      if (donutData.length === 0) return null;

      return (
        <div className="mt-3">
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={donutData} cx="50%" cy="50%" innerRadius={40} outerRadius={70} paddingAngle={3} dataKey="value">
                {donutData.map((_, index) => <Cell key={index} fill={GOLD_COLORS[index % GOLD_COLORS.length]} />)}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-2 mt-1">
            {donutData.map((item, index) => (
              <span key={index} className="text-[10px] text-muted-foreground flex items-center gap-1">
                <span className="w-2 h-2 rounded-full" style={{ background: GOLD_COLORS[index % GOLD_COLORS.length] }} />
                {String(item?.name)} {formatCurrency(Number(item?.value ?? 0))}
              </span>
            ))}
          </div>
        </div>
      );
    }

    if (message.chartType === "bar") {
      const barData = Array.isArray(message.chartData) ? message.chartData : [];
      if (barData.length === 0) return null;

      return (
        <div className="mt-3">
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={barData}>
              <XAxis dataKey="cat" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <Tooltip content={<ChartTooltip />} />
              <Bar dataKey="this" fill="#D4AF37" radius={[4, 4, 0, 0]} name="This Month" />
              <Bar dataKey="last" fill="#333" radius={[4, 4, 0, 0]} name="Last Month" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (message.chartType === "trajectory") {
      const trajectoryData = Array.isArray(message.chartData) ? message.chartData : [];
      if (trajectoryData.length === 0) return null;

      const lastPoint = trajectoryData[trajectoryData.length - 1];
      const goalPct = Number(lastPoint?.target)
        ? Math.max(0, Math.min(100, (Number(lastPoint?.actual) / Number(lastPoint?.target)) * 100))
        : 0;

      return (
        <div className="mt-3">
          <div className="flex justify-center mb-3">
            <div className="relative w-24 h-12 overflow-hidden">
              <svg viewBox="0 0 100 50" className="w-full h-full">
                <path d="M 5 50 A 45 45 0 0 1 95 50" fill="none" stroke="#222" strokeWidth="8" strokeLinecap="round" />
                <path
                  d="M 5 50 A 45 45 0 0 1 95 50"
                  fill="none"
                  stroke="#D4AF37"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${goalPct * 1.41} 141`}
                />
              </svg>
              <span className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs font-bold text-primary">
                {goalPct.toFixed(0)}%
              </span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={trajectoryData}>
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <Line type="monotone" dataKey="actual" stroke="#D4AF37" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="target" stroke="#D4AF37" strokeWidth={1} strokeDasharray="5 5" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      );
    }

    if (message.chartType === "line") {
      const lineData = Array.isArray(message.chartData) ? message.chartData : [];
      if (lineData.length === 0) return null;

      return (
        <div className="mt-3">
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={lineData}>
              <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: "#666", fontSize: 10 }} />
              <Tooltip content={<ChartTooltip />} />
              <Line type="monotone" dataKey="amount" stroke="#D4AF37" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      );
    }

    return null;
  };

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
              {miniGoals.length === 0 && (
                <p className="text-xs text-muted-foreground">No active goals loaded</p>
              )}
              {miniGoals.map((g) => (
                <div key={g.id}>
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
          <div className="px-6 py-4 border-b border-gold-muted flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                <Sparkles size={16} className="text-primary" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-foreground">FinSage AI</h3>
                <p className="text-xs text-success">
                  {chatHealth?.mode === "gemini" ? "Gemini + transaction tools" : "Transaction tools mode"}
                </p>
              </div>
            </div>
            <button
              onClick={handleNewChat}
              className="text-xs px-3 py-1.5 rounded-md border border-gold-muted text-muted-foreground hover:text-foreground hover:border-primary transition-colors"
            >
              New Chat
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-5">
            {error && (
              <div className="bg-error/10 border border-error/30 rounded-lg px-3 py-2 text-xs text-error">
                {error}
              </div>
            )}

            {isHistoryLoading && (
              <p className="text-xs text-muted-foreground">Loading conversation history...</p>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-lg ${
                  msg.role === "user"
                    ? "bg-surface-3 border border-primary/20 rounded-2xl rounded-br-md px-4 py-3"
                    : "bg-surface-2 border-l-2 border-primary rounded-2xl rounded-bl-md px-4 py-3"
                }`}>
                  <p className="text-sm text-foreground/90 leading-relaxed">{renderBold(msg.text)}</p>

                  {renderChart(msg)}

                  {msg.chips && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {msg.chips.map((chip, j) => (
                        <button
                          key={j}
                          onClick={() => sendMessage(chip)}
                          className="text-xs px-3 py-1 rounded-full border border-primary/30 text-primary hover:bg-primary/10 transition-colors"
                        >
                          {chip}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isSending && (
              <div className="flex justify-start">
                <div className="bg-surface-2 border-l-2 border-primary rounded-2xl rounded-bl-md px-4 py-3">
                  <p className="text-sm text-muted-foreground">FinSage is thinking...</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="px-6 py-4 border-t border-gold-muted">
            <div className="flex items-center gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void sendMessage(input);
                  }
                }}
                placeholder="Ask FinSage anything about your finances..."
                className="flex-1 bg-surface-3 border border-gold-muted rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
              />
              <button
                onClick={() => void sendMessage(input)}
                disabled={isSending || !input.trim()}
                className="p-3 bg-primary text-primary-foreground rounded-xl hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
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
