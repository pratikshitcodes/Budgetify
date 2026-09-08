# -*- coding: utf-8 -*-
import sys
import re

path = r'C:\Users\Lenovo\Desktop\FAST_API\expense-tracker\backend\app\services\analytics_service.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_logic_pattern = r'daily_timeline = \{\}\s*for e in expenses:\s*day_str = str\(e\.created_at\.date\(\)\)\s*if day_str not in daily_timeline:\s*daily_timeline\[day_str\] = \{"total": 0, "transactions": \[\]\}\s*daily_timeline\[day_str\]\["total"\] \+= float\(e\.amount\)\s*daily_timeline\[day_str\]\["transactions"\]\.append\(\{\s*"title": e\.title,\s*"amount": float\(e\.amount\),\s*"category": e\.category\s*\}\)'

new_logic = '''daily_timeline = {}
    for e in expenses:
        day_str = str(e.created_at.date())
        cat = e.category if e.category else "Uncategorized"
        
        if day_str not in daily_timeline:
            daily_timeline[day_str] = {"daily_total": 0, "categories": {}}
            
        daily_timeline[day_str]["daily_total"] += float(e.amount)
        
        if cat not in daily_timeline[day_str]["categories"]:
            daily_timeline[day_str]["categories"][cat] = {
                "total": 0,
                "count": 0,
                "items": []
            }
            
        daily_timeline[day_str]["categories"][cat]["total"] += float(e.amount)
        daily_timeline[day_str]["categories"][cat]["count"] += 1
        
        if daily_timeline[day_str]["categories"][cat]["count"] <= 5:
            daily_timeline[day_str]["categories"][cat]["items"].append(f"{e.title} - \u20b9{float(e.amount)}")
'''

content = re.sub(old_logic_pattern, new_logic, content, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
