from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Author(Base):
    __tablename__ = "authors"

    # [REQUIREMENT] Data Models: Author must have id, name, and unique email
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)

    # [REQUIREMENT] Data Integrity: Cascade delete (Deleting Author deletes their Posts)
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"

    # [REQUIREMENT] Data Models: Post must have id, title, content, author_id
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # [REQUIREMENT] Database Design: Foreign Key constraint
    author_id = Column(Integer, ForeignKey("authors.id", ondelete="CASCADE"), nullable=False)

    author = relationship("Author", back_populates="posts")