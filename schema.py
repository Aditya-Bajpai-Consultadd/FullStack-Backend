from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    username = Column(String(50), unique=True, nullable=False, primary_key=True)
    password = Column(String(255), nullable=False)
    role = Column(String(10), nullable=False)

    borrowed_books = relationship("BorrowedBook", back_populates="user", cascade="all, delete")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False)
    author = Column(String(50), nullable=False)
    genre = Column(String(50), nullable=False)
    available = Column(Integer, default=True)
    borrowed = Column(Integer,nullable=True)

    borrowed_books = relationship("BorrowedBook", back_populates="book", cascade="all, delete")

class BorrowedBook(Base):
    __tablename__ = "borrowedBooks"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), ForeignKey("users.username"), nullable=False)
    bookID = Column(Integer, ForeignKey("books.id"), nullable=False)

    user = relationship("User", back_populates="borrowed_books")
    book = relationship("Book", back_populates="borrowed_books")
