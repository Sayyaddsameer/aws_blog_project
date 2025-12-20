from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)

    # [REQUIREMENT] One-to-Many Relationship & Cascade Delete
    # 'cascade="all, delete"' ensures that when an Author is deleted,
    # all their Posts are automatically deleted by SQLAlchemy.
    posts = relationship("Post", back_populates="author", cascade="all, delete")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # 'ondelete="CASCADE"' ensures the Database (MySQL) also enforces deletion
    author_id = Column(Integer, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False)

    author = relationship("Author", back_populates="posts")
