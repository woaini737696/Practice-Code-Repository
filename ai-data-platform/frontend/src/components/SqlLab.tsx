"use client";

import { useState } from "react";
import { Play, Save, Clock, Database } from "lucide-react";
import DataTable from "./DataTable";

interface QueryHistory {
  id: string;
  sql: string;
  timestamp: string;
  status: "success" | "error";
}

export default function SqlLab() {
  const [sql, setSql] = useState("SELECT * FROM users LIMIT 10");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    data: Record<string, unknown>[];
    columns: string[];
    rowCount: number;
    executionTime: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryHistory[]>([
    { id: "1", sql: "SELECT COUNT(*) FROM users", timestamp: "10:30", status: "success" },
    { id: "2", sql: "SELECT * FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)", timestamp: "10:15", status: "success" },
  ]);
  const [savedQueries, setSavedQueries] = useState([
    { id: "1", name: "每日新用户", sql: "SELECT DATE(created_at), COUNT(*) FROM users GROUP BY DATE(created_at)" },
    { id: "2", name: "活跃用户统计", sql: "SELECT COUNT(*) FROM users WHERE last_active >= DATE_SUB(NOW(), INTERVAL 7 DAY)" },
  ]);

  const executeQuery = async () => {
    if (!sql.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/ai-data/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql: sql.trim() }),
      });
      const data = await response.json();

      if (data.success) {
        setResult({
          data: data.data || [],
          columns: data.columns || [],
          rowCount: data.row_count || 0,
          executionTime: data.execution_time || 0,
        });
        setHistory((prev) => [
          { id: Date.now().toString(), sql: sql.trim(), timestamp: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }), status: "success" },
          ...prev.slice(0, 19),
        ]);
      } else {
        setError(data.error || "查询执行失败");
        setHistory((prev) => [
          { id: Date.now().toString(), sql: sql.trim(), timestamp: new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" }), status: "error" },
          ...prev.slice(0, 19),
        ]);
      }
    } catch {
      setError("网络请求失败，请检查后端服务");
    } finally {
      setLoading(false);
    }
  };

  const saveQuery = () => {
    if (!sql.trim()) return;
    const name = prompt("给这条SQL起个名字：");
    if (name) {
      setSavedQueries((prev) => [...prev, { id: Date.now().toString(), name, sql }]);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
      <div className="flex-1 flex">
        {/* 左侧边栏 */}
        <div className="w-64 bg-white border-r border-[#E2E8F0] flex flex-col">
          <div className="p-4 border-b border-[#E2E8F0]">
            <h3 className="text-sm font-medium text-[#1E293B] flex items-center gap-2">
              <Database className="w-4 h-4 text-[#0EA5E9]" />
              表结构
            </h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {["users", "orders", "products", "payments", "logs"].map((table) => (
              <div key={table} className="px-3 py-2 rounded-lg hover:bg-[#F8FAFC] cursor-pointer text-sm text-[#1E293B]">
                {table}
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-[#E2E8F0]">
            <h3 className="text-sm font-medium text-[#1E293B] mb-2">已保存查询</h3>
            <div className="space-y-1">
              {savedQueries.map((q) => (
                <div
                  key={q.id}
                  onClick={() => setSql(q.sql)}
                  className="px-2 py-1.5 rounded text-xs text-[#64748B] hover:bg-[#F8FAFC] hover:text-[#0EA5E9] cursor-pointer truncate"
                >
                  {q.name}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 主区域 */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* SQL编辑器 */}
          <div className="p-4 border-b border-[#E2E8F0] bg-white">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-[#1E293B]">SQL编辑器</span>
              <div className="flex items-center gap-2">
                <button
                  onClick={saveQuery}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs bg-white border border-[#E2E8F0] rounded-lg hover:bg-[#F8FAFC] transition-colors"
                >
                  <Save className="w-3.5 h-3.5" />
                  保存
                </button>
                <button
                  onClick={executeQuery}
                  disabled={loading}
                  className="flex items-center gap-1 px-3 py-1.5 text-xs bg-[#0EA5E9] text-white rounded-lg hover:bg-[#0284C7] disabled:opacity-50 transition-colors"
                >
                  <Play className="w-3.5 h-3.5" />
                  {loading ? "执行中..." : "执行"}
                </button>
              </div>
            </div>
            <textarea
              value={sql}
              onChange={(e) => setSql(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && e.ctrlKey) {
                  e.preventDefault();
                  executeQuery();
                }
              }}
              placeholder="输入SQL查询语句..."
              className="w-full h-32 bg-[#1E293B] text-[#E2E8F0] rounded-lg p-3 font-mono text-sm outline-none focus:ring-2 focus:ring-[#0EA5E9] resize-none"
              spellCheck={false}
            />
            <p className="text-xs text-[#94A3B8] mt-1">提示：仅支持SELECT查询，Ctrl+Enter快速执行</p>
          </div>

          {/* 结果区域 */}
          <div className="flex-1 overflow-y-auto p-4">
            {loading && (
              <div className="flex items-center justify-center py-12">
                <div className="flex items-center gap-2 text-[#64748B]">
                  <Clock className="w-4 h-4 animate-spin" />
                  <span className="text-sm">正在执行查询...</span>
                </div>
              </div>
            )}

            {error && (
              <div className="bg-[#FEF2F2] border border-[#FECACA] rounded-xl p-4 mb-4">
                <p className="text-sm text-[#DC2626]">{error}</p>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                <div className="flex items-center gap-4 text-xs text-[#64748B]">
                  <span>返回 {result.rowCount} 条数据</span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    执行时间 {result.executionTime}s
                  </span>
                </div>
                <DataTable data={result.data} columns={result.columns} rowCount={result.rowCount} />
              </div>
            )}

            {!loading && !error && !result && (
              <div className="flex items-center justify-center py-12 text-[#94A3B8]">
                <div className="text-center">
                  <Database className="w-12 h-12 mx-auto mb-3 text-[#CBD5E1]" />
                  <p className="text-sm">输入SQL查询并点击执行</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 右侧历史 */}
        <div className="w-56 bg-white border-l border-[#E2E8F0] flex flex-col">
          <div className="p-4 border-b border-[#E2E8F0]">
            <h3 className="text-sm font-medium text-[#1E293B]">查询历史</h3>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {history.map((h) => (
              <div
                key={h.id}
                onClick={() => setSql(h.sql)}
                className="px-3 py-2 rounded-lg hover:bg-[#F8FAFC] cursor-pointer mb-1"
              >
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${h.status === "success" ? "bg-[#10B981]" : "bg-[#EF4444]"}`} />
                  <span className="text-xs text-[#94A3B8]">{h.timestamp}</span>
                </div>
                <p className="text-xs text-[#1E293B] mt-1 truncate font-mono">{h.sql}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
