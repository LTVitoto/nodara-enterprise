from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CircuitBreaker:
    max_agent_steps: int = 8
    max_tool_calls: int = 5
    step_count: int = 0
    tool_call_count: int = 0
    seen_signatures: set[str] = field(default_factory=set)

    def register_agent_step(self, signature: str) -> None:
        self.step_count += 1
        if self.step_count > self.max_agent_steps:
            raise RuntimeError("Circuit Breaker: límite de pasos entre agentes alcanzado")
        if signature in self.seen_signatures:
            raise RuntimeError("Circuit Breaker: posible bucle repetitivo detectado")
        self.seen_signatures.add(signature)

    def register_tool_call(self) -> None:
        self.tool_call_count += 1
        if self.tool_call_count > self.max_tool_calls:
            raise RuntimeError("Circuit Breaker: límite de tool calls alcanzado")
