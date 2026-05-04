import { ProjectDetailView } from "@/features/projects/ProjectDetailView";
export default function Page({ params }: { params: { id: string } }) { return <ProjectDetailView projectId={params.id} />; }
