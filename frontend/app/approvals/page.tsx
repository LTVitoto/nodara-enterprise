"use client";

import { useEffect, useState } from "react";
import ApprovalCard from "../components/ApprovalCard";
import { getApprovals } from "../lib/api";

export default function ApprovalsPage() {

  const [approvals, setApprovals] = useState([]);
  const [filter, setFilter] = useState("pending");
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    const data = await getApprovals(filter === "all" ? undefined : filter);
    setApprovals(data);
    setLoading(false);
  };

  useEffect(() => {
    loadData();

    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);

  }, [filter]);

  return (
    <div style={{ padding: 20, background: "#0f172a", minHeight: "100vh", color: "white" }}>

      <h1 style={{ color: "#38bdf8" }}>Aprobaciones (HIL)</h1>

      {/* FILTROS */}
      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        <button onClick={() => setFilter("pending")}>Pendientes</button>
        <button onClick={() => setFilter("approved")}>Aprobadas</button>
        <button onClick={() => setFilter("rejected")}>Rechazadas</button>
        <button onClick={() => setFilter("all")}>Todas</button>
      </div>

      {/* METRICS */}
      <div style={{ marginBottom: 20 }}>
        <p>Total: {approvals.length}</p>
      </div>

      {/* LISTA */}
      {loading ? (
        <p>Cargando...</p>
      ) : approvals.length === 0 ? (
        <p>No hay resultados</p>
      ) : (
        approvals.map((a) => (
          <ApprovalCard key={a.id} approval={a} onUpdate={loadData} />
        ))
      )}
    </div>
  );
}