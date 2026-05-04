import { cn } from "@/lib/cn";

const tones = {
  info: "border-brand-cyan/30 bg-brand-cyan/10 text-brand-navy",
  success: "border-state-success/30 bg-state-success/10 text-state-success",
  warning: "border-state-warning/30 bg-state-warning/10 text-state-warning",
  danger: "border-state-danger/30 bg-state-danger/10 text-state-danger",
  neutral: "border-brand-border bg-brand-soft text-brand-muted"
};

export function Badge({ children, tone = "neutral", className }: { children: React.ReactNode; tone?: keyof typeof tones; className?: string }) {
  return <span className={cn("inline-flex rounded-full border px-2.5 py-1 text-xs font-black", tones[tone], className)}>{children}</span>;
}
