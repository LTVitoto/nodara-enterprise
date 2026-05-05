"use client";
import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardTitle } from '@/components/ui/Card';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { futureRepository, projectsRepository, githubRepository } from '@/services/repositories';
function ProjectSelector({ projects, projectId, setProjectId }: any) {
    if (projects.length === 0) return null;
    return (
        <div className='mb-6'>
            <label className='mr-4 font-bold text-sm'>Seleccionar Proyecto:</label>
            <select className='border border-brand-border bg-white p-2 rounded-xl text-sm' value={projectId} onChange={(e) => setProjectId(e.target.value)}>
                {projects.map((p:any) => <option key={p.id} value={p.id}>{p.titulo}</option>)}
            </select>
        </div>
    );
}
export function AgentsView() {
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string>('');
  const [project, setProject] = useState<any>(null);
  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => { if(projectId) projectsRepository.get(projectId).then(setProject); }, [projectId]);
  return (
    <div>
      <SectionHeader title='Gestión de agentes' description='Roles activos según el proyecto seleccionado.' />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      {project && (
        <div className='grid gap-5 xl:grid-cols-3'>
          <Card><Badge tone='success'>Gemini</Badge><h3 className='mt-3 font-black text-xl'>Infraestructura</h3><p className='mt-2 text-sm text-brand-muted'>{project.rol_gemini}</p></Card>
          <Card><Badge tone='success'>ChatGPT</Badge><h3 className='mt-3 font-black text-xl'>Backend y Datos</h3><p className='mt-2 text-sm text-brand-muted'>{project.rol_chatgpt}</p></Card>
          <Card><Badge tone='success'>Claude</Badge><h3 className='mt-3 font-black text-xl'>Frontend y UX</h3><p className='mt-2 text-sm text-brand-muted'>{project.rol_claude}</p></Card>
        </div>
      )}
    </div>
  );
}
function Tree({ nodes, depth = 0, onFileClick }: any) {
  return (
    <div className='space-y-1 mt-2'>
      {nodes.map((node: any) => (
        <div key={node.id} style={{ marginLeft: depth * 20 }}>
          <div className={`px-2 py-1 text-sm rounded ${node.type === 'file' ? 'cursor-pointer hover:bg-brand-soft text-brand-cyan' : 'font-bold text-brand-navy'}`} onClick={() => node.type === 'file' && onFileClick(node.path)}>
            {node.type === 'folder' ? '📁' : '📄'} {node.name}
          </div>
          {node.children && <Tree nodes={node.children} depth={depth + 1} onFileClick={onFileClick} />}
        </div>
      ))}
    </div>
  );
}
export function WorkspaceView() {
  const [items, setItems] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string>('');
  const [fileContent, setFileContent] = useState<string>('');
  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => { if (projectId) { futureRepository.workspace(projectId).then(setItems); setFileContent(''); } }, [projectId]);
  const handleFileClick = async (path: string) => {
      const res = await futureRepository.workspaceFile(projectId, path);
      setFileContent(res?.content || 'No se pudo leer el archivo.');
  };
  return (
    <div>
      <SectionHeader title='Workspace' description='Haz clic en un archivo para visualizarlo.' />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <div className='grid xl:grid-cols-[300px_1fr] gap-6'>
        <Card>
          <CardTitle title='Explorador' />
          <Tree nodes={items} onFileClick={handleFileClick} />
        </Card>
        <Card>
           <CardTitle title='Visualizador' />
           <pre className='mt-4 p-4 bg-brand-deep text-brand-bright text-xs rounded-xl overflow-auto max-h-[600px]'>{fileContent || 'Selecciona un archivo del explorador.'}</pre>
        </Card>
      </div>
    </div>
  );
}
export function GithubView() {
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string>('');
  const [output, setOutput] = useState<string>('');
  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  const runCmd = async (action: 'status' | 'add' | 'commit' | 'push') => {
      setOutput('Ejecutando...');
      try {
          const res = await githubRepository[action](projectId);
          setOutput(res?.output || 'Comando ejecutado con éxito.');
      } catch (e) { setOutput('Error ejecutando el comando.'); }
  };
  return (
    <div>
      <SectionHeader title='GitOps' description='Control de versiones.' />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <Card>
        <div className='flex gap-2 mb-4'>
            <Button variant='secondary' onClick={() => runCmd('status')}>Git Status</Button>
            <Button variant='secondary' onClick={() => runCmd('add')}>Git Add</Button>
            <Button variant='secondary' onClick={() => runCmd('commit')}>Git Commit</Button>
            <Button onClick={() => runCmd('push')}>Git Push</Button>
        </div>
        <pre className='bg-brand-deep text-brand-bright p-4 rounded-xl text-sm whitespace-pre-wrap'>{output}</pre>
      </Card>
    </div>
  );
}
export function MetricsView() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { futureRepository.metrics().then(setItems); }, []);
  return (
    <div>
      <SectionHeader title='Métricas' description='Dashboard.' />
      <div className='grid gap-5 md:grid-cols-3'>
        {items.map((m, i) => (
        <Card key={i}>
            <p className='text-sm font-bold text-brand-muted'>{m.label}</p>
            <p className='mt-3 text-3xl font-black'>{m.value}</p>
            <Badge tone={m.tone} className='mt-4'>{m.trend}</Badge>
        </Card>
        ))}
      </div>
    </div>
  );
}
export function AuditView() { return <div><SectionHeader title='Auditoría' description='Logs' /></div>; }
export function ToolsView() { return <div><SectionHeader title='Tools' description='Catálogo' /></div>; }
export function MessagesView() { return <div><SectionHeader title='Mensajes' description='Historial' /></div>; }
