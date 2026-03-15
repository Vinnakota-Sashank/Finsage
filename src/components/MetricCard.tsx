import { ArrowUp, ArrowDown } from "lucide-react";

interface MetricCardProps {
  label: string;
  value: string;
  change?: string;
  positive?: boolean;
}

const MetricCard = ({ label, value, change, positive = true }: MetricCardProps) => {
  return (
    <div className="glass-card p-5">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">{label}</p>
      <p className="text-2xl font-bold text-primary">{value}</p>
      {change && (
        <div className={`flex items-center gap-1 mt-2 text-xs font-medium ${positive ? "text-success" : "text-error"}`}>
          {positive ? <ArrowUp size={12} /> : <ArrowDown size={12} />}
          <span>{change}</span>
        </div>
      )}
    </div>
  );
};

export default MetricCard;
