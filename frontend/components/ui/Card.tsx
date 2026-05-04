import { cn } from "@/lib/cn";

export function Card({ children, className }: { children: React.ReactNode; className?: string }) {
  return <section className={cn("rounded-3xl border border-brand-border bg-white/90 p-6 shadow-panel", className)}>{children}</section>;
}

export function CardTitle({ title, eyebrow, action }: { title: string; eyebrow?: string; action?: React.ReactNode }) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div>
        {eyebrow ? <p className="text-xs font-black uppercase tracking-[0.24em] text-brand-cyan">{eyebrow}</p> : null}
        <h2 className="mt-1 text-xl font-black text-brand-navy">{title}</h2>
      </div>
      {action}
    </div>
  );
}
