"use client";

import { User, Sparkles } from "lucide-react";
import { Message } from "@/types";

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} animate-fade-in`}>
      {/* AI头像 */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-[#E0F2FE] flex items-center justify-center shrink-0">
          <Sparkles className="w-4 h-4 text-[#0EA5E9]" />
        </div>
      )}

      {/* 消息内容 */}
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-[#0EA5E9] text-white rounded-br-md"
            : "bg-white border border-[#E2E8F0] text-[#1E293B] rounded-bl-md shadow-sm"
        }`}
      >
        <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
      </div>

      {/* 用户头像 */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-[#1E293B] flex items-center justify-center shrink-0">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  );
}
