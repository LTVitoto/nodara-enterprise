"use client";
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardTitle } from '@/components/ui/Card';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { projectsRepository, futureRepository } from '@/services/repositories';
export function ProjectDetailView({ projectId }: { projectId: string }) {
  const [project, setProject] = useState<any>(null);
  const [readme, setReadme] = useState('');
  const [editReadme, setEditReadme] = useState(false);
  const [tempReadme, setTempReadme] = useState('');
  const [editRole, setEditRole] = useState<string | null>(null);
  const [tempRole, setTempRole] = useState('');
  const loadData = async () => {
      const p = await projectsRepository.get(projectId);
      setProject(p);
      const r = await futureRepository.readme(projectId);
      setReadme(r?.content || 'No hay README');
  };
  useEffect(() => { loadData(); }, [projectId]);
  const saveRole = async (key: string) => {
    await projectsRepository.patch(projectId, { [key]: tempRole });
    setProject({...project, [key]: tempRole});
    setEditRole(null);
  };
  const saveReadme = async () => {
    await futureRepository.updateReadme(projectId, tempReadme);
    setReadme(tempReadme);
    setEditReadme(false);
  };
  if (!project) return <p>Cargando...</p>;
  return (
    <div>
      <SectionHeader title={project.titulo} description={project.descripcion} action={<Link href={`/chat/${project.id}`}><Button>Abrir Chat</Button></Link>} />
      <div className='grid gap-6 xl:grid-cols-[1.1fr_.9fr]'>
        <div className='space-y-6'>
          <Card>
            <div className='flex justify-between items-center mb-4'>
              <CardTitle eyebrow={project.nombre_slug} title='README.md' />
              <Button variant='secondary' onClick={() => { setTempReadme(readme); setEditReadme(!editReadme); }}>{editReadme ? 'Cancelar' : 'Editar'}</Button>
            </div>
            {editReadme ? (
              <div className='space-y-3'>
                <textarea className='w-full min-h-[300px] p-4 bg-brand-deep text-brand-bright font-mono text-xs rounded-xl' value={tempReadme} onChange={e => setTempReadme(e.target.value)} />
                <Button onClick={saveReadme}>Guardar</Button>
              </div>
            ) : (
              <pre className='p-4 bg-brand-soft rounded-xl text-sm whitespace-pre-wrap'>{readme}</pre>
            )}
          </Card>
          <Card>
             <CardTitle eyebrow='Metadata' title='Detalles' />
             <pre className='mt-5 overflow-auto rounded-3xl bg-brand-deep p-5 text-xs leading-6 text-brand-bright'>{JSON.stringify({ tecnologias: project.tecnologias, microservicios: project.microservicios }, null, 2)}</pre>
          </Card>
        </div>
        <Card>
          <CardTitle eyebrow='Roles' title='Sala multi-agente' />
          <div className='space-y-4 mt-4'>
            {[['rol_gemini', 'Gemini · Infra'], ['rol_chatgpt', 'ChatGPT · Backend'], ['rol_claude', 'Claude · Frontend']].map(([key, label]) => (
              <div key={key} className='p-3 border border-brand-border rounded-xl bg-brand-soft'>
                <div className='flex justify-between items-center'>
                  <span className='font-bold text-sm text-brand-navy'>{label}</span>
                  <button className='text-brand-cyan text-xs font-black uppercase' onClick={() => { setEditRole(key); setTempRole(project[key]); }}>Editar</button>
                </div>
                {editRole === key ? (
                  <div className='mt-3 flex flex-col gap-2'>
                    <textarea className='w-full text-xs p-2 border rounded-xl h-20' value={tempRole} onChange={e => setTempRole(e.target.value)} />
                    <Button onClick={() => saveRole(key)}>Guardar Rol</Button>
                  </div>
                ) : (
                  <p className='text-xs text-brand-muted mt-2'>{project[key]}</p>
                )}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
