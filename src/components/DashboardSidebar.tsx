import { useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  TrendingUp,
  FlaskConical,
  Bell,
  Receipt,
} from "lucide-react";
import FinSageLogo from "./FinSageLogo";

const navItems = [
  { title: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
  { title: "AI Chat", icon: MessageSquare, path: "/chat" },
  { title: "Forecasting", icon: TrendingUp, path: "/forecasting" },
  { title: "Simulator", icon: FlaskConical, path: "/simulator" },
  { title: "Alerts", icon: Bell, path: "/alerts" },
  { title: "Tax Intelligence", icon: Receipt, path: "/tax" },
];

const DashboardSidebar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <aside className="w-64 min-h-screen bg-surface-1 border-r border-gold-muted flex flex-col">
      <div className="p-6 border-b border-gold-muted">
        <FinSageLogo />
      </div>

      <nav className="flex-1 py-4">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-6 py-3 text-sm font-medium transition-all duration-200 relative group ${
                isActive
                  ? "text-primary bg-primary/10"
                  : "text-muted-foreground hover:text-foreground hover:bg-surface-3"
              }`}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-8 bg-primary rounded-r" />
              )}
              <item.icon size={20} className={isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"} />
              <span>{item.title}</span>
            </button>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gold-muted flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center text-primary font-semibold text-sm">
          AM
        </div>
        <div>
          <p className="text-sm font-medium text-foreground">Arjun Mehta</p>
          <p className="text-xs text-muted-foreground">Pro Account</p>
        </div>
      </div>
    </aside>
  );
};

export default DashboardSidebar;
