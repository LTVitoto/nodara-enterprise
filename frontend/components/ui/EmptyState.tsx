import { Button } from "@/components/ui/Button";

export function EmptyState({ title, description, actionLabel, onAction }: { title: string; description: string; actionLabel?: string; onAction?: () => void }) {
  return (
    <div className="rounded-3xl border border-dashed border-brand-border bg-white/70 p-10 text-center">
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-cyan/10 text-2xl text-brand-cyan">◇</div>
      <h3 className="text-xl font-black text-brand-navy">{title}</h3>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-brand-muted">{description}</p>
      {actionLabel && onAction ? <Button onClick={onAction} className="mt-6">{actionLabel}</Button> : null}
    </div>
  );
}
