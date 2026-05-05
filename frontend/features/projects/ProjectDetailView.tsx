"use client";
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
  const [editDesc, setEditDesc] = useState(false);
  const [tempDesc, setTempDesc] = useState('');
  const [editRole, setEditRole] = useState<string | null>(null);
  const [tempRole, setTempRole] = useState('');
  const router = useRouter();
  const loadData = async () => {
      const p = await projectsRepository.get(projectId);
      setProject(p); setTempDesc(p.descripcion);
      const r = await futureRepository.readme(projectId);
      setReadme(r?.content || 'No hay README');
  };
  useEffect(() => { loadData(); }, [projectId]);
  const saveRole = async (key: string) => {
    await projectsRepository.patch(projectId, { [key]: tempRole });
    setProject({...project, [key]: tempRole});
    setEditRole(null);
  };
  const saveDesc = async () => {
    await projectsRepository.patch(projectId, { descripcion: tempDesc });
    setProject({...project, descripcion: tempDesc});
    setEditDesc(false);
  };
  const saveReadme = async () => {
    await futureRepository.updateReadme(projectId, tempReadme);
    setReadme(tempReadme);
    setEditReadme(false);
  };
  const handleDelete = async () => {
    if(confirm('¿Eliminar proyecto DEFINITIVAMENTE (Workspace y Repo en GitHub)?')) {
      await projectsRepository.delete(projectId);
      router.push('/projects');
    }
  };
  if (!project) return <p>Cargando...</p>;
  return (
    <div>
      <SectionHeader title={project.titulo} description={project.descripcion.substring(0,50)+'...'} action={<div className='flex gap-2'><Button variant='secondary' onClick={handleDelete}>Borrar</Button><Link href={`/chat/${project.id}`}><Button>Abrir Chat</Button></Link></div>} />
      <div className='grid gap-6 xl:grid-cols-[1.1fr_.9fr]'>
        <div className='space-y-6'>
          <Card>
            <div className='flex justify-between items-center mb-4'>
              <CardTitle eyebrow='Contexto' title='Descripción' />
              <Button variant='secondary' onClick={() => setEditDesc(!editDesc)}>{editDesc ? 'Cancelar' : 'Editar'}</Button>
            </div>
            {editDesc ? (
              <div className='space-y-3'>
                <textarea className='w-full min-h-[100px] p-2 border rounded-xl text-sm' value={tempDesc} onChange={e => setTempDesc(e.target.value)} />
                <Button onClick={saveDesc}>Guardar</Button>
              </div>
            ) : (
              <p className='text-sm text-brand-muted'>{project.descripcion}</p>
            )}
          </Card>
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
        </div>
        <div className='space-y-6'>
          <Card>
            <div className='flex justify-between'><CardTitle eyebrow='Metadata' title='Detalles' /></div>
            <p className='text-xs mt-2'><b>Responsable:</b> {project.responsable || 'N/A'}</p>
            <p className='text-xs'><b>Año:</b> {project.anio}</p>
            <p className='text-xs'><b>Estado:</b> {project.estado}</p>
          </Card>
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
    </div>
  );
}
