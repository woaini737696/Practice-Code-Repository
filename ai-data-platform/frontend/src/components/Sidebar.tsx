"use client";

import {
  MessageSquare,
  LayoutDashboard,
  Database,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const menuItems = [
  { id: "chat", icon: MessageSquare, label: "AI对话分析" },
  { id: "dashboard", icon: LayoutDashboard, label: "数据看板" },
  { id: "sql", icon: Database, label: "SQL实验室" },
  { id: "alert", icon: Bell, label: "监控告警" },
  { id: "settings", icon: Settings, label: "系统设置" },
];

export default function Sidebar({ isOpen, onToggle, activeTab, onTabChange }: SidebarProps) {
  return (
    <aside
      className={`bg-[#1E293B] text-white transition-all duration-300 flex flex-col ${
        isOpen ? "w-56" : "w-16"
      }`}
    >
      {/* Logo区域 */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-white/10">
        {isOpen && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#0EA5E9] flex items-center justify-center">
              <span className="text-sm font-bold">AI</span>
            </div>
            <span className="font-semibold text-sm">数据助理</span>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1 rounded hover:bg-white/10 transition-colors"
        >
          {isOpen ? (
            <ChevronLeft className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* 菜单 */}
      <nav className="flex-1 py-4">
        {menuItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 transition-colors cursor-pointer ${
                isActive
                  ? "bg-[#0EA5E9]/20 text-[#0EA5E9] border-r-2 border-[#0EA5E9]"
                  : "text-[#94A3B8] hover:bg-white/5 hover:text-white"
              }`}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {isOpen && <span className="text-sm">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* 底部信息 */}
      {isOpen && (
        <div className="p-4 border-t border-white/10">
          <div className="text-xs text-[#64748B]">
            <p>v1.0.0 MVP</p>
            <p className="mt-1">本地开发环境</p>
          </div>
        </div>
      )}
    </aside>
  );
}
