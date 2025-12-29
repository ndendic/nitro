"""
Blog Example - Demonstrates Entity Relationships

This example demonstrates:
1. Foreign key relationships (User -> Posts, Post -> Comments)
2. Nested data queries
3. SQLModel relationships
4. RESTful API design

Run: uvicorn examples.blog_demo:app --reload --port 8004
Then visit: http://localhost:8004/docs
"""

from typing import List, Optional
from fastapi import FastAPI, HTTPException
from sqlmodel import Field, Relationship
from nitro.domain.entities.base_entity import Entity
from nitro.infrastructure.repository.sql import SQLModelRepository


# Define entities with relationships
class User(Entity, table=True):
    """User entity."""
    username: str = Field(unique=True)
    email: str
    bio: Optional[str] = None

    model_config = {"repository_class": SQLModelRepository}


class Post(Entity, table=True):
    """Blog post entity with author relationship."""
    title: str
    content: str
    author_id: str = Field(foreign_key="user.id")

    # Relationship - will be loaded eagerly by repository
    author: Optional[User] = Relationship()

    model_config = {"repository_class": SQLModelRepository}


class Comment(Entity, table=True):
    """Comment entity with post and author relationships."""
    content: str
    post_id: str = Field(foreign_key="post.id")
    author_id: str = Field(foreign_key="user.id")

    # Relationships
    post: Optional[Post] = Relationship()
    author: Optional[User] = Relationship()

    model_config = {"repository_class": SQLModelRepository}


# Initialize FastAPI
app = FastAPI(title="Nitro Blog Demo")


@app.on_event("startup")
async def startup():
    """Initialize database."""
    repo = SQLModelRepository()
    repo.init_db()
    print("✓ Blog database initialized")

    # Create sample data if empty
    users = User.all()
    if not users:
        print("Creating sample data...")

        # Create users
        alice = User(id="alice", username="alice", email="alice@example.com", bio="Tech enthusiast")
        bob = User(id="bob", username="bob", email="bob@example.com", bio="Food blogger")
        alice.save()
        bob.save()

        # Create posts
        post1 = Post(
            id="post1",
            title="Getting Started with Nitro",
            content="Nitro is a set of abstraction layers for building Python web applications...",
            author_id="alice"
        )
        post2 = Post(
            id="post2",
            title="My Favorite Recipes",
            content="Here are some amazing recipes I've discovered...",
            author_id="bob"
        )
        post1.save()
        post2.save()

        # Create comments
        comment1 = Comment(
            id="comment1",
            content="Great post! Very informative.",
            post_id="post1",
            author_id="bob"
        )
        comment2 = Comment(
            id="comment2",
            content="Thanks for sharing!",
            post_id="post2",
            author_id="alice"
        )
        comment1.save()
        comment2.save()

        print("✓ Sample data created")


# User endpoints
@app.get("/users", response_model=List[User])
async def list_users():
    """List all users."""
    return User.all()


@app.post("/users", response_model=User)
async def create_user(user: User):
    """Create a new user."""
    user.save()
    return user


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID."""
    user = User.get(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


# Post endpoints
@app.get("/posts", response_model=List[Post])
async def list_posts():
    """List all posts with author information."""
    return Post.all()


@app.post("/posts", response_model=Post)
async def create_post(post: Post):
    """Create a new post."""
    # Verify author exists
    author = User.get(post.author_id)
    if not author:
        raise HTTPException(404, "Author not found")

    post.save()
    return post


@app.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: str):
    """Get post by ID with author information."""
    post = Post.get(post_id)
    if not post:
        raise HTTPException(404, "Post not found")
    return post


# Comment endpoints
@app.get("/comments", response_model=List[Comment])
async def list_comments():
    """List all comments."""
    return Comment.all()


@app.post("/comments", response_model=Comment)
async def create_comment(comment: Comment):
    """Create a new comment."""
    # Verify post and author exist
    post = Post.get(comment.post_id)
    if not post:
        raise HTTPException(404, "Post not found")

    author = User.get(comment.author_id)
    if not author:
        raise HTTPException(404, "Author not found")

    comment.save()
    return comment


@app.get("/comments/{comment_id}", response_model=Comment)
async def get_comment(comment_id: str):
    """Get comment by ID with relationships."""
    comment = Comment.get(comment_id)
    if not comment:
        raise HTTPException(404, "Comment not found")
    return comment


# Nested data endpoint
@app.get("/posts/{post_id}/full")
async def get_post_full(post_id: str):
    """Get post with all comments and author information."""
    post = Post.get(post_id)
    if not post:
        raise HTTPException(404, "Post not found")

    # Get all comments for this post using filter
    all_comments = Comment.all()
    comments = [c for c in all_comments if c.post_id == post_id]

    return {
        "post": {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author": {
                "id": post.author.id if post.author else None,
                "username": post.author.username if post.author else None,
                "email": post.author.email if post.author else None,
            } if post.author else None
        },
        "comments": [
            {
                "id": c.id,
                "content": c.content,
                "author": {
                    "id": c.author.id if c.author else None,
                    "username": c.author.username if c.author else None,
                } if c.author else None
            }
            for c in comments
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
