import sys
import re

path = r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\routers\reports.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace get_monthly_summary with get_detailed_analysis in get_monthly_report, get_monthly_pdf, and get_monthly_csv
content = re.sub(r'data = analytics_service\.get_monthly_summary\(db, current_user\.id, month, year\)', 'data = analytics_service.get_detailed_analysis(db, current_user.id, month, year)', content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
