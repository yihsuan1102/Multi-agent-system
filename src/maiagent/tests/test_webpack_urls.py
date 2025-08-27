#!/usr/bin/env python3
import requests
import re

# Get the chat page HTML
response = requests.get('http://localhost:8000/chat/')
content = response.text

# Extract all script and link tags
script_pattern = r'<script[^>]*src="([^"]*)"[^>]*>'
link_pattern = r'<link[^>]*href="([^"]*)"[^>]*>'

scripts = re.findall(script_pattern, content)
links = re.findall(link_pattern, content)

print("=== JavaScript Files ===")
for script in scripts:
    print(f"  {script}")
    
print("\n=== CSS Files ===")  
for link in links:
    print(f"  {link}")
    
# Look for webpack_loader rendered content
print("\n=== Webpack Bundle Search ===")
webpack_lines = []
for line in content.split('\n'):
    if 'webpack' in line.lower() or 'bundle' in line.lower() or 'project-' in line or 'vendors-' in line:
        webpack_lines.append(line.strip())

for line in webpack_lines[:10]:  # Show first 10 matches
    print(f"  {line}")