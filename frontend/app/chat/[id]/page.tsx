import { MultiAgentChat } from "@/features/chat/MultiAgentChat";
export default function Page({ params }: { params: { id: string } }) { return <MultiAgentChat projectId={params.id} />; }
