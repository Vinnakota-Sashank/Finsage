# FinSage — AI-Powered Personal Finance Intelligence System

> *"Talk to your money. It finally talks back."*

## Overview

**FinSage** is a conversational AI financial intelligence platform designed for Indian professionals. It acts as a personal CFO — you ask questions in natural language, and it queries your structured financial data, generates intelligent visualizations, forecasts spending, simulates scenarios, and proactively alerts you to anomalies.

## Key Features

- **Agentic AI Chat** — Natural language queries backed by structured function calls against real financial data
- **Auto-Generated Visualizations** — Dynamic chart selection (donut, bar, line, gauge, treemap) based on query type
- **Predictive Forecasting** — Prophet-based time series projections with confidence intervals
- **Monte Carlo Simulator** — "What-if" scenario engine with 1,000 probabilistic simulations
- **Proactive Alerts** — Anomaly detection for spending spikes, credit health, budget breaches, and goal risks
- **India-Specific Intelligence** — Section 80C/80D tax optimization, UPI analytics, EPF projections, festival budgets

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| Animations | Framer Motion |
| State | React Query + Zustand |

## Getting Started

```sh
# Install dependencies
npm install

# Start the development server
npm run dev
```

The app runs on `http://localhost:8080`.

## Project Structure

```
src/
├── pages/          # Route-level page components
├── components/     # Reusable UI components
├── hooks/          # Custom React hooks
├── lib/            # Utilities
└── main.tsx        # Entry point
```

## Team

Built by the FinSage team for VNR Design-a-thon 2026.
