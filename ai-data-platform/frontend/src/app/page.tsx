"use client";

import { useState, useRef, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import ChatMessage from "@/components/ChatMessage";
import DataTable from "@/components/DataTable";
import SqlPreview from "@/components/SqlPreview";
import Dashboard from "@/components/Dashboard";
import SqlLab from "@/components/SqlLab";
import Alerts from "@/components/Alerts";
import Settings from "@/components/Settings";
import { Message, ChatResponse } from "@/types";
import {
  Send,
  Loader2,
  Database,
  Sparkles,
} from "lucide-react";

const API_BASE = "";

export default function Home() {
  const [activeTab, setActiveTab] = useState("chat");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "你好！我是你的AI数据分析助手。我可以帮你查询数据、分析趋势、发现异常。请直接告诉我你想分析什么？",
      type: "text",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      type: "text",
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const history = messages
        .filter((m) => m.id !== "welcome")
        .map((m) => ({
          role: m.role,
          content: m.content,
        }));

      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMessage.content,
          history,
        }),
      });

      const data: ChatResponse = await response.json();

      // 处理HTTP错误状态或后端返回的错误
      if (!response.ok || data.error) {
        const errorContent = data.error
          ? `分析失败: ${data.error}`
          : "抱歉，服务暂时不可用，请稍后重试。";
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: errorContent,
          type: "text",
        };
        setMessages((prev) => [...prev, errorMessage]);
        return;
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.analysis || "分析完成，但未返回具体内容。",
        type: data.type || "text",
        sql: data.sql,
        data: data.data,
        columns: data.columns,
        rowCount: data.row_count,
        executionTime: data.execution_time,
        suggestions: data.suggestions,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "抱歉，请求失败，请检查后端服务是否正常运行。",
        type: "text",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
  };

  return (
    <div className="flex h-screen bg-[#F5F7FA]">
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activeTab={activeTab}
        onTabChange={(tab) => {
          console.log("Tab changed to:", tab);
          setActiveTab(tab);
        }}
      />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-white border-b border-[#E2E8F0] flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-[#0EA5E9]" />
            <h1 className="text-lg font-semibold text-[#1E293B]">AI数据分析中台</h1>
          </div>
          <div className="flex items-center gap-2 text-sm text-[#64748B]">
            <Database className="w-4 h-4" />
            <span>MySQL只读从库</span>
            <span className="w-2 h-2 rounded-full bg-[#10B981]"></span>
          </div>
        </header>
        <main key={activeTab} className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {activeTab === "chat" && (
            <>
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div key={message.id}>
                    <ChatMessage message={message} />
                    {message.type === "data" && message.data && message.columns && (
                      <div className="ml-12 mt-2">
                        <DataTable data={message.data} columns={message.columns} rowCount={message.rowCount} />
                      </div>
                    )}
                    {message.sql && (
                      <div className="ml-12 mt-2">
                        <SqlPreview sql={message.sql} executionTime={message.executionTime} />
                      </div>
                    )}
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="ml-12 mt-3 flex flex-wrap gap-2">
                        {message.suggestions.map((suggestion, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleSuggestionClick(suggestion)}
                            className="px-3 py-1.5 text-sm bg-[#E0F2FE] text-[#0EA5E9] rounded-full hover:bg-[#0EA5E9] hover:text-white transition-colors"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="flex items-center gap-2 text-[#64748B] animate-fade-in">
                    <div className="w-8 h-8 rounded-full bg-[#E0F2FE] flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-[#0EA5E9]" />
                    </div>
                    <div className="bg-white rounded-lg px-4 py-2 shadow-sm border border-[#E2E8F0]">
                      <div className="flex items-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-sm">AI正在分析数据...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
              <div className="p-4 bg-white border-t border-[#E2E8F0] shrink-0">
                <div className="max-w-4xl mx-auto">
                  <div className="flex items-end gap-2 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] p-2 focus-within:border-[#0EA5E9] focus-within:ring-1 focus-within:ring-[#0EA5E9] transition-all">
                    <textarea
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="输入你想分析的问题，例如：最近7天新注册用户有多少？"
                      className="flex-1 bg-transparent resize-none outline-none text-sm text-[#1E293B] placeholder:text-[#94A3B8] max-h-32 min-h-[40px] py-2 px-2"
                      rows={1}
                      disabled={loading}
                    />
                    <button
                      onClick={handleSend}
                      disabled={!input.trim() || loading}
                      className="p-2 rounded-lg bg-[#0EA5E9] text-white hover:bg-[#0284C7] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-xs text-[#94A3B8] mt-2 text-center">
                    AI生成的SQL会自动执行，所有操作均为只读，不会影响线上数据
                  </p>
                </div>
              </div>
            </>
          )}
          {activeTab === "dashboard" && <Dashboard />}
          {activeTab === "sql" && <SqlLab />}
          {activeTab === "alert" && <Alerts />}
          {activeTab === "settings" && <Settings />}
        </main>
      </div>
    </div>
  );
}
