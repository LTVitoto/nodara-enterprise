"use client";
import { useEffect, useRef, useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardTitle } from '@/components/ui/Card';
import { WS_BASE_URL } from '@/lib/env';
import { filesRepository } from '@/services/repositories';
export function MultiAgentChat({ projectId }: { projectId: string }) {
  const [input, setInput] = useState('');
  const [events, setEvents] = useState<any[]>([]);
  const [status, setStatus] = useState('closed');
  const wsRef = useRef<WebSocket | null>(null);
  useEffect(() => {
    const wsUrl = `${WS_BASE_URL}/ws/chat/${projectId}?usuario_config_id=1`;
    const socket = new WebSocket(wsUrl);
    wsRef.current = socket;
    socket.onopen = () => setStatus('open');
    socket.onclose = () => setStatus('closed');
    socket.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        setEvents(prev => [...prev, { type: raw.event, agent: raw.data?.agent, message: raw.data?.message }]);
      } catch {}
    };
    return () => socket.close();
  }, [projectId]);
  function send() {
    if (!input.trim() || !wsRef.current) return;
    wsRef.current.send(JSON.stringify({ message: input, correlation_id: crypto.randomUUID() }));
    setInput('');
  }
  const uploadFile = async (file: File) => {
    try {
      await filesRepository.upload(projectId, file);
      setInput(`[Archivo Subido: ${file.name}] Por favor analízalo.`);
    } catch(err) { console.error('Upload Error', err); }
  };
  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) uploadFile(file);
      }
    }
  };
  return (
    <div className='grid gap-6 xl:grid-cols-[1fr_300px]'>
      <Card className='min-h-[600px] flex flex-col'>
        <CardTitle eyebrow='Conversación' title='Sala de orquestación' action={<Badge>{status}</Badge>} />
        <div className='flex-1 overflow-y-auto bg-brand-soft rounded-2xl p-4 mt-4 space-y-4'>
          {events.map((e, i) => (
            <div key={i} className='bg-white p-3 rounded-xl shadow-sm'>
              <span className='font-bold text-xs text-brand-cyan uppercase'>{e.type}</span>
              {e.agent && <span className='ml-2 text-xs font-bold text-brand-navy'>[{e.agent}]</span>}
              <p className='mt-2 text-sm whitespace-pre-wrap'>{e.message}</p>
            </div>
          ))}
        </div>
        <div className='mt-4 flex gap-2 items-center'>
          <label className='cursor-pointer bg-brand-soft px-4 py-3 rounded-2xl border text-sm font-bold hover:bg-brand-border transition'>
            📎 Subir
            <input type='file' className='hidden' onChange={e => e.target.files?.[0] && uploadFile(e.target.files[0])} />
          </label>
          <input className='flex-1 rounded-2xl border px-4 py-3' placeholder='Pega (Ctrl+V) una imagen o texto...' value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} onPaste={handlePaste} />
          <Button onClick={send}>Enviar</Button>
        </div>
      </Card>
    </div>
  );
}
