# -*- coding: utf-8 -*-
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet

def generate_csv(data: dict, is_comparison: bool = False) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    if not is_comparison:
        # Monthly report
        writer.writerow(["Budgetify Financial Diary"])
        writer.writerow(["Month", data.get("month"), "Year", data.get("year")])
        writer.writerow([])
        writer.writerow(["--- OVERVIEW ---"])
        writer.writerow(["Total Expenses", f"\u20b9{data.get('total_expenses')}"])
        writer.writerow(["Budget", f"\u20b9{data.get('budget')}"])
        writer.writerow(["Remaining", f"\u20b9{data.get('remaining_budget')}"])
        writer.writerow(["Transactions", data.get("transaction_count")])
        writer.writerow([])
        
        writer.writerow(["--- CATEGORY ANALYSIS ---"])
        writer.writerow(["Category", "Amount Spent"])
        for cat, amt in data.get("category_breakdown", {}).items():
            writer.writerow([cat, f"\u20b9{amt}"])
        writer.writerow([])
        
        writer.writerow(["--- BIGGEST EXPENSES ---"])
        writer.writerow(["Date", "Title", "Category", "Amount"])
        for exp in data.get("top_expenses", []):
            writer.writerow([exp["date"], exp["title"], exp["category"], f"\u20b9{exp['amount']}"])
        writer.writerow([])
        
        writer.writerow(["--- DAILY SPENDING TIMELINE ---"])
        writer.writerow(["Date", "Category", "Details", "Category Total", "Daily Total"])
        timeline = data.get("daily_timeline", {})
        for day in sorted(timeline.keys()):
            day_data = timeline[day]
            for cat, cat_data in day_data["categories"].items():
                items_str = " | ".join(cat_data["items"])
                writer.writerow([day, cat, items_str, f"\u20b9{cat_data['total']}", f"\u20b9{day_data['daily_total']}"])
            
    else:
        # Comparison report
        m1 = data["month1"]["summary"]
        m2 = data["month2"]["summary"]
        writer.writerow(["Budgetify Comparison Report"])
        writer.writerow(["Metric", f"Month {m1['month']}/{m1['year']}", f"Month {m2['month']}/{m2['year']}"])
        writer.writerow(["Total Expenses", m1["total_expenses"], m2["total_expenses"]])
        writer.writerow(["Budget", m1["budget"], m2["budget"]])
        writer.writerow(["Transactions", m1["transaction_count"], m2["transaction_count"]])
        
        writer.writerow([])
        writer.writerow(["Category", "Month 1 Spending", "Month 2 Spending", "Difference", "% Change"])
        for cat in data["categories"]:
            writer.writerow([
                cat["category"],
                cat["month1_spending"],
                cat["month2_spending"],
                cat["absolute_difference"],
                cat["percentage_difference"]
            ])
            
    return output.getvalue()

def generate_pdf(data: dict, is_comparison: bool = False) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    h2 = styles['Heading2']
    h3 = styles['Heading3']
    normal = styles['Normal']
    
    elements = []
    
    if not is_comparison:
        elements.append(Paragraph(f"Budgetify Financial Diary - {data.get('month')}/{data.get('year')}", title_style))
        elements.append(Spacer(1, 12))
        
        # Overview
        elements.append(Paragraph("1. Monthly Overview", h2))
        summary_data = [
            ["Metric", "Value"],
            ["Total Expenses", f"INR {data.get('total_expenses')}"],
            ["Budget", f"INR {data.get('budget')}"],
            ["Remaining", f"INR {data.get('remaining_budget')}"],
            ["Transactions", str(data.get('transaction_count'))],
        ]
        
        t = Table(summary_data, colWidths=[200, 200])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#7c5cfc')),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        # Categories
        elements.append(Paragraph("2. Category Analysis", h2))
        cat_data = [["Category", "Amount Spent"]]
        for cat, amt in data.get("category_breakdown", {}).items():
            cat_data.append([cat, f"INR {amt}"])
        if len(cat_data) > 1:
            t_cat = Table(cat_data, colWidths=[200, 200])
            t_cat.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D9E75')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t_cat)
        elements.append(Spacer(1, 12))
        
        # Top Expenses
        elements.append(Paragraph("3. Biggest Expenses", h2))
        top_data = [["Date", "Title", "Category", "Amount"]]
        for exp in data.get("top_expenses", []):
            top_data.append([exp["date"], exp["title"], exp["category"], f"INR {exp['amount']}"])
        if len(top_data) > 1:
            t_top = Table(top_data, colWidths=[100, 150, 100, 100])
            t_top.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B6B')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(t_top)
        elements.append(Spacer(1, 12))
        
        # Timeline
        elements.append(Paragraph("4. Spending Timeline", h2))
        timeline = data.get("daily_timeline", {})
        for day in sorted(timeline.keys()):
            day_data = timeline[day]
            elements.append(Paragraph(f"<b>{day} (Total: INR {day_data['daily_total']})</b>", h3))
            
            for cat, cat_data in day_data["categories"].items():
                items_str = ", ".join(cat_data["items"])
                elements.append(Paragraph(f"• {cat}: INR {cat_data['total']} ({cat_data['count']} transactions) -> {items_str}", normal))
            elements.append(Spacer(1, 6))
            
    else:
        m1 = data["month1"]["summary"]
        m2 = data["month2"]["summary"]
        
        elements.append(Paragraph(f"Budgetify Comparison Report", title_style))
        elements.append(Paragraph(f"Comparing {m1['month']}/{m1['year']} vs {m2['month']}/{m2['year']}", normal))
        elements.append(Spacer(1, 12))
        
        summary_data = [
            ["Metric", f"Month {m1['month']}/{m1['year']}", f"Month {m2['month']}/{m2['year']}"],
            ["Total Expenses", f"INR {m1['total_expenses']}", f"INR {m2['total_expenses']}"],
            ["Budget", f"INR {m1['budget']}", f"INR {m2['budget']}"],
            ["Transactions", str(m1['transaction_count']), str(m2['transaction_count'])],
        ]
        
        t = Table(summary_data, colWidths=[150, 150, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c5cfc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 24))
        
        elements.append(Paragraph("Category Breakdown", styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        cat_data = [["Category", "Month 1", "Month 2", "Difference"]]
        for cat in data["categories"]:
            cat_data.append([
                cat["category"],
                f"INR {cat['month1_spending']}",
                f"INR {cat['month2_spending']}",
                f"INR {cat['absolute_difference']}"
            ])
            
        t_cat = Table(cat_data)
        t_cat.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D9E75')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t_cat)
        
    doc.build(elements)
    return buffer.getvalue()
