import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Forecasting from "./pages/Forecasting";
import Simulator from "./pages/Simulator";
import Alerts from "./pages/Alerts";
import Tax from "./pages/Tax";
import Ingestion from "./pages/Ingestion";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/forecasting" element={<Forecasting />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/tax" element={<Tax />} />
          <Route path="/ingestion" element={<Ingestion />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
