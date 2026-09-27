import re

with open('app/static/index.html', encoding='utf-8') as f:
    text = f.read()

ids = sorted(set(re.findall(r'getElementById\([\"\']([^\"\']+)[\"\']\)', text)))
print(f"Total unique IDs: {len(ids)}")
for i in ids:
    print(f"ID: {i}")

funcs = sorted(set(re.findall(r'function\s+([a-zA-Z0-9_]+)\s*\(', text)))
print(f"\nTotal functions: {len(funcs)}")
for fn in funcs:
    print(f"FN: {fn}")
