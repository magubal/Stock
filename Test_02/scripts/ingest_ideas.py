import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models.idea import Idea

def ingest_text_file(file_path):
    print(f"Parsing text file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Create DB session
    db = SessionLocal()
    
    # Check if this file is already ingested (simple duplicate check by title)
    title = f"Idea extracted from {os.path.basename(file_path)} - {datetime.now().strftime('%Y-%m-%d')}"
    existing = db.query(Idea).filter(Idea.title == title).first()
    
    if existing:
        print(f"Idea '{title}' already exists. Skipping.")
        db.close()
        return

    # Create new Idea
    new_idea = Idea(
        title=title,
        content=content[:10000], # Limit content length
        source="Text_Log",
        status="draft",
        priority=3,
        tags=["extracted", "log", "daily_work"],
        author="System"
    )
    
    try:
        db.add(new_idea)
        db.commit()
        db.refresh(new_idea)
        print(f"Successfully ingested idea ID: {new_idea.id}")
    except Exception as e:
        print(f"Error saving to DB: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    target_text = r"F:\PSJ\AntigravityWorkPlace\Stock\Test_02\data\ask\전달용_tmp.txt"
    
    if os.path.exists(target_text):
        ingest_text_file(target_text)
    else:
        print(f"File not found: {target_text}")
