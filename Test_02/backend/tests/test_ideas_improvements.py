import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.api.ideas import read_ideas
from backend.app.database import Base
from backend.app.models.idea import Idea
from scripts import ingest_ideas


def _session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


class IdeaImprovementsTests(unittest.TestCase):
    def test_read_ideas_applies_tag_filter_before_pagination(self):
        session_local = _session_factory()
        db = session_local()
        try:
            db.add_all(
                [
                    Idea(
                        title="idea-old-alpha",
                        content="old alpha",
                        source="test",
                        status="draft",
                        tags=["alpha"],
                        updated_at=datetime(2026, 1, 1, 0, 0, 0),
                    ),
                    Idea(
                        title="idea-middle-beta",
                        content="middle beta",
                        source="test",
                        status="draft",
                        tags=["beta"],
                        updated_at=datetime(2026, 1, 2, 0, 0, 0),
                    ),
                    Idea(
                        title="idea-new-alpha",
                        content="new alpha",
                        source="test",
                        status="draft",
                        tags=["alpha"],
                        updated_at=datetime(2026, 1, 3, 0, 0, 0),
                    ),
                ]
            )
            db.commit()

            ideas = read_ideas(skip=1, limit=1, status=None, tag="alpha", db=db)

            self.assertEqual(len(ideas), 1)
            self.assertEqual(ideas[0].title, "idea-old-alpha")
        finally:
            db.close()

    def test_ingest_text_file_uses_valid_idea_status(self):
        session_local = _session_factory()
        original_session_local = ingest_ideas.SessionLocal
        ingest_ideas.SessionLocal = session_local

        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "sample.txt"
            input_file.write_text("sample idea content", encoding="utf-8")
            ingest_ideas.ingest_text_file(str(input_file))

        db = session_local()
        try:
            saved = db.query(Idea).all()
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0].status, "draft")
        finally:
            db.close()
            ingest_ideas.SessionLocal = original_session_local


if __name__ == "__main__":
    unittest.main()
