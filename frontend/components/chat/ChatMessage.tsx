import type { ChatResponse } from "@/lib/api";
import { ResponseCard } from "@/components/chat/ResponseCard";
import { TypingIndicator } from "@/components/ui/TypingIndicator";
import { User, Bot } from "lucide-react";
import clsx from "clsx";

export interface UIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  isTyping?: boolean;
  structuredData?: ChatResponse;
}

interface Props {
  message: UIMessage;
}

export function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end items-end gap-2.5 animate-fade-up">
        <div className="max-w-[75%] rounded-2xl rounded-br-sm bg-blue-600 px-4 py-2.5">
          <p className="text-sm text-white leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
        <div className="w-7 h-7 rounded-full bg-[#1e2535] border border-[#252d3d] flex items-center justify-center flex-shrink-0">
          <User className="w-3.5 h-3.5 text-slate-400" />
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex justify-start items-start gap-2.5 animate-fade-up">
      <div className="w-7 h-7 rounded-full bg-blue-500/15 border border-blue-500/25 flex items-center justify-center flex-shrink-0 mt-1">
        <Bot className="w-3.5 h-3.5 text-blue-400" />
      </div>

      <div className="flex-1 max-w-[85%] space-y-2">
        {message.isTyping ? (
          <div className="rounded-2xl rounded-bl-sm border border-[#1e2535] bg-[#161b27]">
            <TypingIndicator />
          </div>
        ) : message.structuredData ? (
          <ResponseCard data={message.structuredData} />
        ) : (
          <div className="rounded-2xl rounded-bl-sm border border-[#1e2535] bg-[#161b27] px-4 py-3">
            <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap prose-chat">
              {message.content}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
