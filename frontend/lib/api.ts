/**
 * Typed API client for AI MediBot v2.2
 * All backend calls go through these functions — no fetch() scattered in components.
 */

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API = `${BASE}/api/v1`;

// ── Token storage ─────────────────────────────────────────────────────────────

export function setToken(t: string) {
  if (typeof window !== "undefined") localStorage.setItem("mb_token", t);
}
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mb_token");
}
export function clearToken() {
  if (typeof window !== "undefined") localStorage.removeItem("mb_token");
}

// ── Base fetch ────────────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  auth = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Symptom {
  name: string;
  raw: string;
  duration?: string | null;
  severity?: string | null;
}

export interface Condition {
  name: string;
  confidence: number;
  reasoning: string;
}

export interface Citation {
  document_id: number;
  title: string;
  source?: string | null;
  medical_domain?: string | null;
  authority_level: number;
  score: number;
}

export type RiskLevel = "low" | "medium" | "high";
export type Urgency = "none" | "consult_doctor" | "emergency";

export interface ChatResponse {
  conversation_id: number;
  message_id: number;
  symptoms: Symptom[];
  risk_level: RiskLevel;
  conditions: Condition[];
  advice: string;
  immediate_steps: string[];
  when_to_seek_care: string;
  should_escalate: boolean;
  urgency: Urgency;
  red_flags_triggered: string[];
  explanation: string;
  key_factors: string[];
  confidence_score: number;
  citations: Citation[];
  rag_used: boolean;
  llm_provider: string;
}

export interface Conversation {
  id: number;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

// ── Auth endpoints ────────────────────────────────────────────────────────────

export async function register(email: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }, false);
  setToken(data.access_token);
  return data;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const data = await apiFetch<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }, false);
  setToken(data.access_token);
  return data;
}

// ── Chat endpoints ────────────────────────────────────────────────────────────

export async function sendMessage(
  message: string,
  conversation_id?: number
): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversation_id }),
  });
}

// ── Conversation endpoints ────────────────────────────────────────────────────

export async function listConversations(): Promise<Conversation[]> {
  return apiFetch<Conversation[]>("/conversations");
}

export async function getConversation(id: number): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(`/conversations/${id}`);
}

export async function deleteConversation(id: number): Promise<void> {
  return apiFetch<void>(`/conversations/${id}`, { method: "DELETE" });
}
