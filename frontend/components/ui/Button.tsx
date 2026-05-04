import { cn } from "@/lib/cn";
import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";

export function Button({ className, variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const variants: Record<Variant, string> = {
    primary: "bg-brand-cyan text-brand-deep hover:bg-brand-bright shadow-cyan",
    secondary: "bg-white text-brand-navy border border-brand-border hover:border-brand-cyan",
    ghost: "bg-transparent text-brand-navy hover:bg-brand-lilac",
    danger: "bg-state-danger text-white hover:opacity-90"
  };

  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-2xl px-4 py-2 text-sm font-bold transition disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
