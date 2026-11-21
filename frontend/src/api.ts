// Thin typed client for the SHIFTTRACE console API.

export type Json = Record<string, unknown>;

export interface Asset {
  asset_id: string; name: string; asset_type: string; manufacturer: string; model: string; serial_no: string;
  location: string; status: string; criticality: string; metadata: Json;
  open_work_orders?: number; open_loops?: number;
  latest_handoff?: { handoff_id: string; created_at: string; created_by: string } | null;
}
export interface WorkOrderLog { id: number; ts: string; author: string; status_from: string | null; status_to: string | null; note: string; session_id: string | null; via: string }
export interface WorkOrder { work_order_id: string; asset_id: string; title: string; description: string; priority: string; status: string; assigned_to: string; created_at: string; updated_at: string; log: WorkOrderLog[] }
export interface Evidence {
  id: number; session_id: string | null; asset_id: string; ts: string; event_type: string; source_type: string;
  title: string; detail: string | null; payload: Json | null; model_id: string | null; status: string | null;
  verified_by: string | null; media_ref: string | null; related_id: number | null; raised_by_technician?: string;
}
export interface ToolAction { id: number; session_id: string | null; ts: string; tool_name: string; caller: string; input: Json; result: Json | null; status: string; duration_ms: number }
export interface Transcript { id: number; session_id: string; ts: string; role: "user" | "agent"; turn_id: string; text: string }
export interface Procurement {
  request_id: string; part_id: string; part_name: string; quantity: number; work_order_id: string | null; session_id: string | null;
  status: string; reason: string | null; created_by: string; approved_by: string | null; approval_via: string | null;
  approval_evidence: string | null; supplier: string; expected_by: string | null; supplier_ref: string | null;
  failure_reason: string | null; created_at: string; decided_at: string | null;
}
export interface SessionRow { session_id: string; asset_id: string; technician: string; shift_label: string; started_at: string; ended_at: string | null; status: string; agent_id: string | null; summary: string | null; task_id?: string | null }
export interface Task { id: string; label: string; summary: string; goal: string; procedure: string[]; restricted_tools: string[] | null; read_only?: boolean }
export interface Transfer { transfer_id: string; part_id: string; part_name: string; quantity: number; from_location: string; to_location: string; reason: string | null; status: string; session_id: string | null; created_by: string; confirmed_by: string | null; confirmation_via: string | null; confirmation_evidence: string | null; erp_ref: string | null; failure_reason: string | null; created_at: string; decided_at: string | null }
export interface FollowUp { follow_up_id: string; title: string; due_text: string | null; due_date: string | null; assignee: string; asset_id: string; session_id: string | null; created_by: string; status: string; created_at: string; calendar?: { google_calendar?: string; outlook_calendar?: string } }
export interface TaskList { asset_id: string | null; default: string; tasks: Task[] }
export interface Pack { id: string; name: string; description: string; loaded: boolean; assets: string[] }
export interface SessionDetail extends SessionRow {
  channel: string | null; voice_running: boolean; agent_config: Json | null; task: Task | null;
  evidence: Evidence[]; tool_actions: ToolAction[]; transcripts: Transcript[]; procurement: Procurement[];
  handoff: Handoff | null;
  transfers?: Transfer[]; follow_ups?: FollowUp[];
}
export interface HandoffReport {
  schema: string; headline: string; spoken_summary: string; generated_by: string; carried_over_from?: string | null;
  task?: { id: string; label: string } | null;
  asset: { asset_id: string; name: string; model: string; location: string };
  session: { session_id: string; technician: string; shift: string; started_at: string; ended_at: string | null };
  work_order: { work_order_id: string; status: string; priority: string; title: string } | null;
  observations: { event_id?: number; ts?: string; text: string; detail?: string | null; source: string; model_id?: string | null; status?: string | null; media_ref?: string | null; verified_by?: string }[];
  records_consulted?: { tool: string; input: Json; ts: string }[];
  actions_completed: { text: string; ref?: string | null; verified?: boolean; detail?: string }[];
  actions_failed_or_pending: { text: string; ref?: string | null; detail?: string | null; status?: string }[];
  parts: { part_id: string; name: string; state: string; ref: string | null }[];
  ruled_out: { event_id?: number; text: string; reason?: string }[];
  confirmed?: { event_id?: number; text: string; status?: string }[];
  open_loops: { event_id?: number; text: string; type: string; raised_by?: string; since?: string }[];
  suggested_next_steps: string[];
  follow_ups?: { follow_up_id: string; title: string; due: string | null; assignee: string }[];
  manual_refs: string[];
}
export interface Handoff { handoff_id: string; asset_id: string; session_id: string | null; created_at: string; created_by: string; report: HandoffReport; status: string }
export interface Part { part_id: string; name: string; on_hand: number; reserved: number; available: number; in_stock: boolean; location: string; lead_time_days: number; supplier: string; compatible_models: string; open_procurement_requests: Json[] }
export interface Health {
  ok: boolean; agora_credentials: boolean; murf_key: boolean; mcp_public_url: string | null; llm_model: string; murf_voice_id: string;
  tunnel: { mode: string; url: string | null; self_test: boolean | null; healthy: boolean | null; checked_at: number | null; restarts: number; error: string | null };
  active_agents: string[];
}
export interface VoiceCreds { agent_id: string; channel: string; user_uid: number; agent_uid: number; app_id: string; token: string }
export interface StartResult { session_id: string; asset_id: string; task_id?: string; voice: VoiceCreds | null; voice_error: string | null }

async function req<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: body !== undefined ? { "content-type": "application/json" } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail = data?.detail ?? data;
    throw new Error(typeof detail === "string" ? detail : detail?.message ?? `HTTP ${res.status}`);
  }
  return data as T;
}

export const api = {
  get: <T,>(url: string) => req<T>("GET", url),
  post: <T,>(url: string, body: unknown = {}) => req<T>("POST", url, body),
  startSession: (asset_id: string, technician: string, shift_label: string, voice: boolean, task_id?: string) =>
    req<StartResult>("POST", "/api/sessions", { asset_id, technician, shift_label, voice, task_id }),
  tool: (tool: string, session_id: string | null, args: Json) => req<Json>("POST", "/api/console/tool", { tool, session_id, args }),
};

export const media = (name: string) => `/api/media/${encodeURIComponent(name)}`;

export function fmtTime(ts: string | null | undefined): string {
  if (!ts) return "";
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23" });
}
export function fmtDateTime(ts: string | null | undefined): string {
  if (!ts) return "";
  const d = new Date(ts);
  const today = new Date();
  const sameDay = d.toDateString() === today.toDateString();
  const yest = new Date(today.getTime() - 86400000).toDateString() === d.toDateString();
  const day = sameDay ? "Today" : yest ? "Yesterday" : d.toLocaleDateString([], { day: "2-digit", month: "short" });
  return `${day} ${d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hourCycle: "h23" })}`;
}

/** 24-hour clock for the log margin (plants run on 24-hour time). */
export function hhmm(ts: string | number | null | undefined): string {
  if (ts === null || ts === undefined || ts === "") return "";
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
}
/** Short day for shift bands: "Today", "Yesterday" or "Fri 20 Nov". */
export function dayLabel(ts: string | null | undefined): string {
  if (!ts) return "";
  const d = new Date(ts); const today = new Date();
  if (d.toDateString() === today.toDateString()) return "Today";
  if (new Date(today.getTime() - 86400000).toDateString() === d.toDateString()) return "Yesterday";
  return d.toLocaleDateString([], { weekday: "short", day: "numeric", month: "short" });
}
