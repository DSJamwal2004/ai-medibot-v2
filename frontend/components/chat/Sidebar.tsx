"use client";
import { useState } from "react";
import type { Conversation } from "@/lib/api";
import { deleteConversation } from "@/lib/api";
import {
  Plus, MessageSquare, Trash2, Activity, LogOut, X
} from "lucide-react";
import clsx from "clsx";

interface Props {
  conversations: Conversation[];
  activeId: number | undefined;
  onSelect: (id: number) => void;
  onNew: () => void;
  onDelete: (id: number) => void;
  onLogout: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

export function Sidebar({
  conversations, activeId, onSelect, onNew, onDelete, onLogout,
  mobileOpen, onMobileClose
}: Props) {
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function handleDelete(e: React.MouseEvent, id: number) {
    e.stopPropagation();
    setDeletingId(id);
    try {
      await deleteConversation(id);
      onDelete(id);
    } finally {
      setDeletingId(null);
    }
  }

  function formatDate(iso: string) {
    const d = new Date(iso);
    const now = new Date();
    const isToday = d.toDateString() === now.toDateString();
    if (isToday) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  }

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Brand */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-[#1e2535]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center">
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-100 leading-none">AI MediBot</p>
            <p className="text-xs text-slate-500 mt-0.5">v2.2</p>
          </div>
        </div>
        {/* Mobile close */}
        <button onClick={onMobileClose} className="lg:hidden text-slate-500 hover:text-slate-300">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* New chat button */}
      <div className="px-3 py-3">
        <button onClick={onNew}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl border border-blue-500/25 bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 text-sm font-medium transition-all group">
          <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform" />
          New conversation
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto px-2 pb-2 space-y-0.5">
        {conversations.length === 0 ? (
          <div className="text-center py-8 px-4">
            <MessageSquare className="w-8 h-8 text-slate-700 mx-auto mb-2" />
            <p className="text-xs text-slate-600">No conversations yet</p>
          </div>
        ) : (
          conversations.map(conv => (
            <button key={conv.id} onClick={() => { onSelect(conv.id); onMobileClose(); }}
              className={clsx(
                "w-full text-left px-3 py-2.5 rounded-xl transition-all group flex items-center justify-between gap-2",
                activeId === conv.id
                  ? "bg-blue-500/15 border border-blue-500/20 text-slate-100"
                  : "hover:bg-[#1e2535] text-slate-400 hover:text-slate-200 border border-transparent"
              )}>
              <div className="flex items-center gap-2 min-w-0">
                <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm truncate leading-snug">
                    {conv.title ?? "New conversation"}
                  </p>
                  <p className="text-xs text-slate-600 mt-0.5">{formatDate(conv.updated_at)}</p>
                </div>
              </div>
              <button
                onClick={e => handleDelete(e, conv.id)}
                disabled={deletingId === conv.id}
                className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-1 rounded-lg hover:bg-red-500/20 hover:text-red-400 transition-all text-slate-600"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </button>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-[#1e2535] px-3 py-3">
        <button onClick={onLogout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-[#1e2535] text-slate-500 hover:text-slate-300 text-sm transition-colors">
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 border-r border-[#1e2535] bg-[#0c1018] h-full">
        {sidebarContent}
      </aside>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/60" onClick={onMobileClose} />
          <aside className="relative w-72 flex flex-col bg-[#0c1018] border-r border-[#1e2535] h-full">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
