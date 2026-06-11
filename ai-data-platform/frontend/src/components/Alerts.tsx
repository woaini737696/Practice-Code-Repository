"use client";

import { useState } from "react";
import {
  Bell,
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from "lucide-react";

interface AlertRule {
  id: string;
  name: string;
  metric: string;
  condition: string;
  threshold: string;
  status: "active" | "paused";
  lastTriggered?: string;
}

interface AlertLog {
  id: string;
  ruleName: string;
  message: string;
  severity: "high" | "medium" | "low";
  timestamp: string;
  status: "resolved" | "pending";
}

export default function Alerts() {
  const [rules, setRules] = useState<AlertRule[]>([
    {
      id: "1",
      name: "日活跃用户下降预警",
      metric: "DAU",
      condition: "低于",
      threshold: "1000",
      status: "active",
      lastTriggered: "2024-01-15 08:30",
    },
    {
      id: "2",
      name: "新用户注册异常",
      metric: "日注册量",
      condition: "低于",
      threshold: "50",
      status: "active",
    },
    {
      id: "3",
      name: "收入波动监控",
      metric: "日收入",
      condition: "下降超过",
      threshold: "20%",
      status: "paused",
    },
  ]);

  const [logs] = useState<AlertLog[]>([
    {
      id: "1",
      ruleName: "日活跃用户下降预警",
      message: "今日DAU为892，低于阈值1000",
      severity: "high",
      timestamp: "2024-01-15 08:30",
      status: "pending",
    },
    {
      id: "2",
      ruleName: "新用户注册异常",
      message: "昨日新注册32人，低于平均值50%",
      severity: "medium",
      timestamp: "2024-01-14 09:15",
      status: "resolved",
    },
    {
      id: "3",
      ruleName: "收入波动监控",
      message: "昨日收入环比下降25%",
      severity: "low",
      timestamp: "2024-01-13 10:00",
      status: "resolved",
    },
  ]);

  const [showAddModal, setShowAddModal] = useState(false);
  const [newRule, setNewRule] = useState({
    name: "",
    metric: "DAU",
    condition: "低于",
    threshold: "",
  });

  const addRule = () => {
    if (!newRule.name || !newRule.threshold) return;
    setRules((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        name: newRule.name,
        metric: newRule.metric,
        condition: newRule.condition,
        threshold: newRule.threshold,
        status: "active",
      },
    ]);
    setNewRule({ name: "", metric: "DAU", condition: "低于", threshold: "" });
    setShowAddModal(false);
  };

  const toggleRuleStatus = (id: string) => {
    setRules((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: r.status === "active" ? "paused" : "active" } : r))
    );
  };

  const deleteRule = (id: string) => {
    if (confirm("确定删除这条告警规则吗？")) {
      setRules((prev) => prev.filter((r) => r.id !== id));
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "bg-[#FEF2F2] text-[#DC2626] border-[#FECACA]";
      case "medium":
        return "bg-[#FEF3C7] text-[#D97706] border-[#FDE68A]";
      case "low":
        return "bg-[#E0F2FE] text-[#0284C7] border-[#BAE6FD]";
      default:
        return "bg-[#F1F5F9] text-[#64748B]";
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      {/* 顶部 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-[#1E293B]">监控告警</h2>
          <p className="text-sm text-[#64748B] mt-1">设置数据异常监控规则，及时发现业务问题</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[#0EA5E9] text-white rounded-lg hover:bg-[#0284C7] transition-colors"
        >
          <Plus className="w-4 h-4" />
          新建规则
        </button>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#FEF2F2] flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-[#DC2626]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[#1E293B]">1</p>
              <p className="text-xs text-[#64748B]">待处理告警</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#E0F2FE] flex items-center justify-center">
              <Bell className="w-5 h-5 text-[#0EA5E9]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[#1E293B]">{rules.filter((r) => r.status === "active").length}</p>
              <p className="text-xs text-[#64748B]">生效中规则</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#DCFCE7] flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-[#10B981]" />
            </div>
            <div>
              <p className="text-2xl font-bold text-[#1E293B]">{logs.filter((l) => l.status === "resolved").length}</p>
              <p className="text-xs text-[#64748B]">已处理告警</p>
            </div>
          </div>
        </div>
      </div>

      {/* 告警规则 */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm mb-6">
        <div className="px-5 py-4 border-b border-[#E2E8F0]">
          <h3 className="text-sm font-medium text-[#1E293B]">告警规则</h3>
        </div>
        <div className="divide-y divide-[#F1F5F9]">
          {rules.map((rule) => (
            <div key={rule.id} className="px-5 py-4 flex items-center justify-between hover:bg-[#F8FAFC]">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-[#1E293B]">{rule.name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      rule.status === "active"
                        ? "bg-[#DCFCE7] text-[#166534]"
                        : "bg-[#F1F5F9] text-[#64748B]"
                    }`}
                  >
                    {rule.status === "active" ? "生效中" : "已暂停"}
                  </span>
                </div>
                <p className="text-xs text-[#64748B] mt-1">
                  {rule.metric} {rule.condition} {rule.threshold}
                  {rule.lastTriggered && ` · 上次触发: ${rule.lastTriggered}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleRuleStatus(rule.id)}
                  className="p-2 rounded-lg hover:bg-[#E2E8F0] transition-colors"
                  title={rule.status === "active" ? "暂停" : "启用"}
                >
                  {rule.status === "active" ? (
                    <Bell className="w-4 h-4 text-[#0EA5E9]" />
                  ) : (
                    <Bell className="w-4 h-4 text-[#94A3B8]" />
                  )}
                </button>
                <button
                  onClick={() => deleteRule(rule.id)}
                  className="p-2 rounded-lg hover:bg-[#FEF2F2] transition-colors"
                  title="删除"
                >
                  <Trash2 className="w-4 h-4 text-[#EF4444]" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 告警记录 */}
      <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm">
        <div className="px-5 py-4 border-b border-[#E2E8F0]">
          <h3 className="text-sm font-medium text-[#1E293B]">告警记录</h3>
        </div>
        <div className="divide-y divide-[#F1F5F9]">
          {logs.map((log) => (
            <div key={log.id} className="px-5 py-4 flex items-start gap-3 hover:bg-[#F8FAFC]">
              <div
                className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                  log.severity === "high"
                    ? "bg-[#DC2626]"
                    : log.severity === "medium"
                    ? "bg-[#D97706]"
                    : "bg-[#0284C7]"
                }`}
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-[#1E293B]">{log.ruleName}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${getSeverityColor(log.severity)}`}>
                    {log.severity === "high" ? "高" : log.severity === "medium" ? "中" : "低"}
                  </span>
                </div>
                <p className="text-sm text-[#64748B] mt-1">{log.message}</p>
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-xs text-[#94A3B8] flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {log.timestamp}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      log.status === "resolved"
                        ? "bg-[#DCFCE7] text-[#166534]"
                        : "bg-[#FEF2F2] text-[#DC2626]"
                    }`}
                  >
                    {log.status === "resolved" ? "已处理" : "待处理"}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 添加规则弹窗 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl w-full max-w-md p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-[#1E293B] mb-4">新建告警规则</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-[#64748B] mb-1">规则名称</label>
                <input
                  type="text"
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  placeholder="例如：日活跃用户下降预警"
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-[#64748B] mb-1">监控指标</label>
                  <select
                    value={newRule.metric}
                    onChange={(e) => setNewRule({ ...newRule, metric: e.target.value })}
                    className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9]"
                  >
                    <option>DAU</option>
                    <option>日注册量</option>
                    <option>日收入</option>
                    <option>日订单量</option>
                    <option>留存率</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-[#64748B] mb-1">条件</label>
                  <select
                    value={newRule.condition}
                    onChange={(e) => setNewRule({ ...newRule, condition: e.target.value })}
                    className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9]"
                  >
                    <option>低于</option>
                    <option>高于</option>
                    <option>下降超过</option>
                    <option>上升超过</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">阈值</label>
                <input
                  type="text"
                  value={newRule.threshold}
                  onChange={(e) => setNewRule({ ...newRule, threshold: e.target.value })}
                  placeholder="例如：1000 或 20%"
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-sm text-[#64748B] hover:bg-[#F8FAFC] rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={addRule}
                className="px-4 py-2 text-sm bg-[#0EA5E9] text-white rounded-lg hover:bg-[#0284C7] transition-colors"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
