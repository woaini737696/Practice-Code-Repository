"use client";

import { useState } from "react";
import {
  BarChart3,
  Users,
  ShoppingCart,
  TrendingUp,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
  icon: React.ElementType;
}

function MetricCard({ title, value, change, isPositive, icon: Icon }: MetricCardProps) {
  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm text-[#64748B]">{title}</span>
        <div className="w-9 h-9 rounded-lg bg-[#E0F2FE] flex items-center justify-center">
          <Icon className="w-4 h-4 text-[#0EA5E9]" />
        </div>
      </div>
      <div className="text-2xl font-bold text-[#1E293B] mb-1">{value}</div>
      <div className={`flex items-center gap-1 text-xs ${isPositive ? "text-[#10B981]" : "text-[#EF4444]"}`}>
        {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
        <span>{change}</span>
        <span className="text-[#94A3B8] ml-1">较上周</span>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState([
    { title: "总用户数", value: "12,458", change: "+12.5%", isPositive: true, icon: Users },
    { title: "今日活跃用户", value: "3,271", change: "+8.2%", isPositive: true, icon: TrendingUp },
    { title: "今日订单数", value: "856", change: "-2.1%", isPositive: false, icon: ShoppingCart },
    { title: "今日收入", value: "¥45,230", change: "+15.3%", isPositive: true, icon: BarChart3 },
  ]);

  const refreshData = async () => {
    setLoading(true);
    // 模拟数据刷新
    setTimeout(() => {
      setMetrics((prev) =>
        prev.map((m) => ({
          ...m,
          value: m.title.includes("收入")
            ? `¥${(Math.random() * 50000 + 20000).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`
            : m.title.includes("用户")
            ? `${(Math.random() * 20000 + 5000).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}`
            : `${(Math.random() * 1000 + 200).toFixed(0)}`,
        }))
      );
      setLoading(false);
    }, 800);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      {/* 顶部操作栏 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-[#1E293B]">数据看板</h2>
          <p className="text-sm text-[#64748B] mt-1">实时监控核心业务指标</p>
        </div>
        <button
          onClick={refreshData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white border border-[#E2E8F0] rounded-lg text-sm text-[#1E293B] hover:bg-[#F8FAFC] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          刷新数据
        </button>
      </div>

      {/* 核心指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {metrics.map((metric, idx) => (
          <MetricCard key={idx} {...metric} />
        ))}
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* 用户趋势 */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <h3 className="text-sm font-medium text-[#1E293B] mb-4">近7天用户增长趋势</h3>
          <SimpleBarChart />
        </div>

        {/* 收入来源分布 */}
        <div className="bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
          <h3 className="text-sm font-medium text-[#1E293B] mb-4">收入来源分布</h3>
          <SimplePieChart />
        </div>
      </div>

      {/* 最近活动 */}
      <div className="mt-6 bg-white rounded-xl border border-[#E2E8F0] p-5 shadow-sm">
        <h3 className="text-sm font-medium text-[#1E293B] mb-4">最近数据活动</h3>
        <div className="space-y-3">
          {[
            { time: "10:23", desc: "AI助手执行查询：最近7天新注册用户", status: "成功" },
            { time: "09:45", desc: "AI助手执行查询：今日活跃用户统计", status: "成功" },
            { time: "09:12", desc: "系统定时扫描：数据异常检测", status: "正常" },
            { time: "08:30", desc: "AI助手执行查询：订单收入分析", status: "成功" },
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-4 py-2 border-b border-[#F1F5F9] last:border-0">
              <span className="text-xs text-[#94A3B8] w-12">{item.time}</span>
              <span className="text-sm text-[#1E293B] flex-1">{item.desc}</span>
              <span className="text-xs px-2 py-1 rounded-full bg-[#DCFCE7] text-[#166534]">{item.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function SimpleBarChart() {
  const data = [
    { day: "周一", value: 65 },
    { day: "周二", value: 78 },
    { day: "周三", value: 52 },
    { day: "周四", value: 91 },
    { day: "周五", value: 84 },
    { day: "周六", value: 120 },
    { day: "周日", value: 105 },
  ];
  const maxValue = Math.max(...data.map((d) => d.value));

  return (
    <div className="flex items-end justify-between h-40 gap-2">
      {data.map((item, idx) => (
        <div key={idx} className="flex-1 flex flex-col items-center gap-2">
          <div
            className="w-full bg-[#0EA5E9] rounded-t-md transition-all duration-500 hover:bg-[#0284C7]"
            style={{ height: `${(item.value / maxValue) * 100}%` }}
          />
          <span className="text-xs text-[#64748B]">{item.day}</span>
        </div>
      ))}
    </div>
  );
}

function SimplePieChart() {
  const segments = [
    { label: "会员订阅", value: 45, color: "#0EA5E9" },
    { label: "广告收入", value: 30, color: "#10B981" },
    { label: "增值服务", value: 25, color: "#F59E0B" },
  ];

  return (
    <div className="flex items-center gap-6">
      <div className="relative w-32 h-32">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          {segments.reduce(
            (acc, segment, idx) => {
              const startOffset = acc.offset;
              const dashArray = `${segment.value} ${100 - segment.value}`;
              const circle = (
                <circle
                  key={idx}
                  cx="18"
                  cy="18"
                  r="15.9"
                  fill="none"
                  stroke={segment.color}
                  strokeWidth="3"
                  strokeDasharray={dashArray}
                  strokeDashoffset={-startOffset}
                  className="transition-all duration-500"
                />
              );
              return { elements: [...acc.elements, circle], offset: startOffset + segment.value };
            },
            { elements: [] as React.ReactNode[], offset: 0 }
          ).elements}
        </svg>
      </div>
      <div className="space-y-2">
        {segments.map((s, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: s.color }} />
            <span className="text-sm text-[#1E293B]">{s.label}</span>
            <span className="text-sm text-[#64748B]">{s.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
