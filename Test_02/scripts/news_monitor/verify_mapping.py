import sys, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')
db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'stock_research.db')
conn = sqlite3.connect(db_path)
rows = conn.execute("""
    SELECT sector, COUNT(*) as cnt, GROUP_CONCAT(industry, ' | ')
    FROM industry_performances WHERE date='2026-02-19'
    GROUP BY sector ORDER BY cnt DESC
""").fetchall()
for r in rows:
    inds = r[2].split(' | ')
    preview = ' | '.join(inds[:3]) + ('...' if len(inds) > 3 else '')
    print(f"{r[0]:25s} ({r[1]:3d}) {preview}")
unknown = conn.execute("SELECT industry FROM industry_performances WHERE sector='Unknown' AND date='2026-02-19'").fetchall()
if unknown:
    print(f"\nUnknown: {[u[0] for u in unknown]}")
else:
    print("\nAll industries mapped!")
conn.close()
