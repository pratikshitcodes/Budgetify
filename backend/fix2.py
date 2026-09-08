import sys
import re

path = r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\routers\agents.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's clean all occurrences of get_detailed_analysis blocks inside the if tool_name blocks and re-insert them cleanly.
content = re.sub(r'\s*elif tool_name == \"get_detailed_analysis\":\s*result = analytics_service\.get_detailed_analysis[^\n]+', '', content)
content = re.sub(r'\s*elif tool_name == \"get_detailed_monthly_analysis\":\s*result = analytics_service\.get_detailed_monthly_analysis[^\n]+', '', content)

# Also clean up the messed up literals
content = re.sub(r'\s*elif tool_name == "get_detailed_analysis":\s*.*?elif tool_name == "compare_months":', '\n                elif tool_name == "compare_months":', content, flags=re.DOTALL)


replacement = '''
                elif tool_name == "get_monthly_summary":
                    result = analytics_service.get_monthly_summary(db, current_user.id, args["month"], args["year"])

                elif tool_name == "get_detailed_analysis":
                    result = analytics_service.get_detailed_analysis(db, current_user.id, args["month"], args["year"])
'''

content = content.replace('''
                elif tool_name == "get_monthly_summary":
                    result = analytics_service.get_monthly_summary(db, current_user.id, args["month"], args["year"])''', replacement)


with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
