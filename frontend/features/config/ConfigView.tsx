"use client";
import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardTitle } from '@/components/ui/Card';
import { SectionHeader } from '@/components/ui/SectionHeader';
import { configRepository } from '@/services/repositories';
export function ConfigView() {
  const [config, setConfig] = useState<any>(null);
  useEffect(() => { configRepository.list().then(items => setConfig(items[0] || null)); }, []);
  async function toggleAutoApprove() {
    const cid = config?.id ? config.id : 1;
    await configRepository.patch(cid, { auto_aprobar_ejecucion: !config?.auto_aprobar_ejecucion });
    setConfig({...config, auto_aprobar_ejecucion: !config?.auto_aprobar_ejecucion});
  }
  return (
    <div>
      <SectionHeader title='Configuración operacional' description='Control BYOK.' />
      <div className='grid gap-6 xl:grid-cols-[.8fr_1.2fr]'>
        <Card>
          <CardTitle eyebrow='Usuario' title={`ID ${config?.id ?? '1'}`} />
          <div className='space-y-4'>
            <div className='flex justify-between p-4 bg-brand-soft rounded-2xl'>
              <span className='font-bold'>Auto aprobar ejecución</span>
              <Badge tone={config?.auto_aprobar_ejecucion ? 'success' : 'warning'}>{config?.auto_aprobar_ejecucion ? 'ON' : 'OFF'}</Badge>
            </div>
            <Button onClick={toggleAutoApprove} className='w-full'>Alternar Auto Aprobación</Button>
          </div>
        </Card>
        <Card>
          <CardTitle eyebrow='BYOK' title='Estado de API Keys y saldos' />
          <div className='grid gap-4 md:grid-cols-3'>
            {[['OpenAI', config?.has_api_key_openai, config?.saldo_virtual_openai],
              ['Anthropic', config?.has_api_key_anthropic, config?.saldo_virtual_anthropic],
              ['Gemini', config?.has_api_key_gemini, config?.saldo_virtual_gemini]].map(([name, has, s]) => (
              <div key={String(name)} className='rounded-3xl border bg-white p-5'>
                <div className='text-lg font-black'>{String(name)}</div>
                <Badge tone={has ? 'success' : 'danger'} className='mt-3'>{has ? 'Cargada' : 'Falta Key'}</Badge>
              </div>
            ))}
            <div className='rounded-3xl border bg-white p-5 col-span-3'>
              <div className='text-lg font-black'>GitHub GitOps</div>
              <Badge tone={config?.has_api_key_github ? 'success' : 'danger'} className='mt-3'>
                {config?.has_api_key_github ? 'Token Cargado en .env' : 'Falta GITHUB_PERSONAL_ACCESS_TOKEN'}
              </Badge>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
