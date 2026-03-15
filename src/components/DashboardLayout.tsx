import { ReactNode } from "react";
import { Bell } from "lucide-react";
import DashboardSidebar from "./DashboardSidebar";

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  showTopBar?: boolean;
}

const DashboardLayout = ({ children, title, subtitle, showTopBar = true }: DashboardLayoutProps) => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  return (
    <div className="flex min-h-screen bg-background">
      <DashboardSidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        {showTopBar && (
          <header className="h-16 border-b border-gold-muted flex items-center justify-between px-8 bg-surface-1/50 backdrop-blur-sm">
            <div>
              {title ? (
                <>
                  <h1 className="text-lg font-semibold text-foreground">{title}</h1>
                  {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
                </>
              ) : (
                <p className="text-lg font-medium text-foreground">
                  {getGreeting()}, <span className="text-primary">Arjun</span>
                </p>
              )}
            </div>
            <div className="flex items-center gap-4">
              <button className="relative p-2 rounded-lg hover:bg-surface-3 transition-colors">
                <Bell size={20} className="text-muted-foreground" />
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-error rounded-full text-[10px] font-bold flex items-center justify-center text-foreground">
                  3
                </span>
              </button>
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs font-semibold">
                AM
              </div>
            </div>
          </header>
        )}
        <main className="flex-1 overflow-y-auto p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
