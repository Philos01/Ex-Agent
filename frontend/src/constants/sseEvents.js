/**
 * Standardized SSE Event Types
 *
 * Unified event protocol between backend AgentLoop and frontend components.
 * All ReAct-related events use the `react_` prefix for backward compatibility
 * with existing frontend components.
 */

// ── Content Events ──
export const SSE_CONTENT = "content"
export const SSE_SOURCES = "sources"
export const SSE_STATE = "state"
export const SSE_COMPONENT = "component"
export const SSE_DONE = "[DONE]"
export const SSE_REASONING_CHUNK = "reasoning_chunk"
export const SSE_REACT_REASONING_CHUNK = "react_reasoning_chunk"

// ── ReAct Agent Events ──
export const SSE_REACT_THOUGHT = "react_thought"
export const SSE_REACT_THOUGHT_CHUNK = "react_thought_chunk"
export const SSE_REACT_ACTION = "react_action"
export const SSE_REACT_OBSERVATION = "react_observation"
export const SSE_REACT_FINAL_ANSWER = "react_final_answer"
export const SSE_REACT_STEPS = "react_steps"
export const SSE_REACT_ERROR = "react_error"

// ── ReAct Step Types ──
export const STEP_THOUGHT = "thought"
export const STEP_ACTION = "action"
export const STEP_OBSERVATION = "observation"
export const STEP_FINAL_ANSWER = "final_answer"

// ── ReAct Step Icons ──
export const STEP_ICONS = {
  [STEP_THOUGHT]: "lightbulb",
  [STEP_ACTION]: "build",
  [STEP_OBSERVATION]: "visibility",
  [STEP_FINAL_ANSWER]: "check_circle",
}

// ── ReAct Step Colors ──
export const STEP_COLORS = {
  [STEP_THOUGHT]: "primary",
  [STEP_ACTION]: "tertiary",
  [STEP_OBSERVATION]: "secondary",
  [STEP_FINAL_ANSWER]: "success",
}

// ── Handler Map ──
export const REACT_EVENT_HANDLERS = {
  [SSE_REACT_THOUGHT]: STEP_THOUGHT,
  [SSE_REACT_ACTION]: STEP_ACTION,
  [SSE_REACT_OBSERVATION]: STEP_OBSERVATION,
  [SSE_REACT_FINAL_ANSWER]: STEP_FINAL_ANSWER,
}
