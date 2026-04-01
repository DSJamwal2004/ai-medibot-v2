"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  sendMessage, listConversations, getConversation,
  clearToken, type ChatResponse, type Conversation
} from "@/lib/api";
import { Sidebar } from "@/components/chat/Sidebar";
import { ChatMessage, type UIMessage } from "@/components/chat/ChatMessage";
import {
  Send, Menu, Activity, Sparkles, Stethoscope, Pill, Shield
} from "lucide-react";
import clsx from "clsx";

// ── Starter prompts ───────────────────────────────────────────────────────────
const STARTERS = [
  { icon: Stethoscope, label: "Symptom check", prompt: "I have a headache and fever for two days" },
  { icon: Pill, label: "Medication query", prompt: "Can I take ibuprofen with paracetamol?" },
  { icon: Shield, label: "What are red flags?", prompt: "What are the warning signs of a stroke?" },
  { icon: Sparkles, label: "General guidance", prompt: "When should I see a doctor for a cold?" },
];

export default function ChatPage() {
  const router = useRouter();
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<number | undefined>();
  const [messages, setMessages] = useState<UIMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Load conversations on mount
  useEffect(() => {
    listConversations()
      .then(setConversations)
      .catch(() => { clearToken(); router.push("/login"); });
  }, [router]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  const loadConversation = useCallback(async (id: number) => {
    setActiveId(id);
    try {
      const conv = await getConversation(id);
      const mapped: UIMessage[] = conv.messages.map(m => ({
        id: String(m.id),
        role: m.role as "user" | "assistant",
        content: m.content,
      }));
      setMessages(mapped);
    } catch {
      setMessages([]);
    }
  }, []);

  function startNew() {
    setActiveId(undefined);
    setMessages([]);
  }

  function handleDelete(id: number) {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (activeId === id) startNew();
  }

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  async function submitMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;

    setInput("");
    setSending(true);

    const userMsg: UIMessage = { id: crypto.randomUUID(), role: "user", content: trimmed };
    const typingId = crypto.randomUUID();
    const typingMsg: UIMessage = { id: typingId, role: "assistant", content: "", isTyping: true };

    setMessages(prev => [...prev, userMsg, typingMsg]);

    try {
      const res: ChatResponse = await sendMessage(trimmed, activeId);
      setActiveId(res.conversation_id);

      const assistantMsg: UIMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.advice,
        structuredData: res,
      };

      setMessages(prev => prev.filter(m => m.id !== typingId).concat(assistantMsg));

      // Refresh sidebar list
      listConversations().then(setConversations).catch(() => {});
    } catch (err: any) {
      setMessages(prev => prev.filter(m => m.id !== typingId).concat({
        id: crypto.randomUUID(),
        role: "assistant",
        content: `Something went wrong: ${err.message ?? "Please try again."}`,
      }));
    } finally {
      setSending(false);
      textareaRef.current?.focus();
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitMessage(input);
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-screen bg-[#0f1117] overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={loadConversation}
        onNew={startNew}
        onDelete={handleDelete}
        onLogout={handleLogout}
        mobileOpen={sidebarOpen}
        onMobileClose={() => setSidebarOpen(false)}
      />

      {/* Main area */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Top bar */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-[#1e2535] bg-[#0f1117]/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-1.5 rounded-lg hover:bg-[#1e2535] text-slate-500 hover:text-slate-300 transition-colors">
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-medium text-slate-300">
                {activeId
                  ? conversations.find(c => c.id === activeId)?.title ?? "Conversation"
                  : "New conversation"
                }
              </span>
            </div>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-emerald-400 font-medium">AI Active</span>
          </div>
        </header>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto">
          {isEmpty ? (
            // ── Empty state ─────────────────────────────────────────────────
            <div className="flex flex-col items-center justify-center h-full px-4 py-12 text-center">
              <div className="w-14 h-14 rounded-2xl bg-blue-500/15 border border-blue-500/25 flex items-center justify-center mb-5">
                <Activity className="w-7 h-7 text-blue-400" />
              </div>
              <h2 className="text-xl font-semibold text-slate-200 mb-2">How can I help you today?</h2>
              <p className="text-sm text-slate-500 max-w-md mb-8 leading-relaxed">
                Describe your symptoms for a structured assessment, or ask a general medical question.
              </p>

              {/* Starter prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-lg">
                {STARTERS.map(({ icon: Icon, label, prompt }) => (
                  <button key={label} onClick={() => submitMessage(prompt)}
                    className="flex items-center gap-3 p-3.5 rounded-xl border border-[#1e2535] bg-[#161b27] hover:bg-[#1a2236] hover:border-blue-500/25 text-left transition-all group">
                    <div className="w-8 h-8 rounded-lg bg-[#1e2535] group-hover:bg-blue-500/15 flex items-center justify-center flex-shrink-0 transition-colors">
                      <Icon className="w-4 h-4 text-slate-400 group-hover:text-blue-400 transition-colors" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-slate-300">{label}</p>
                      <p className="text-xs text-slate-600 mt-0.5 line-clamp-1">{prompt}</p>
                    </div>
                  </button>
                ))}
              </div>

              <p className="mt-10 text-xs text-slate-700 max-w-sm leading-relaxed">
                AI MediBot provides general health information only. For emergencies, call 112 / 911.
                Not a substitute for professional medical advice.
              </p>
            </div>
          ) : (
            // ── Message thread ──────────────────────────────────────────────
            <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">
              {messages.map(msg => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* Input area */}
        <div className="flex-shrink-0 border-t border-[#1e2535] bg-[#0f1117]/90 backdrop-blur-sm px-4 py-4">
          <div className="max-w-3xl mx-auto">
            <div className={clsx(
              "flex items-end gap-3 rounded-2xl border bg-[#161b27] px-4 py-3 transition-all",
              sending ? "border-[#1e2535]" : "border-[#1e2535] focus-within:border-blue-500/40 focus-within:ring-1 focus-within:ring-blue-500/20"
            )}>
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={sending}
                rows={1}
                placeholder="Describe your symptoms or ask a medical question…"
                className="flex-1 resize-none bg-transparent text-sm text-slate-200 placeholder:text-slate-600 focus:outline-none leading-relaxed disabled:opacity-50 max-h-40"
              />
              <button
                onClick={() => submitMessage(input)}
                disabled={!input.trim() || sending}
                className={clsx(
                  "flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all",
                  input.trim() && !sending
                    ? "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20"
                    : "bg-[#1e2535] text-slate-600 cursor-not-allowed"
                )}
              >
                {sending ? (
                  <span className="w-4 h-4 border-2 border-slate-600 border-t-slate-300 rounded-full animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </button>
            </div>
            <p className="text-center text-xs text-slate-700 mt-2.5">
              Enter to send · Shift+Enter for new line · Not a substitute for medical advice
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
