"""Blog Monitor 설정."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "backend" / "stock_research.db"
BLOG_DATA_DIR = PROJECT_ROOT / "data" / "naver_blog_data"
RSS_LIST_FILE = BLOG_DATA_DIR / "naver_bloger_rss_list.txt"
