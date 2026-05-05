"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLogo } from "@/components/layout/BrandLogo";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";
import { DATA_MODE } from "@/lib/env";

const nav = [
  { href: "/", label: "Dashboard", sprint: 1 },
  { href: "/config", label: "Configuración", sprint: 1 },
  { href: "/projects", label: "Proyectos", sprint: 1 },
  { href: "/approvals", label: "Aprobaciones", sprint: 1 },
  { href: "/files", label: "Archivos", sprint: 1 },
  { href: "/messages", label: "Historial", sprint: 2 },
  { href: "/tools", label: "Tools", sprint: 2 },
  { href: "/agents", label: "Agentes", sprint: 3 },
  { href: "/metrics", label: "Métricas", sprint: 3 },
  { href: "/workspace", label: "Workspace", sprint: 3 },
  { href: "/github", label: "GitHub", sprint: 4 },
  { href: "/audit", label: "Auditoría", sprint: 4 }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-brand-soft text-brand-navy">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-80 flex-col border-r border-white/10 bg-brand-deep text-white shadow-panel xl:flex">
        <div className="border-b border-white/10 p-6">
          <BrandLogo compact />
          <div className="mt-5 flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-brand-cyan pulse-cyan" />
            <span className="text-xs font-black uppercase tracking-[0.22em] text-brand-bright">AI Control Tower</span>
          </div>
        </div>
        <nav className="vf-scrollbar flex-1 space-y-1 overflow-y-auto p-4">
          {nav.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-bold transition",
                  active ? "bg-brand-cyan text-brand-deep shadow-cyan" : "text-white/75 hover:bg-white/10 hover:text-white"
                )}
              >
                <span>{item.label}</span>
                
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-white/10 p-5">
          <p className="text-xs leading-5 text-white/60">Victor Figueroa · Arquitecto de Soluciones</p>
          <p className="mt-1 text-xs text-brand-bright"><a href='https://www.victorfigueroa.cl' target='_blank' rel='noopener noreferrer' className='text-brand-cyan hover:underline font-bold transition-all'>Victor Figueroa</a></p>
        </div>
      </aside>

      <main className="xl:pl-80">
        <header className="sticky top-0 z-20 border-b border-brand-border bg-white/85 px-5 py-4 backdrop-blur xl:px-10">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-4 xl:hidden"><BrandLogo compact /></div>
            <div className="hidden xl:block">
              <p className="text-xs font-black uppercase tracking-[0.24em] text-brand-cyan">Orquestador Multi-Agente</p>
              <p className="text-sm text-brand-muted">Sala enterprise para Gemini Infra y ChatGPT Fullstack.</p>
            </div>
            
          </div>
        </header>
        <div className="vf-grid-bg min-h-[calc(100vh-80px)] p-5 md:p-8 xl:p-10">{children}</div>
      </main>
    </div>
  );
}
