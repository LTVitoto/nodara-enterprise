export type WsEventType =
  | "orchestration_start"
  | "agent_selected"
  | "agent_message_start"
  | "agent_delta"
  | "agent_message_end"
  | "human_approval_required"
  | "tool_execution_start"
  | "tool_execution_end"
  | "agent_error"
  | "orchestration_end";

export interface WsOutboundMessage {
  message: string;
  correlation_id: string;
}

export interface WsIncomingEvent {
  type: WsEventType | string;
  correlation_id?: string;
  agent?: string;
  delta?: string;
  content?: string;
  message?: string;
  approval_id?: number;
  tool_name?: string;
  payload?: Record<string, unknown>;
  error?: string;
  timestamp?: string;
}
