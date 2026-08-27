import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

def generate_csv(data: dict, is_comparison: bool = False) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    
    if not is_comparison:
        # Monthly report
        writer.writerow(["Budgetify Monthly Report"])
        writer.writerow(["Month", data.get("month"), "Year", data.get("year")])
        writer.writerow([])
        writer.writerow(["Summary"])
        writer.writerow(["Total Expenses", data.get("total_expenses")])
        writer.writerow(["Budget", data.get("budget")])
        writer.writerow(["Remaining", data.get("remaining_budget")])
        writer.writerow(["Transactions", data.get("transaction_count")])
        
        highest = data.get("highest_expense")
        if highest:
            writer.writerow(["Highest Expense", highest["title"], highest["amount"], highest["category"]])
            
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
    normal_style = styles['Normal']
    
    elements = []
    
    if not is_comparison:
        elements.append(Paragraph(f"Budgetify Monthly Report - {data.get('month')}/{data.get('year')}", title_style))
        elements.append(Spacer(1, 12))
        
        summary_data = [
            ["Metric", "Value"],
            ["Total Expenses", f"Rs {data.get('total_expenses')}"],
            ["Budget", f"Rs {data.get('budget')}"],
            ["Remaining", f"Rs {data.get('remaining_budget')}"],
            ["Transactions", str(data.get('transaction_count'))],
        ]
        
        if data.get("highest_expense"):
            h = data["highest_expense"]
            summary_data.append(["Highest Expense", f"{h['title']} (Rs {h['amount']})"])
            
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
        
    else:
        m1 = data["month1"]["summary"]
        m2 = data["month2"]["summary"]
        
        elements.append(Paragraph(f"Budgetify Comparison Report", title_style))
        elements.append(Paragraph(f"Comparing {m1['month']}/{m1['year']} vs {m2['month']}/{m2['year']}", normal_style))
        elements.append(Spacer(1, 12))
        
        summary_data = [
            ["Metric", f"Month {m1['month']}/{m1['year']}", f"Month {m2['month']}/{m2['year']}"],
            ["Total Expenses", f"Rs {m1['total_expenses']}", f"Rs {m2['total_expenses']}"],
            ["Budget", f"Rs {m1['budget']}", f"Rs {m2['budget']}"],
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
                f"Rs {cat['month1_spending']}",
                f"Rs {cat['month2_spending']}",
                f"Rs {cat['absolute_difference']}"
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
