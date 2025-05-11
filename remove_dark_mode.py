import re
import os

def remove_dark_mode_styles(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove dark mode styles
    pattern = r'/\* Dark mode.*?\*/\s*\[data-theme="dark"\].*?{.*?}.*?(?=\n\n|\Z)'
    cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    # Remove individual dark mode selectors
    pattern = r'\[data-theme="dark"\].*?{.*?}.*?(?=\n\n|\Z)'
    cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(cleaned_content)
    
    print(f"Removed dark mode styles from {file_path}")

# Process CSS files
css_files = [
    'static/css/style.css',
    'static/css/cart-popup.css',
    'static/css/quote-popup.css'
]

for css_file in css_files:
    if os.path.exists(css_file):
        remove_dark_mode_styles(css_file)
    else:
        print(f"File not found: {css_file}")

print("Dark mode styles removal complete")
