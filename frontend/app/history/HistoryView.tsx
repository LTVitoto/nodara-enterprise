
'use client'
import { useEffect, useState } from 'react'

export default function HistoryView({ proyectoId }) {
  const [data, setData] = useState([])
  const [summary, setSummary] = useState(null)
  const [technical, setTechnical] = useState(false)
  const [filterAgent, setFilterAgent] = useState('all')

  useEffect(() => {
    fetch(`/api/history/${proyectoId}`)
      .then(r => r.json())
      .then(setData)

    fetch(`/api/history/summary/${proyectoId}`)
      .then(r => r.json())
      .then(setSummary)
  }, [proyectoId])

  const filtered = data.filter(m => filterAgent === 'all' || m.agente === filterAgent)

  return (
    <div>
      <h1>Historial</h1>

      {summary && (
        <div>
          <b>Costo total:</b> ${summary.total_cost_usd} |
          <b> Tokens:</b> {summary.total_tokens} |
          <b> Días:</b> {summary.duration_days}
        </div>
      )}

      <button onClick={() => setTechnical(!technical)}>Toggle Técnico</button>

      <select onChange={(e)=>setFilterAgent(e.target.value)}>
        <option value="all">Todos</option>
        <option value="gemini">Gemini</option>
        <option value="chatgpt">ChatGPT</option>
      </select>

      {filtered.map(msg => (
        <div key={msg.id} style={{border:'1px solid #ccc', margin:10, padding:10}}>
          <b>{msg.agente}</b>: {msg.content}

          {technical && (
            <pre>{JSON.stringify(msg, null, 2)}</pre>
          )}
        </div>
      ))}
    </div>
  )
}
