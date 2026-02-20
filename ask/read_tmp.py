import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('전달용_tmp.txt', 'r', encoding='utf-8') as f:
    print(f.read())
