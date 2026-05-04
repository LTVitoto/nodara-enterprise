import { Badge } from "@/components/ui/Badge";

export function SectionHeader({
  title,
  description,
  sprint,
  action
}: {
  title: string;
  description: string;
  sprint?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
      <div className="max-w-3xl">
        {sprint ? <Badge tone="info" className="mb-3">{sprint}</Badge> : null}
        <h1 className="text-3xl font-black tracking-tight text-brand-navy md:text-4xl">{title}</h1>
        <p className="mt-3 text-base leading-7 text-brand-muted">{description}</p>
      </div>
      {action}
    </div>
  );
}
