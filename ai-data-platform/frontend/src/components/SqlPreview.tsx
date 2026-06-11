"use client";

import { useState } from "react";
import { Code, Clock, ChevronDown, ChevronUp, Copy, Check } from "lucide-react";

interface SqlPreviewProps {
  sql: string;
  executionTime?: number;
}

export default function SqlPreview({ sql, executionTime }: SqlPreviewProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[#1E293B] rounded-xl overflow-hidden">
      {/* 头部 */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#0F172A]">
        <div className="flex items-center gap-2">
          <Code className="w-4 h-4 text-[#0EA5E9]" />
          <span className="text-xs text-[#94A3B8]">SQL</span>
          {executionTime && (
            <span className="flex items-center gap-1 text-xs text-[#64748B]">
              <Clock className="w-3 h-3" />
              {executionTime}s
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-white/10 transition-colors"
            title="复制SQL"
          >
            {copied ? (
              <Check className="w-3.5 h-3.5 text-[#10B981]" />
            ) : (
              <Copy className="w-3.5 h-3.5 text-[#94A3B8]" />
            )}
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 rounded hover:bg-white/10 transition-colors"
          >
            {expanded ? (
              <ChevronUp className="w-3.5 h-3.5 text-[#94A3B8]" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-[#94A3B8]" />
            )}
          </button>
        </div>
      </div>

      {/* SQL内容 */}
      {expanded && (
        <div className="px-4 py-3 overflow-x-auto">
          <pre className="text-xs text-[#E2E8F0] font-mono whitespace-pre-wrap break-all">
            {sql}
          </pre>
        </div>
      )}
    </div>
  );
}
