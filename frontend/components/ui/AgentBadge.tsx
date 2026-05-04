import { cn } from "@/lib/cn";
import type { AgentName } from "@/types/domain";

const labels: Record<AgentName, string> = {
  gemini: "Gemini · Infra",
  chatgpt: "ChatGPT · Fullstack",
  claude: "Claude · Legacy",
  orchestrator: "Alineación"
};

const styles: Record<AgentName, string> = {
  gemini: "bg-indigo-50 text-indigo-700 border-indigo-200",
  chatgpt: "bg-brand-cyan/10 text-brand-navy border-brand-cyan/30",
  claude: "bg-violet-50 text-violet-700 border-violet-200",
  orchestrator: "bg-brand-deep text-white border-brand-cyan/40"
};

export function AgentBadge({ agent }: { agent: AgentName }) {
  return (
    <span className={cn("inline-flex rounded-full border px-3 py-1 text-xs font-black", styles[agent])}>
      {labels[agent]}
    </span>
  );
}
