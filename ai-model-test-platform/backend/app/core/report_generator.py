import io
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class ReportGenerator:
    """报告生成器，支持PDF和Excel导出"""
    
    @staticmethod
    def generate_pdf(test_data: Dict[str, Any]) -> bytes:
        """生成PDF测试报告"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1  # 居中
        )
        
        elements = []
        
        # 标题
        elements.append(Paragraph("AI模型测试报告", title_style))
        elements.append(Spacer(1, 20))
        
        # 基本信息
        elements.append(Paragraph("<b>测试基本信息</b>", styles["Heading2"]))
        basic_info = [
            ["测试名称", test_data.get("name", "")],
            ["测试状态", test_data.get("status", "")],
            ["创建时间", test_data.get("created_at", "")],
            ["完成时间", test_data.get("completed_at", "")],
            ["参与模型数", str(len(test_data.get("models", [])))],
            ["参与用户数", str(len(test_data.get("users", [])))],
        ]
        
        basic_table = Table(basic_info, colWidths=[2*inch, 4*inch])
        basic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(basic_table)
        elements.append(Spacer(1, 20))
        
        # 模型评分对比
        elements.append(Paragraph("<b>模型评分对比</b>", styles["Heading2"]))
        
        if test_data.get("results"):
            # 构建对比表格
            headers = ["模型", "用户", "总分"] + [d["name"] for d in test_data.get("dimensions", [])]
            
            table_data = [headers]
            for result in test_data["results"]:
                row = [
                    result.get("model_name", ""),
                    result.get("user_name", ""),
                    str(result.get("total_score", "N/A"))
                ]
                
                scores = result.get("scores", {})
                for dim in test_data.get("dimensions", []):
                    dim_score = scores.get(dim["name", {}], {}).get("score", "N/A")
                    row.append(str(dim_score))
                
                table_data.append(row)
            
            col_widths = [1.5*inch] * len(headers)
            results_table = Table(table_data, colWidths=col_widths)
            results_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(results_table)
        
        elements.append(Spacer(1, 20))
        
        # 模型平均分排名
        elements.append(Paragraph("<b>模型平均分排名</b>", styles["Heading2"]))
        
        if test_data.get("model_ranking"):
            ranking_data = [["排名", "模型", "平均分"]]
            for idx, item in enumerate(test_data["model_ranking"], 1):
                ranking_data.append([str(idx), item["name"], f"{item['avg_score']:.2f}"])
            
            ranking_table = Table(ranking_data, colWidths=[1*inch, 3*inch, 2*inch])
            ranking_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(ranking_table)
        
        doc.build(elements)
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    
    @staticmethod
    def generate_excel(test_data: Dict[str, Any]) -> bytes:
        """生成Excel测试报告"""
        
        wb = openpyxl.Workbook()
        
        # 概览sheet
        ws_overview = wb.active
        ws_overview.title = "测试概览"
        
        # 标题
        ws_overview['A1'] = 'AI模型测试报告'
        ws_overview['A1'].font = Font(size=16, bold=True)
        ws_overview.merge_cells('A1:D1')
        ws_overview['A1'].alignment = Alignment(horizontal='center')
        
        # 基本信息
        ws_overview['A3'] = '测试名称'
        ws_overview['B3'] = test_data.get("name", "")
        ws_overview['A4'] = '测试状态'
        ws_overview['B4'] = test_data.get("status", "")
        ws_overview['A5'] = '创建时间'
        ws_overview['B5'] = test_data.get("created_at", "")
        ws_overview['A6'] = '完成时间'
        ws_overview['B6'] = test_data.get("completed_at", "")
        
        # 设置样式
        for row in range(3, 7):
            ws_overview[f'A{row}'].font = Font(bold=True)
            ws_overview[f'A{row}'].fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
        
        # 详细结果sheet
        ws_details = wb.create_sheet("详细结果")
        
        if test_data.get("results"):
            # 表头
            headers = ["模型", "用户", "总分", "评分详情"]
            for col, header in enumerate(headers, 1):
                cell = ws_details.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
                cell.alignment = Alignment(horizontal='center')
            
            # 数据
            for row_idx, result in enumerate(test_data["results"], 2):
                ws_details.cell(row=row_idx, column=1, value=result.get("model_name", ""))
                ws_details.cell(row=row_idx, column=2, value=result.get("user_name", ""))
                ws_details.cell(row=row_idx, column=3, value=result.get("total_score", ""))
                
                scores = result.get("scores", {})
                score_text = "\n".join([
                    f"{k}: {v.get('score', 'N/A')} ({v.get('reason', '')})"
                    for k, v in scores.items()
                ])
                ws_details.cell(row=row_idx, column=4, value=score_text)
                ws_details.cell(row=row_idx, column=4).alignment = Alignment(wrap_text=True)
            
            # 自动调整列宽
            for col in range(1, 5):
                ws_details.column_dimensions[get_column_letter(col)].width = 25
        
        # 排名sheet
        ws_ranking = wb.create_sheet("模型排名")
        
        if test_data.get("model_ranking"):
            headers = ["排名", "模型", "平均分"]
            for col, header in enumerate(headers, 1):
                cell = ws_ranking.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
                cell.alignment = Alignment(horizontal='center')
            
            for row_idx, item in enumerate(test_data["model_ranking"], 2):
                ws_ranking.cell(row=row_idx, column=1, value=row_idx - 1)
                ws_ranking.cell(row=row_idx, column=2, value=item["name"])
                ws_ranking.cell(row=row_idx, column=3, value=round(item["avg_score"], 2))
            
            for col in range(1, 4):
                ws_ranking.column_dimensions[get_column_letter(col)].width = 20
        
        # 保存到内存
        buffer = io.BytesIO()
        wb.save(buffer)
        excel_bytes = buffer.getvalue()
        buffer.close()
        
        return excel_bytes
