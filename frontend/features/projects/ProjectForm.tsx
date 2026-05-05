"use client";
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { projectsRepository } from '@/services/repositories';
export function ProjectForm() {
  const router = useRouter();
  const [form, setForm] = useState({ titulo: '', responsable: '', descripcion: '', github_url: '', anio: new Date().getFullYear(), rol_gemini: 'Experto Infra, FullStack', rol_chatgpt: 'Experto Backend y Datos', rol_claude: 'Experto Frontend y UX', estado: 'privado' });
  const submit = async (e: any) => {
    e.preventDefault();
    const p = await projectsRepository.create(form);
    if(p && p.id) router.push(`/projects/${p.id}`);
  };
  return (
    <form onSubmit={submit} className='max-w-2xl space-y-6'>
      <SectionHeader title='Crear proyecto' description='Registra una nueva iniciativa.' />
      <div className='p-6 bg-white rounded-3xl shadow-sm border space-y-4'>
        <h3 className='font-black text-brand-navy'>Datos base</h3>
        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Título</label><input className='w-full border rounded-xl p-3 text-sm' value={form.titulo} onChange={e => setForm({...form, titulo: e.target.value})} required /></div>
        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Responsable</label><input className='w-full border rounded-xl p-3 text-sm' value={form.responsable} onChange={e => setForm({...form, responsable: e.target.value})} required /></div>
        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Descripción</label><textarea className='w-full border rounded-xl p-3 text-sm min-h-[100px]' value={form.descripcion} onChange={e => setForm({...form, descripcion: e.target.value})} required /></div>
        <div className='grid grid-cols-2 gap-4'>
          <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>GitHub URL</label><input className='w-full border rounded-xl p-3 text-sm' value={form.github_url} onChange={e => setForm({...form, github_url: e.target.value})} /></div>
          <div>
            <label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Privacidad GitOps</label>
            <select className='w-full border rounded-xl p-3 text-sm' value={form.estado} onChange={e => setForm({...form, estado: e.target.value})}>
              <option value='privado'>Privado</option>
              <option value='publico'>Público</option>
            </select>
          </div>
        </div>
        <h3 className='font-black text-brand-navy mt-6'>Roles Multi-Agente</h3>
        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol Gemini</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_gemini} onChange={e => setForm({...form, rol_gemini: e.target.value})} /></div>
        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol ChatGPT</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_chatgpt} onChange={e => setForm({...form, rol_chatgpt: e.target.value})} /></div>
        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol Claude</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_claude} onChange={e => setForm({...form, rol_claude: e.target.value})} /></div>
        <Button type='submit' className='w-full mt-4'>Crear proyecto</Button>
      </div>
    </form>
  );
}
