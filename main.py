from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from mangum import Mangum
import models, database

# Create tables automatically (useful for simple setup)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Blog API Platform")

# --- Pydantic Schemas (Validation) ---

class AuthorCreate(BaseModel):
    name: str
    email: EmailStr  # [REQUIREMENT] Validates email format

class PostCreate(BaseModel):
    title: str
    content: str
    author_id: int

class AuthorResponse(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        from_attributes = True

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
    class Config:
        from_attributes = True

# [REQUIREMENT] GET /posts/{id} response must include Author details
class PostResponseDetailed(PostResponse):
    author: AuthorResponse

# --- Author Endpoints ---

# [REQUIREMENT] POST /authors
@app.post("/authors", response_model=AuthorResponse)
def create_author(author: AuthorCreate, db: Session = Depends(database.get_db)):
    # Check for unique email
    if db.query(models.Author).filter(models.Author.email == author.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_author = models.Author(name=author.name, email=author.email)
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author

# [REQUIREMENT] GET /authors
@app.get("/authors", response_model=List[AuthorResponse])
def get_authors(db: Session = Depends(database.get_db)):
    return db.query(models.Author).all()

# [REQUIREMENT] GET /authors/{id}
@app.get("/authors/{id}", response_model=AuthorResponse)
def get_single_author(id: int, db: Session = Depends(database.get_db)):
    author = db.query(models.Author).filter(models.Author.id == id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

# [REQUIREMENT] PUT /authors/{id}
@app.put("/authors/{id}", response_model=AuthorResponse)
def update_author(id: int, author_update: AuthorCreate, db: Session = Depends(database.get_db)):
    author = db.query(models.Author).filter(models.Author.id == id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    author.name = author_update.name
    author.email = author_update.email
    db.commit()
    db.refresh(author)
    return author

# [REQUIREMENT] DELETE /authors/{id}
@app.delete("/authors/{id}")
def delete_author(id: int, db: Session = Depends(database.get_db)):
    author = db.query(models.Author).filter(models.Author.id == id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    # [REQUIREMENT] Cascade delete happens here automatically via SQLAlchemy models
    db.delete(author) 
    db.commit()
    return {"message": "Author and associated posts deleted"}

# [REQUIREMENT] Nested Resource Endpoint: GET /authors/{id}/posts
@app.get("/authors/{id}/posts", response_model=List[PostResponse])
def get_posts_by_author(id: int, db: Session = Depends(database.get_db)):
    # Verify author exists first
    author = db.query(models.Author).filter(models.Author.id == id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    return db.query(models.Post).filter(models.Post.author_id == id).all()

# --- Post Endpoints ---

# [REQUIREMENT] POST /posts
@app.post("/posts", response_model=PostResponse)
def create_post(post: PostCreate, db: Session = Depends(database.get_db)):
    # [REQUIREMENT] Return 400 error if author_id does not exist
    if not db.query(models.Author).filter(models.Author.id == post.author_id).first():
        raise HTTPException(status_code=400, detail="Author ID does not exist")
    
    new_post = models.Post(title=post.title, content=post.content, author_id=post.author_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# [REQUIREMENT] GET /posts (with filtering)
@app.get("/posts", response_model=List[PostResponse])
def get_posts(author_id: Optional[int] = None, db: Session = Depends(database.get_db)):
    query = db.query(models.Post)
    if author_id:
        # [REQUIREMENT] Allow filtering by author_id
        query = query.filter(models.Post.author_id == author_id)
    return query.all()

# [REQUIREMENT] GET /posts/{id} (Detailed response)
@app.get("/posts/{id}", response_model=PostResponseDetailed)
def get_single_post(id: int, db: Session = Depends(database.get_db)):
    # [REQUIREMENT] Efficient Queries (N+1 Optimization) using joinedload
    post = db.query(models.Post).options(joinedload(models.Post.author)).filter(models.Post.id == id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# [REQUIREMENT] PUT /posts/{id}
@app.put("/posts/{id}", response_model=PostResponse)
def update_post(id: int, post_update: PostCreate, db: Session = Depends(database.get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.title = post_update.title
    post.content = post_update.content
    db.commit()
    db.refresh(post)
    return post

# [REQUIREMENT] DELETE /posts/{id}
@app.delete("/posts/{id}")
def delete_post(id: int, db: Session = Depends(database.get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(post)
    db.commit()
    return {"message": "Post deleted"}

# --- AWS Lambda Handler ---
handler = Mangum(app)
