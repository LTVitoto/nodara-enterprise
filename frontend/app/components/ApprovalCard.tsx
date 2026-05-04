"use client";

import { approveApproval, rejectApproval } from "../lib/api";

export default function ApprovalCard({ approval, onUpdate }) {
  const handleApprove = async () => {
    await approveApproval(approval.id);
    onUpdate();
  };

  const handleReject = async () => {
    await rejectApproval(approval.id);
    onUpdate();
  };

  return (
    <div style={{
      border: "1px solid #333",
      padding: 15,
      marginBottom: 10,
      borderRadius: 8,
      background: "#1a1a2e"
    }}>
      <p><strong>ID:</strong> {approval.id}</p>
      <p><strong>Agente:</strong> {approval.agente}</p>
      <p><strong>Tool:</strong> {approval.tool_name}</p>
      <p><strong>Status:</strong> {approval.status}</p>

      <pre style={{ background: "#000", padding: 10 }}>
        {JSON.stringify(approval.arguments_json, null, 2)}
      </pre>

      {approval.status === "pending" && (
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={handleApprove} style={{ background: "green" }}>
            Aprobar
          </button>
          <button onClick={handleReject} style={{ background: "red" }}>
            Rechazar
          </button>
        </div>
      )}
    </div>
  );
}