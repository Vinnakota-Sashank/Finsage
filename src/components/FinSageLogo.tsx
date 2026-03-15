import { Sparkles } from "lucide-react";

interface FinSageLogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
}

const FinSageLogo = ({ size = "md", showText = true }: FinSageLogoProps) => {
  const iconSizes = { sm: 18, md: 24, lg: 32 };
  const textSizes = { sm: "text-lg", md: "text-xl", lg: "text-3xl" };

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <Sparkles size={iconSizes[size]} className="text-primary" />
        <div className="absolute inset-0 blur-md bg-primary/30" />
      </div>
      {showText && (
        <span className={`${textSizes[size]} font-bold gold-gradient-text`}>
          FinSage
        </span>
      )}
    </div>
  );
};

export default FinSageLogo;
