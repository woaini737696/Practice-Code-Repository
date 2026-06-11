"use client";

import { useState } from "react";
import {
  Database,
  Mail,
  Key,
  Shield,
  Save,
  Check,
  AlertTriangle,
  Eye,
  EyeOff,
} from "lucide-react";

export default function Settings() {
  const [dbConfig, setDbConfig] = useState({
    host: "localhost",
    port: "3306",
    user: "",
    password: "",
    database: "",
  });

  const [llmConfig, setLlmConfig] = useState({
    provider: "deepseek",
    apiKey: "",
    model: "deepseek-chat",
    baseUrl: "https://api.deepseek.com/v1",
  });

  const [emailConfig, setEmailConfig] = useState({
    smtpHost: "",
    smtpPort: "587",
    smtpUser: "",
    smtpPassword: "",
    fromEmail: "",
    toEmail: "",
  });

  const [saved, setSaved] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [activeSection, setActiveSection] = useState("database");

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const sections = [
    { id: "database", label: "数据库配置", icon: Database },
    { id: "llm", label: "AI模型配置", icon: Key },
    { id: "email", label: "邮件告警", icon: Mail },
    { id: "security", label: "安全设置", icon: Shield },
  ];

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* 左侧设置菜单 */}
      <div className="w-56 bg-white border-r border-[#E2E8F0] py-4">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
              activeSection === section.id
                ? "bg-[#E0F2FE] text-[#0EA5E9] border-r-2 border-[#0EA5E9]"
                : "text-[#64748B] hover:bg-[#F8FAFC]"
            }`}
          >
            <section.icon className="w-4 h-4" />
            <span className="text-sm">{section.label}</span>
          </button>
        ))}
      </div>

      {/* 右侧内容 */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-[#1E293B]">系统设置</h2>
              <p className="text-sm text-[#64748B] mt-1">配置平台运行所需的关键参数</p>
            </div>
            <button
              onClick={handleSave}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm transition-colors ${
                saved
                  ? "bg-[#DCFCE7] text-[#166534]"
                  : "bg-[#0EA5E9] text-white hover:bg-[#0284C7]"
              }`}
            >
              {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
              {saved ? "已保存" : "保存设置"}
            </button>
          </div>

          {/* 数据库配置 */}
          {activeSection === "database" && (
            <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-medium text-[#1E293B] flex items-center gap-2">
                <Database className="w-4 h-4 text-[#0EA5E9]" />
                MySQL只读从库配置
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-[#64748B] mb-1">主机地址</label>
                  <input
                    type="text"
                    value={dbConfig.host}
                    onChange={(e) => setDbConfig({ ...dbConfig, host: e.target.value })}
                    className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[#64748B] mb-1">端口</label>
                  <input
                    type="text"
                    value={dbConfig.port}
                    onChange={(e) => setDbConfig({ ...dbConfig, port: e.target.value })}
                    className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">数据库名</label>
                <input
                  type="text"
                  value={dbConfig.database}
                  onChange={(e) => setDbConfig({ ...dbConfig, database: e.target.value })}
                  placeholder="请输入数据库名称"
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">用户名</label>
                <input
                  type="text"
                  value={dbConfig.user}
                  onChange={(e) => setDbConfig({ ...dbConfig, user: e.target.value })}
                  placeholder="请输入数据库用户名"
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">密码</label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={dbConfig.password}
                    onChange={(e) => setDbConfig({ ...dbConfig, password: e.target.value })}
                    placeholder="请输入数据库密码"
                    className="w-full px-3 py-2 pr-10 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                  />
                  <button
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#94A3B8]"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              <div className="bg-[#E0F2FE] rounded-lg p-3 flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 text-[#0EA5E9] shrink-0 mt-0.5" />
                <p className="text-xs text-[#0284C7]">
                  当前连接的是只读从库，所有查询操作均为只读，不会影响线上数据。
                </p>
              </div>
            </div>
          )}

          {/* AI模型配置 */}
          {activeSection === "llm" && (
            <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-medium text-[#1E293B] flex items-center gap-2">
                <Key className="w-4 h-4 text-[#0EA5E9]" />
                AI大模型配置
              </h3>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">模型提供商</label>
                <select
                  value={llmConfig.provider}
                  onChange={(e) => setLlmConfig({ ...llmConfig, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9]"
                >
                  <option value="deepseek">DeepSeek</option>
                  <option value="openai">OpenAI</option>
                  <option value="custom">自定义</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">API Key</label>
                <input
                  type="password"
                  value={llmConfig.apiKey}
                  onChange={(e) => setLlmConfig({ ...llmConfig, apiKey: e.target.value })}
                  placeholder="sk-..."
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">模型名称</label>
                <input
                  type="text"
                  value={llmConfig.model}
                  onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">API地址</label>
                <input
                  type="text"
                  value={llmConfig.baseUrl}
                  onChange={(e) => setLlmConfig({ ...llmConfig, baseUrl: e.target.value })}
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
            </div>
          )}

          {/* 邮件告警配置 */}
          {activeSection === "email" && (
            <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-medium text-[#1E293B] flex items-center gap-2">
                <Mail className="w-4 h-4 text-[#0EA5E9]" />
                邮件告警配置
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-[#64748B] mb-1">SMTP服务器</label>
                  <input
                    type="text"
                    value={emailConfig.smtpHost}
                    onChange={(e) => setEmailConfig({ ...emailConfig, smtpHost: e.target.value })}
                    placeholder="smtp.example.com"
                    className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                  />
                </div>
                <div>
                  <label className="block text-sm text-[#64748B] mb-1">SMTP端口</label>
                  <input
                    type="text"
                    value={emailConfig.smtpPort}
                    onChange={(e) => setEmailConfig({ ...emailConfig, smtpPort: e.target.value })}
                    className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">发件人邮箱</label>
                <input
                  type="email"
                  value={emailConfig.fromEmail}
                  onChange={(e) => setEmailConfig({ ...emailConfig, fromEmail: e.target.value })}
                  placeholder="alert@example.com"
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">收件人邮箱</label>
                <input
                  type="email"
                  value={emailConfig.toEmail}
                  onChange={(e) => setEmailConfig({ ...emailConfig, toEmail: e.target.value })}
                  placeholder="your@email.com"
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">SMTP用户名</label>
                <input
                  type="text"
                  value={emailConfig.smtpUser}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtpUser: e.target.value })}
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
              <div>
                <label className="block text-sm text-[#64748B] mb-1">SMTP密码</label>
                <input
                  type="password"
                  value={emailConfig.smtpPassword}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtpPassword: e.target.value })}
                  className="w-full px-3 py-2 border border-[#E2E8F0] rounded-lg text-sm outline-none focus:border-[#0EA5E9] focus:ring-1 focus:ring-[#0EA5E9]"
                />
              </div>
            </div>
          )}

          {/* 安全设置 */}
          {activeSection === "security" && (
            <div className="bg-white rounded-xl border border-[#E2E8F0] p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-medium text-[#1E293B] flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#0EA5E9]" />
                安全设置
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between py-3 border-b border-[#F1F5F9]">
                  <div>
                    <p className="text-sm text-[#1E293B]">手机号脱敏</p>
                    <p className="text-xs text-[#64748B]">查询结果中自动脱敏手机号字段</p>
                  </div>
                  <div className="w-11 h-6 bg-[#0EA5E9] rounded-full relative cursor-pointer">
                    <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5 shadow-sm" />
                  </div>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-[#F1F5F9]">
                  <div>
                    <p className="text-sm text-[#1E293B]">只读模式</p>
                    <p className="text-xs text-[#64748B]">仅允许SELECT查询，禁止任何数据修改</p>
                  </div>
                  <div className="w-11 h-6 bg-[#0EA5E9] rounded-full relative cursor-pointer">
                    <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5 shadow-sm" />
                  </div>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-[#F1F5F9]">
                  <div>
                    <p className="text-sm text-[#1E293B]">查询超时限制</p>
                    <p className="text-xs text-[#64748B]">单条查询最大执行时间30秒</p>
                  </div>
                  <div className="w-11 h-6 bg-[#0EA5E9] rounded-full relative cursor-pointer">
                    <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5 shadow-sm" />
                  </div>
                </div>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm text-[#1E293B]">返回行数限制</p>
                    <p className="text-xs text-[#64748B]">单次查询最多返回10000行数据</p>
                  </div>
                  <div className="w-11 h-6 bg-[#0EA5E9] rounded-full relative cursor-pointer">
                    <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5 shadow-sm" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
