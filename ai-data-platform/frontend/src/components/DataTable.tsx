"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight, Table } from "lucide-react";

interface DataTableProps {
  data: Record<string, unknown>[];
  columns: string[];
  rowCount?: number;
}

export default function DataTable({ data, columns, rowCount }: DataTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;
  const totalPages = Math.ceil(data.length / pageSize);

  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const currentData = data.slice(startIndex, endIndex);

  return (
    <div className="bg-white rounded-xl border border-[#E2E8F0] shadow-sm overflow-hidden">
      {/* 表头 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#E2E8F0] bg-[#F8FAFC]">
        <div className="flex items-center gap-2">
          <Table className="w-4 h-4 text-[#64748B]" />
          <span className="text-sm font-medium text-[#1E293B]">查询结果</span>
        </div>
        <span className="text-xs text-[#64748B]">
          共 {rowCount || data.length} 条数据
        </span>
      </div>

      {/* 表格 */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[#F8FAFC] border-b border-[#E2E8F0]">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2.5 text-left text-xs font-medium text-[#64748B] uppercase tracking-wider whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#E2E8F0]">
            {currentData.map((row, idx) => (
              <tr key={idx} className="hover:bg-[#F8FAFC] transition-colors">
                {columns.map((col) => (
                  <td
                    key={col}
                    className="px-4 py-2.5 text-[#1E293B] whitespace-nowrap"
                  >
                    {row[col] !== null && row[col] !== undefined
                      ? String(row[col] as string | number | boolean)
                      : "-"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-[#E2E8F0]">
          <span className="text-xs text-[#64748B]">
            第 {startIndex + 1}-{Math.min(endIndex, data.length)} 条
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="p-1 rounded hover:bg-[#F1F5F9] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-xs px-2">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="p-1 rounded hover:bg-[#F1F5F9] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
