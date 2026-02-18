import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import SessionLocal
from backend.app.models.idea import Idea

def check_ideas():
    db = SessionLocal()
    ideas = db.query(Idea).all()
    print(f"Total Ideas: {len(ideas)}")
    for idea in ideas:
        print(f"[{idea.id}] {idea.title} ({idea.status})")
        print(f"   Source: {idea.source}")
        print(f"   Tags: {idea.tags}")
        print("-" * 20)
    db.close()

if __name__ == "__main__":
    check_ideas()
