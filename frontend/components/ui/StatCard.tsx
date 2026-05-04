import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";

export function StatCard({ label, value, trend, tone = "info" }: { label: string; value: string; trend?: string; tone?: "info" | "success" | "warning" | "danger" }) {
  return (
    <Card className="p-5">
      <div className="text-sm font-bold text-brand-muted">{label}</div>
      <div className="mt-3 text-3xl font-black text-brand-navy">{value}</div>
      {trend ? <Badge tone={tone} className="mt-4">{trend}</Badge> : null}
    </Card>
  );
}
