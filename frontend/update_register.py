import re

with open('register.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Make it a bright, fresh cyan theme
css = re.sub(r'background\s*:\s*linear-gradient\([^)]+\);', 'background: linear-gradient(135deg, #00d2ff, #3a7bd5);', css)
css = re.sub(r'background-color\s*:\s*#[0-9a-fA-F]+;*;?', 'background-color: #ffffff;', css)

# Fix inputs & Focus
css = re.sub(r'border-color\s*:\s*#[0-9a-fA-F]+;', 'border-color: #00d2ff;', css)
css = re.sub(r'box-shadow\s*:\s*0 0 0 3px[^;]+;', 'box-shadow: 0 0 0 3px rgba(0, 210, 255, 0.2);', css)

# Button styles
css = re.sub(r'border\s*:\s*2px solid rgb\([^)]+\);', 'border: 2px solid #0099cc;', css)
css = re.sub(r'box-shadow\s*:\s*0 0 8px[^;]+;', 'box-shadow: 0 0 8px rgba(0, 210, 255, 0.6);', css)

with open('register.css', 'w', encoding='utf-8') as f:
    f.write(css)
