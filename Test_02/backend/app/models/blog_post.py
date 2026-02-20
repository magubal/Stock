"""
Blog Investor Digest - DB Models
- BlogPost: 투자자 블로그 수집글 (메타+본문텍스트+이미지경로)
- BlogSummary: AI 자동 정리본 (내용요약/핵심관점/시사점) + 사용자 수정
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    blogger = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False, unique=True)
    pub_date = Column(DateTime(timezone=True), nullable=True)
    text_content = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    image_size_kb = Column(Integer, default=0)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(20), default="COLLECTOR")  # COLLECTOR or DEMO

    summaries = relationship("BlogSummary", back_populates="post", cascade="all, delete-orphan")


class BlogSummary(Base):
    __tablename__ = "blog_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("blog_posts.id"), nullable=False, index=True)
    summary = Column(Text, nullable=True)
    viewpoint = Column(Text, nullable=True)
    implications = Column(Text, nullable=True)
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    ai_model = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("BlogPost", back_populates="summaries")
