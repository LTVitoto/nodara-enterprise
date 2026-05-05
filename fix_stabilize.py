import os

def w(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ Reparado: {path}")

# 1. FIX BACKEND: Crear el modelo EventoAuditoria
w("backend/app/models/audit.py", [
    "from sqlalchemy import Column, Integer, String, DateTime",
    "from datetime import datetime",
    "from app.database import Base",
    "class EventoAuditoria(Base):",
    "    __tablename__ = 'eventos_auditoria'",
    "    id = Column(Integer, primary_key=True, autoincrement=True)",
    "    actor = Column(String(255))",
    "    action = Column(String(255))",
    "    target = Column(String(255))",
    "    severity = Column(String(50), default='info')",
    "    fecha_evento = Column(DateTime, default=datetime.utcnow)"
])

# 2. Registrar el modelo en __init__.py
init_path = "backend/app/models/__init__.py"
if os.path.exists(init_path):
    with open(init_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "EventoAuditoria" not in content:
        with open(init_path, "a", encoding="utf-8") as f:
            f.write("\nfrom app.models.audit import EventoAuditoria\n")
else:
    w(init_path, ["from app.models.audit import EventoAuditoria"])

# 3. Actualizar los routers para importar desde audit en lugar de governance
for router_file in ["backend/app/routers/audit.py", "backend/app/routers/github.py"]:
    if os.path.exists(router_file):
        with open(router_file, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("from app.models.governance import EventoAuditoria", "from app.models.audit import EventoAuditoria")
        with open(router_file, "w", encoding="utf-8") as f:
            f.write(content)

# 4. FIX FRONTEND: Eliminar dependencia de Input inexistente y usar HTML nativo
w("frontend/features/projects/ProjectForm.tsx", [
    "\"use client\";",
    "import { useState } from 'react';",
    "import { useRouter } from 'next/navigation';",
    "import { Button } from '@/components/ui/Button';",
    "import { SectionHeader } from '@/components/ui/SectionHeader';",
    "import { projectsRepository } from '@/services/repositories';",
    "export function ProjectForm() {",
    "  const router = useRouter();",
    "  const [form, setForm] = useState({ titulo: '', responsable: '', descripcion: '', github_url: '', anio: new Date().getFullYear(), rol_gemini: 'Experto Infra, FullStack', rol_chatgpt: 'Experto Backend y Datos', rol_claude: 'Experto Frontend y UX', estado: 'privado' });",
    "  const submit = async (e: any) => {",
    "    e.preventDefault();",
    "    const p = await projectsRepository.create(form);",
    "    if(p && p.id) router.push(`/projects/${p.id}`);",
    "  };",
    "  return (",
    "    <form onSubmit={submit} className='max-w-2xl space-y-6'>",
    "      <SectionHeader title='Crear proyecto' description='Registra una nueva iniciativa.' />",
    "      <div className='p-6 bg-white rounded-3xl shadow-sm border space-y-4'>",
    "        <h3 className='font-black text-brand-navy'>Datos base</h3>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Título</label><input className='w-full border rounded-xl p-3 text-sm' value={form.titulo} onChange={e => setForm({...form, titulo: e.target.value})} required /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Responsable</label><input className='w-full border rounded-xl p-3 text-sm' value={form.responsable} onChange={e => setForm({...form, responsable: e.target.value})} required /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Descripción</label><textarea className='w-full border rounded-xl p-3 text-sm min-h-[100px]' value={form.descripcion} onChange={e => setForm({...form, descripcion: e.target.value})} required /></div>",
    "        <div className='grid grid-cols-2 gap-4'>",
    "          <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>GitHub URL</label><input className='w-full border rounded-xl p-3 text-sm' value={form.github_url} onChange={e => setForm({...form, github_url: e.target.value})} /></div>",
    "          <div>",
    "            <label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Privacidad GitOps</label>",
    "            <select className='w-full border rounded-xl p-3 text-sm' value={form.estado} onChange={e => setForm({...form, estado: e.target.value})}>",
    "              <option value='privado'>Privado</option>",
    "              <option value='publico'>Público</option>",
    "            </select>",
    "          </div>",
    "        </div>",
    "        <h3 className='font-black text-brand-navy mt-6'>Roles Multi-Agente</h3>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol Gemini</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_gemini} onChange={e => setForm({...form, rol_gemini: e.target.value})} /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol ChatGPT</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_chatgpt} onChange={e => setForm({...form, rol_chatgpt: e.target.value})} /></div>",
    "        <div><label className='block text-xs font-bold text-brand-muted uppercase mb-1'>Rol Claude</label><input className='w-full border rounded-xl p-3 text-sm' value={form.rol_claude} onChange={e => setForm({...form, rol_claude: e.target.value})} /></div>",
    "        <Button type='submit' className='w-full mt-4'>Crear proyecto</Button>",
    "      </div>",
    "    </form>",
    "  );",
    "}"
])

# 5. FIX FRONTEND TEXT: Cambiar texto de footer en todos los archivos
for root, dirs, files in os.walk("frontend"):
    for file in files:
        if file.endswith((".tsx", ".ts", ".jsx", ".js")):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                if "ChatGPT Fullstack: FastAPI · PostgreSQL · Next.js" in content:
                    content = content.replace("ChatGPT Fullstack: FastAPI · PostgreSQL · Next.js", "https://www.victorfigueroa.cl")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"✅ Texto de pie de página actualizado en: {filepath}")
            except Exception as e:
                pass

print("✅ Operación finalizada con éxito.")
