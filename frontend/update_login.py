import re

with open('expense_login.css', 'r', encoding='utf-8') as f:
    css = f.read()

css = css.replace('background: #f5f7fb;', 'background: #0f172a;')
css = re.sub(r'background:linear-gradient\(135deg,[\s\S]*?#5DA9E9\);', 'background:linear-gradient(135deg, #091c29, #004d61);', css)

css = css.replace('background: rgba(255,255,255,0.88);', 'background: rgba(21, 32, 43, 0.88);')
css = css.replace('border: 1px solid rgba(255,255,255,0.45);', 'border: 1px solid rgba(6, 182, 212, 0.3);')
css = css.replace('box-shadow: 0 24px 70px rgba(44, 21, 85, 0.28);', 'box-shadow: 0 24px 70px rgba(6, 182, 212, 0.15);')

css = css.replace('color: #2b2b2b;', 'color: #e0f2fe;')
css = css.replace('color: #6b7280;', 'color: #94a3b8;')
css = css.replace('color: #4b5563;', 'color: #94a3b8;')

css = re.sub(r'input\[type="text"\],\s*input\[type="password"\]\{[\s\S]*?\}', 
    'input[type="text"],\ninput[type="password"]{\n  width: 100%;\n  box-sizing: border-box;\n  padding: 12px 12px;\n  font-size: 14px;\n  border-radius: 14px;\n  border: 1px solid #334155;\n  outline: none;\n  background: rgba(15, 23, 42, 0.6);\n  color: #e0f2fe;\n  box-shadow: 0 2px 8px rgba(0,0,0,0.2);\n}', css)

css = css.replace('border-color: rgb(0, 140, 255);', 'border-color: #06b6d4; box-shadow: 0 0 8px rgba(6, 182, 212, 0.3);')
css = css.replace('background: linear-gradient(180deg, rgb(0, 183, 255) 0%, rgb(0, 89, 255));', 'background: linear-gradient(180deg, #06b6d4 0%, #0891b2);')

with open('expense_login.css', 'w', encoding='utf-8') as f:
    f.write(css)
