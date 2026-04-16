# FinSage — Prototype Design Specification

---

## SECTION 1 — Prototype Concept Summary

**FinSage** is an AI-powered personal finance intelligence system — a conversational "Personal CFO" for Indian professionals. The prototype demonstrates a modern SaaS AI platform where users interact via natural language chat and receive **computed, data-backed financial insights** — not generic advice. The system showcases:

- **Agentic AI function calling** — the AI executes structured queries against real financial data (spending breakdowns, comparisons, goal tracking)
- **Auto-generated visualizations** — every response is paired with the optimal chart type (donut, bar, line, gauge, treemap)
- **Predictive forecasting** — Prophet-based spending predictions with confidence intervals
- **Monte Carlo scenario simulation** — "What if I increase my SIP?" with 1,000-run probability distributions
- **Proactive anomaly alerts** — spending spikes, credit health warnings, goal risk notifications
- **India-specific intelligence** — Section 80C tax optimization, UPI categorization, EPF projections, festival budgets

The prototype uses **hardcoded realistic sample data** for a synthetic user profile ("Arjun Mehta", 28yo Software Engineer, Hyderabad, ₹1.2L/month income) to simulate the full product experience without a backend.

---

## SECTION 2 — User Flow

1. **Landing Page** — User lands on a premium dark product page that introduces FinSage. CTAs: "Launch Dashboard" or "Try Demo."
2. **Dashboard Overview** — After entering, the user sees a financial command center: summary metrics cards (Income, Spending, Savings Rate, Credit Score, Net Worth), spending trend chart, category breakdown, and active goal progress.
3. **AI Chat Interface** — A chat panel (right side or expandable) lets the user type natural language questions. The AI responds with text + auto-generated charts inline. Suggestion chips appear below each response.
4. **Insights & Forecasting** — The user asks predictive questions ("What will I spend next month?") and gets line charts with confidence bands. Goal projections show probability gauges.
5. **Scenario Simulator** — The user asks "What if?" questions and sees Monte Carlo simulation results: probability histograms, before/after comparisons, trade-off analysis.
6. **Alert Center** — A notification panel shows proactive alerts: spending spikes (red), budget warnings (yellow), upcoming payments (green), credit health alerts. Each alert has severity, explanation, and recommended action.
7. **Tax & India Intelligence** — Section 80C usage breakdown, remaining investment capacity, EPF projection charts, festival budget forecasts.

---

## SECTION 3 — Screens to Generate

### Screen 1: Landing Page
- Hero section: "Talk to your money. It finally talks back."
- Product tagline, feature highlights (3-4 cards: AI Chat, Forecasting, Alerts, Tax Intelligence)
- Simulated product screenshot/mockup
- CTA buttons: "Launch Dashboard", "See How It Works"
- Trusted-by logos / blockchain network badges placeholder
- Black and gold premium theme

### Screen 2: Main Dashboard (Financial Command Center)
- **Top bar:** FinSage logo, user avatar, notification bell with badge count
- **Summary metric cards row:** Monthly Income (₹1,20,000) | Total Spend (₹98,400) | Savings Rate (18%) | Credit Score (742, with up/down indicator) | Net Worth (₹12,40,000)
- **Spending Trend chart:** Area/line chart showing 6-month spending trajectory
- **Category Breakdown:** Donut/treemap showing top spending categories (Rent, Food, Transport, Shopping, EMIs, SIPs, etc.)
- **Active Goals panel:** 3 goal cards with progress bars (Goa Trip 64%, Emergency Fund 68%, New Laptop 37.5%) with projected completion dates
- **Recent Alerts ticker:** 2-3 latest alerts in a slim banner

### Screen 3: AI Chat Interface (primary interaction screen)
- **Left panel:** Dashboard summary (compact) or navigation
- **Center/Right panel:** Chat interface
  - Message bubbles: user messages (right, subtle gold accent) and AI responses (left, dark card)
  - AI responses contain: text explanation + inline chart (donut, bar, line, gauge depending on query) + data table snippet
  - Suggestion chips below AI responses: "Compare with last month", "Show trend", "Set a budget"
  - Typing indicator animation
- **Sample conversation pre-loaded:**
  - User: "How much did I spend on food this month?"
  - AI: "You spent ₹14,800 on food this month." + Donut chart (Swiggy ₹5,200, Zomato ₹3,100, Dining ₹4,200, Groceries ₹2,300)
  - User: "Compare it with last month"
  - AI: "Food spending increased 23% month-over-month. Dining out was the biggest increase (+₹1,800)." + Grouped bar chart

### Screen 4: Forecasting & Predictions
- **Spending Forecast:** Line chart with shaded confidence band (80% interval) projecting next 3 months
- **Goal Probability Panel:** Gauge charts for each goal showing completion probability (Goa Trip: 62%, Emergency Fund: 78%)
- **Loan Payoff Timeline:** Horizontal bar/timeline showing student loan payoff trajectory
- **Net Worth Projection:** Stacked area chart showing projected assets vs liabilities over 12 months
- **Key Insight Cards:** "At current rate, you'll reach Emergency Fund target by Nov 2026" / "Net worth projected to cross ₹15L by Q1 2027"

### Screen 5: Scenario Simulator ("What-If" Engine)
- **Input panel:** Scenario selector or natural language input: "What if I increase my SIP to ₹25,000?"
- **Results panel:**
  - Probability distribution histogram (1,000 simulations) showing expected corpus range
  - Key stats: Median outcome ₹22.4L, P10 ₹18.1L, P90 ₹28.7L
  - Before vs After comparison cards: Current SIP ₹15K → proposed ₹25K, impact on savings rate, goal timelines
  - Trade-off analysis: "Discretionary budget drops from ₹28K to ₹23K"
- **Secondary scenario example:** "What if I take a ₹5L car loan?" with EMI impact, savings rate change, goal delays

### Screen 6: Alert Center (Proactive Intelligence)
- **Alert list with severity icons:**
  - 🔴 Critical: "Unusual spending spike: ₹12,400 on Shopping this week — 3.1× your weekly average"
  - 🟡 Warning: "Credit card utilization at 68% — pay ₹15,000 before cycle date to avoid score impact"
  - 🟡 Warning: "Dining budget 92% used — 11 days left in month"
  - 🟢 Info: "SIP auto-debit of ₹15,000 scheduled tomorrow — ensure sufficient balance"
  - 🔵 Insight: "Netflix subscription (₹649) wasn't charged this month — cancelled?"
- Each alert has: severity badge, timestamp, description, recommended action button
- Filter tabs: All | Critical | Warnings | Insights
- Alert trend mini-chart: alerts per week over last month

### Screen 7: Tax & India Intelligence
- **Section 80C Optimizer:** Stacked horizontal bar showing usage (EPF ₹86,400 + ELSS ₹18,000 + PPF ₹24,000 = ₹1,28,400 / ₹1,50,000). Remaining ₹21,600 highlighted with CTA: "Invest in ELSS before March 31 to save ₹6,480 in tax"
- **Section 80D panel:** ₹0 / ₹25,000 used. Recommendation card for health insurance
- **EPF Projection:** Line chart projecting EPF corpus to retirement (₹1.2 Cr at 60 @ 8.15%)
- **Festival Budget Predictor:** Card showing "Based on last Diwali: expect ₹28,000 in shopping. Start saving ₹7K/month from August."
- **UPI Analytics:** Breakdown of UPI merchant transactions (Swiggy, Uber, Amazon, Flipkart) with category auto-tagging

---

## SECTION 4 — Final Prompt

---


---

Build a modern, premium SaaS AI financial intelligence platform called **FinSage** with the tagline "Talk to your money. It finally talks back." This is a personal finance AI advisor for Indian professionals. The entire app uses a **dark theme with black/very dark backgrounds (#0A0A0A, #111111, #1A1A1A) and rich gold accents (#D4AF37, #FFD700, #B8860B)** — similar to a luxury fintech product. Use gold for highlights, CTAs, active states, chart accents, and key metrics. Text is white and light gray. Cards use dark glass-morphism (rgba backgrounds with subtle borders). No bright colors except gold tones and occasional red/green for alerts.

Use **React, JavaScript, Tailwind CSS, shadcn/ui, Recharts** for charts. Use **Lucide icons**. All data is hardcoded/simulated — no backend needed.

---

### PAGE 1: LANDING PAGE (route: `/`)

A premium, cinematic landing page with a black background and gold accents.

**Hero Section:**
- Large headline: "Where AI meets Personal Finance" in white/gold gradient text
- Subheadline: "FinSage is your AI-powered personal CFO. Ask questions in plain English. Get precise, data-backed answers with intelligent visualizations — not generic advice."
- Two CTA buttons: "Launch Dashboard" (gold filled, navigates to `/dashboard`) and "See How It Works" (gold outline)
- Below the hero: a floating mockup/screenshot of the dashboard with a subtle gold glow/shadow effect

**Features Section:**
- 4 feature cards in a row on dark glass-morph backgrounds with gold icon accents:
  1. **AI Chat Intelligence** — "Ask anything about your finances. Get computed answers, not guesses." (icon: MessageSquare)
  2. **Predictive Forecasting** — "Prophet-powered spending forecasts with confidence intervals." (icon: TrendingUp)
  3. **Proactive Alerts** — "Anomaly detection warns you before problems arise." (icon: Bell)
  4. **India-Specific Intelligence** — "Section 80C optimization, UPI analytics, EPF projections." (icon: IndianRupee)

**How It Works Section:**
- 3-step horizontal process: "Ask a Question" → "AI Analyzes Your Data" → "Get Insights + Visualizations"
- Each step has a gold numbered circle and brief description

**Footer:** Minimal dark footer with FinSage logo and "Built for Indian professionals" tagline.

---

### PAGE 2: MAIN DASHBOARD (route: `/dashboard`)

This is the financial command center. Dark background, sidebar navigation on the left, main content area.

**Left Sidebar (dark, narrow):**
- FinSage logo (gold) at top
- Navigation items with Lucide icons: Dashboard (LayoutDashboard), AI Chat (MessageSquare), Forecasting (TrendingUp), Simulator (FlaskConical), Alerts (Bell), Tax Intelligence (Receipt)
- Active item has a gold accent bar on the left and gold text
- User avatar and name "Arjun Mehta" at the bottom

**Top Bar:**
- Welcome text: "Good evening, Arjun" (left)
- Notification bell icon with red badge showing "3" (right)
- Small user avatar (right)

**Summary Metrics Row (5 cards):**
- Each card is a dark glass-morph rectangle with:
  - Small label in gray ("Monthly Income", "Total Spending", "Savings Rate", "Credit Score", "Net Worth")
  - Large gold value ("₹1,20,000", "₹98,400", "18%", "742", "₹12,40,000")
  - Small green/red change indicator ("+₹5,200", "-2.3%", "+12 pts", etc.)

**Main Content Grid (2 columns below metrics):**

**Left column (wider, ~60%):**
- **Spending Trend Chart:** A Recharts AreaChart with gold gradient fill showing monthly spending over 6 months (Apr–Sep 2025). Values fluctuate between ₹85K–₹1.1L. X-axis: month names. Y-axis: amount in ₹. Gold line with semi-transparent gold fill below.
- **Category Breakdown:** A Recharts PieChart / donut chart showing spending categories. Use varying gold/amber/bronze/dark-gold shades for segments. Categories: Rent (₹22,000), Food (₹14,800), EMI (₹8,500), Shopping (₹7,000), SIP (₹15,000), Transport (₹4,500), Utilities (₹3,200), Others (₹23,400). Show legend below chart.

**Right column (~40%):**
- **Active Goals Panel:** 3 goal cards stacked vertically. Each card has:
  - Goal name and target date
  - Progress bar (gold fill on dark track)
  - Current amount / Target amount
  - Projected completion status
  - Goals: "Goa Trip" (₹32,000/₹50,000 by Jun 2026, 64%, on gold progress bar), "Emergency Fund" (₹2,45,000/₹3,60,000 by Dec 2026, 68%), "New Laptop" (₹45,000/₹1,20,000 by Aug 2026, 37.5%)
- **Recent Alerts:** 3 compact alert items with colored severity dots (red/yellow/green) and brief text. "Shopping spike 3.1× average" (red), "Credit utilization 68%" (yellow), "SIP debit tomorrow" (green).

---

### PAGE 3: AI CHAT INTERFACE (route: `/chat`)

A full-screen chat interface — the core product experience. Same sidebar on left.

**Main area split:**

**Left compact panel (25% width):**
- A condensed version of the dashboard: 5 small metric tiles (Income, Spend, Savings, Score, Net Worth) in a vertical stack
- Mini goals progress list
- This provides financial context while chatting

**Right chat panel (75% width):**
- Chat header: "FinSage AI" with a gold sparkle icon and status "Online"
- Message area with pre-loaded sample conversation:

  **Message 1 (User, right-aligned, subtle dark bubble with gold-tinted border):**
  "How much did I spend on food this month?"

  **Message 2 (AI, left-aligned, darker bubble with gold accent line on left):**
  Text: "You spent **₹14,800** on food this month. Here's the breakdown by source:"
  Below text: An inline Recharts **DonutChart** inside the message bubble showing: Swiggy ₹5,200 (35%), Zomato ₹3,100 (21%), Dining Out ₹4,200 (28%), Groceries ₹2,300 (16%). Use gold/amber/bronze shades.
  Below chart: 3 suggestion chips (small pill buttons with gold borders): "Compare with last month" | "Show 3-month trend" | "Set food budget"

  **Message 3 (User):**
  "Compare it with last month"

  **Message 4 (AI):**
  Text: "Food spending **increased 23%** month-over-month. Dining out saw the biggest jump (+₹1,800). Here's the comparison:"
  Below text: An inline Recharts **BarChart** (grouped bars) comparing This Month vs Last Month for each subcategory (Swiggy, Zomato, Dining, Groceries). Gold bars for current month, dim gray bars for last month.
  Below chart: Suggestion chips: "Why did dining increase?" | "Forecast next month" | "Show all categories"

  **Message 5 (User):**
  "Am I on track for my Goa trip savings?"

  **Message 6 (AI):**
  Text: "Your **Goa Trip** goal: ₹50,000 by June 2026. Current savings: ₹32,000 (64%). At your current rate, you'll reach **₹46,200** by June — **₹3,800 short**. ⚠️ Recommendation: Reduce dining by ₹2,000/month to stay on track."
  Below text: A **progress gauge** (semi-circle) at 64% in gold, plus a small **LineChart** showing savings trajectory with a dashed gold target line at ₹50K and a solid gold projection line falling short.
  Suggestion chips: "What if I save ₹5K more?" | "Adjust goal" | "Show all goals"

- **Chat input bar** at bottom: Dark input field with gold border on focus, placeholder "Ask FinSage anything about your finances...", gold send button with arrow icon.

---

### PAGE 4: FORECASTING & PREDICTIONS (route: `/forecasting`)

**Spending Forecast Section (full width):**
- Title: "Spending Forecast — Next 3 Months"
- A Recharts **AreaChart** showing 6 months of historical spending (solid gold line) and 3 months of forecasted spending (dashed gold line) with a semi-transparent gold shaded confidence band (80% interval). Historical data: solid fill. Forecast: lighter fill with dashed borders.
- Below chart: Insight card: "Predicted total spend next month: **₹1,02,400** (range: ₹94,000 – ₹1,11,000)"

**Two-column grid below:**

**Left: Goal Probability Panel**
- 3 cards, each showing:
  - Goal name
  - A circular progress/gauge component showing probability
  - Goa Trip: 62% probability (gold ring on dark), Emergency Fund: 78%, New Laptop: 34%
  - Under each: "At current savings rate" text

**Right: Net Worth Projection**
- Recharts **StackedAreaChart** showing Assets (gold) vs Liabilities (dark gray/bronze) over next 12 months
- Net worth line (bright gold) rising over time
- Key stat card below: "Projected net worth in 12 months: **₹15,80,000** (+₹3,40,000 from today)"

**Bottom row: AI Insight Cards (3 cards):**
- "At current trajectory, Emergency Fund target reached by **Nov 2026**" (with TrendingUp icon in gold)
- "Student loan projected payoff: **March 2029** — 2 months ahead of schedule" (with CheckCircle icon)
- "Mutual fund SIP corpus at 5 years: **₹12.4L** (expected CAGR 12.5%)" (with BarChart icon)

---

### PAGE 5: SCENARIO SIMULATOR (route: `/simulator`)

**Header:** "What-If Scenario Engine" with subtitle "Simulate financial decisions with 1,000 Monte Carlo scenarios"

**Scenario Input Section:**
- A prominent input/selector area: A dark card with gold border. Text: "Describe your scenario:" with an input field. Pre-filled example: "What if I increase my SIP to ₹25,000 per month?"
- A gold "Run Simulation" button

**Results Section (shown as if simulation completed):**

**Top row: Key Metrics (4 cards):**
- "Expected Corpus (5yr)" → **₹22.4L** (gold, large font)
- "Best Case (P90)" → **₹28.7L** (green-gold tint)
- "Worst Case (P10)" → **₹18.1L** (amber tint)
- "Improvement vs Current" → **+₹6.8L (+44%)** (bright gold with up arrow)

**Main chart:** A Recharts **BarChart styled as histogram** showing probability distribution of outcomes from 1,000 simulations. X-axis: corpus value buckets (₹16L–₹30L). Y-axis: frequency. Bars in gold gradient. A vertical dashed line showing the median at ₹22.4L.

**Comparison Panel (side by side cards):**
- **Current Plan:** SIP ₹15,000/mo | Savings Rate 18% | 5yr Corpus ₹15.6L
- **Proposed Plan:** SIP ₹25,000/mo | Savings Rate 26.3% | 5yr Corpus ₹22.4L
- Each card is dark with the proposed card having a subtle gold glow border

**Trade-off Analysis Card:**
- "Monthly discretionary budget drops: ₹28,000 → ₹23,000"
- "Emergency fund timeline unaffected"
- "Goa trip goal: probability increases 62% → 94%"

---

### PAGE 6: ALERT CENTER (route: `/alerts`)

**Header:** "Proactive Intelligence Alerts" with filter tabs: All | Critical | Warnings | Insights (active tab has gold underline)

**Alert Trend Mini-Chart:** A small Recharts BarChart showing alerts per week (last 4 weeks): 2, 5, 3, 4 alerts.

**Alert List:** Vertical list of alert cards, each with:
- Colored severity dot on the left (red, yellow, green, blue)
- Timestamp (e.g., "2 hours ago", "Yesterday")
- Alert title in bold white
- Description text in gray
- Recommended action button (gold outline, small)

**Alerts (pre-populated):**

1. 🔴 **Critical** — "Unusual Spending Spike Detected" — "Shopping spend this week: ₹12,400 — that's 3.1× your weekly average of ₹4,000. Primary transactions: Amazon ₹6,200, Flipkart ₹4,800." — Action: "Review Transactions" — 2 hours ago

2. 🟡 **Warning** — "Credit Utilization Rising" — "Credit card utilization at 68% (₹24,000 / ₹35,000 limit). Credit scores typically drop when utilization exceeds 30%. Pay ₹15,000 before March 20 billing cycle." — Action: "Set Payment Reminder" — 5 hours ago

3. 🟡 **Warning** — "Dining Budget Almost Exhausted" — "Dining budget: ₹7,400 / ₹8,000 used (92%) with 11 days remaining this month." — Action: "Adjust Budget" — Yesterday

4. 🟢 **Info** — "Upcoming Auto-Debit" — "SIP auto-debit of ₹15,000 scheduled for tomorrow (March 13). Current savings account balance: ₹2,45,000 — sufficient." — Action: "View Schedule" — Yesterday

5. 🔵 **Insight** — "Missing Recurring Transaction" — "Netflix subscription (₹649) was not charged this billing cycle. Last charge: Feb 10. Subscription may have been cancelled or card expired." — Action: "Check Subscription" — 2 days ago

6. 🟡 **Warning** — "Goal At Risk" — "Goa Trip savings: At current savings rate, projected to reach ₹46,200 by June — ₹3,800 short of your ₹50,000 target." — Action: "Adjust Savings Plan" — 3 days ago

---

### PAGE 7: TAX & INDIA INTELLIGENCE (route: `/tax`)

**Header:** "India Financial Intelligence"

**Section 80C Optimizer (top, full width):**
- Title: "Section 80C — Tax Saving Tracker (FY 2025-26)"
- A horizontal stacked **BarChart** (single bar) showing:
  - EPF: ₹86,400 (dark gold)
  - ELSS SIP: ₹18,000 (medium gold)
  - PPF: ₹24,000 (light gold)
  - Remaining: ₹21,600 (dark/empty segment with dashed border)
  - Total bar represents ₹1,50,000
- Stats: "Used: ₹1,28,400 / ₹1,50,000 (85.6%)" | "Remaining: ₹21,600"
- Gold highlighted recommendation card: "💡 Invest ₹21,600 in ELSS before March 31 to save **₹6,480** in tax (30% bracket)"

**Two-column grid below:**

**Left: Section 80D Card**
- "Section 80D — Medical Insurance"
- "Used: ₹0 / ₹25,000"
- Empty progress bar
- Recommendation: "Consider health insurance for additional ₹7,500 tax saving"

**Right: EPF Projection**
- Title: "EPF Corpus Projection"
- Recharts **LineChart** showing EPF growth curve from current ₹5.6L to ₹1.2Cr at age 60 (@ 8.15% rate). Gold curve on dark background with key milestone markers.

**Bottom row:**

**Festival Budget Predictor Card:**
- "🎆 Diwali 2026 Predicted Budget: ₹28,000"
- "Based on your Oct 2025 spending patterns"
- "Suggestion: Start saving ₹7,000/month from August"
- Small bar chart comparing last 2 Diwali spends

**UPI Spending Analytics Card:**
- Title: "UPI Transaction Intelligence"
- Mini horizontal bar chart showing top UPI merchants: Swiggy (₹5,200), Amazon (₹4,800), Uber (₹2,100), Zomato (₹3,100), Flipkart (₹1,900)
- "Auto-categorized from 142 UPI transactions this month"

---

### GLOBAL DESIGN SPECIFICATIONS:

- **Color Palette:** Background: #0A0A0A, #111111, #1A1A1A. Cards: #1E1E1E with border rgba(212,175,55,0.15). Primary accent: #D4AF37 (gold). Secondary accent: #FFD700 (bright gold). Text: #FFFFFF, #A0A0A0, #666666. Success: #4CAF50. Warning: #FFB300. Error: #E53935.
- **Typography:** Clean sans-serif (Inter or system font). Large bold numbers for metrics. Smaller gray labels.
- **Cards:** Rounded corners (12px), subtle gold border (1px, 10-15% opacity), slight background blur for glass-morph feel.
- **Charts:** All Recharts. Gold/amber color scheme. Dark grid lines (#222). No chart backgrounds (transparent). Smooth animations on render.
- **Interactions:** Sidebar navigation with hover gold glow effect. Smooth page transitions. Chart hover tooltips with dark style. Buttons with gold hover brightness increase. Alert cards with subtle hover lift.
- **Responsiveness:** Desktop-first (this is a dashboard product). Sidebar collapses to icons on tablet.
- **Font sizes:** Metric values: 28-32px bold. Card titles: 16px semibold. Body text: 14px regular. Small labels: 12px.

Make every screen look like a **real AI startup product** — data-rich, visually impressive, with the intelligence of the system front and center. Every chart, metric, and insight card should reinforce that this is not a simple app — it is an **AI-powered financial reasoning engine**.

---
