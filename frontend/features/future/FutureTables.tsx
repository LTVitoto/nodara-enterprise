"use client";
import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardTitle } from '@/components/ui/Card';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { futureRepository, projectsRepository, githubRepository } from '@/services/repositories';
import { formatDate } from '@/lib/format';
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
  const [edit, setEdit] = useState<string | null>(null);
  const [temp, setTemp] = useState('');
  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => { if(projectId) projectsRepository.get(projectId).then(setProject); }, [projectId]);
  const save = async (key: string) => {
    await projectsRepository.patch(projectId, { [key]: temp });
    setProject({...project, [key]: temp}); setEdit(null);
  };
  return (
    <div>
      <SectionHeader title='Gestión de agentes' description='Roles por proyecto.' />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      {project && (
        <div className='grid gap-5 xl:grid-cols-3'>
          {[['rol_gemini','Gemini'],['rol_chatgpt','ChatGPT'],['rol_claude','Claude']].map(([k, n]) => (
            <Card key={k}><Badge tone='success'>{n}</Badge>
            <div className='flex justify-between mt-3'><h3 className='font-black text-xl'>Rol</h3><button className='text-brand-cyan text-xs font-black uppercase' onClick={() => {setEdit(k); setTemp(project[k]);}}>Editar</button></div>
            {edit === k ? <div className='mt-2'><textarea className='w-full text-xs p-2 border rounded' value={temp} onChange={e => setTemp(e.target.value)} /><Button onClick={() => save(k)}>Guardar</Button></div> : <p className='mt-2 text-sm text-brand-muted'>{project[k]}</p>}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
function Tree({ nodes, depth = 0, onFileClick, onDeleteClick }: any) {
  return (
    <div className='space-y-1 mt-2'>
      {nodes.map((node: any) => (
        <div key={node.id} style={{ marginLeft: depth * 20 }} className='group'>
          <div className={`px-2 py-1 text-sm rounded flex justify-between items-center ${node.type === 'file' ? 'hover:bg-brand-soft text-brand-cyan' : 'font-bold text-brand-navy'}`}>
            <span className='cursor-pointer flex-1' onClick={() => node.type === 'file' && onFileClick(node.path)}> {node.type === 'folder' ? '📁' : '📄'} {node.name} </span>
            {node.type === 'file' && <button onClick={() => onDeleteClick(node.path)} className='hidden group-hover:block text-red-500 text-xs font-bold'>X</button>}
          </div>
          {node.children && <Tree nodes={node.children} depth={depth + 1} onFileClick={onFileClick} onDeleteClick={onDeleteClick} />}
        </div>
      ))}
    </div>
  );
}
export function WorkspaceView() {
  const [items, setItems] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string>('');
  const [fileData, setFileData] = useState<any>({content: '', is_image: false, path: ''});
  const [tempContent, setTempContent] = useState('');
  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  const loadTree = () => { if (projectId) { futureRepository.workspace(projectId).then(setItems); setFileData({content: '', is_image: false, path: ''}); } };
  useEffect(() => { loadTree(); }, [projectId]);
  const handleFileClick = async (path: string) => {
      const res = await futureRepository.workspaceFile(projectId, path);
      setFileData({ content: res?.content || '', is_image: res?.is_image, path });
      setTempContent(res?.content || '');
  };
  const handleSave = async () => {
      if(fileData.path) { await futureRepository.updateWorkspaceFile(projectId, fileData.path, tempContent); alert('Guardado'); }
  };
  const handleDelete = async (path: string) => {
      if(confirm('¿Eliminar archivo?')) { await futureRepository.deleteWorkspaceFile(projectId, path); loadTree(); }
  };
  return (
    <div>
      <SectionHeader title='Workspace' description='Edita o elimina archivos físicamente.' />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <div className='grid xl:grid-cols-[300px_1fr] gap-6'>
        <Card>
          <CardTitle title='Explorador' />
          <Tree nodes={items} onFileClick={handleFileClick} onDeleteClick={handleDelete} />
        </Card>
        <Card>
           <div className='flex justify-between items-center mb-4'>
             <CardTitle title='Visualizador / Editor' />
             {!fileData.is_image && fileData.path && <Button onClick={handleSave}>Guardar Fichero</Button>}
           </div>
           <div className='mt-4 p-4 bg-brand-deep text-brand-bright rounded-xl overflow-auto max-h-[600px] flex items-center justify-center min-h-[100px]'>
              {fileData.is_image ? <img src={fileData.content} className='max-w-full rounded shadow-xl' alt='Preview' /> : <textarea className='w-full min-h-[300px] bg-transparent outline-none text-xs font-mono' value={tempContent} onChange={e => setTempContent(e.target.value)} placeholder='Selecciona archivo...' />}
           </div>
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
          setOutput(res?.output || 'Ejecutado con éxito.');
      } catch (e) { setOutput('Error.'); }
  };
  return (
    <div>
      <SectionHeader title='GitOps' description='Control de versiones con Push Automático.' />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <Card>
        <div className='flex gap-2 mb-4'>
            <Button variant='secondary' onClick={() => runCmd('status')}>Git Status</Button>
            <Button variant='secondary' onClick={() => runCmd('add')}>Git Add .</Button>
            <Button variant='secondary' onClick={() => runCmd('commit')}>Git Commit</Button>
            <Button onClick={() => runCmd('push')}>Git Push (API)</Button>
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
export function AuditView() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { futureRepository.audit().then(setItems); }, []);
  return (
    <div><SectionHeader title='Auditoría' description='Logs reales de la BD' />
      <div className='space-y-4'>
        {items.length === 0 ? <p>No hay eventos de auditoría registrados.</p> : items.map((a:any) => (
        <Card key={a.id}><Badge tone={a.severity}>{a.severity}</Badge>
            <h3 className='mt-3 font-black'>{a.action}</h3>
            <p className='mt-1 text-sm text-brand-muted'>{a.actor} · {a.target}</p>
            <p className='mt-1 text-xs text-brand-muted'>{formatDate(a.fecha_evento)}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}
export function ToolsView() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(() => { futureRepository.tools().then(setItems); }, []);
  return (
    <div><SectionHeader title='Catálogo Tools' description='Lectura libre vs escritura con HIL.' />
      <div className='grid gap-5 md:grid-cols-2'>
        {items.length === 0 ? <p>Sin herramientas.</p> : items.map((t:any) => (
        <Card key={t.name}><Badge tone={t.requires_approval ? 'warning' : 'success'}>{t.requires_approval ? 'Requiere HIL' : 'Libre'}</Badge>
            <h3 className='mt-3 text-lg font-black'>{t.name}</h3>
            <p className='mt-2 text-sm text-brand-muted'>{t.description}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}
export function MessagesView() {
  const [items, setItems] = useState<any[]>([]);
  const [projects, setProjects] = useState<any[]>([]);
  const [projectId, setProjectId] = useState<string>('');
  useEffect(() => { projectsRepository.list().then(p => { setProjects(p); if(p.length > 0) setProjectId(p[0].id); }); }, []);
  useEffect(() => { if(projectId) futureRepository.messages(projectId).then(setItems); }, [projectId]);
  return (
    <div><SectionHeader title='Mensajes' description='Historial por proyecto.' />
      <ProjectSelector projects={projects} projectId={projectId} setProjectId={setProjectId} />
      <div className='space-y-4'>
        {items.length === 0 ? <p>Sin mensajes.</p> : items.map((m:any) => (
        <Card key={m.id}><Badge tone={m.remitente === 'user' ? 'info' : 'success'}>{m.remitente}</Badge>
            <p className='mt-3 text-sm text-brand-navy whitespace-pre-wrap'>{m.contenido}</p>
        </Card>
        ))}
      </div>
    </div>
  );
}
