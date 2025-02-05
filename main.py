from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import jwtToken
import re
from database import engine, get_db
from schema import Base, Book, BorrowedBook, User
from models import  BookResponse, BookCreate, BookUpdate,UserLogin, BorrowRequest, BorrowResponse, ReturnRequest, ReturnResponse, Token, UserCreate
from fastapi.middleware.cors import CORSMiddleware


Base.metadata.create_all(bind=engine)



app = FastAPI()

origins = [
    "http://localhost:5173",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)




@app.get('/')
def index():
    return {'data': {'name': 'Aditya'}}

PASSWORD_REGEX = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"

@app.post("/register",status_code=200)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = jwtToken.get_password_hash(user.password)
    if not user.username:
        raise HTTPException(status_code=400, detail="Invalid username")
    if not re.match(PASSWORD_REGEX, user.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long, including at least one letter and one number."
        )
    
    new_user = User(username=user.username, password=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return { "message": "success" }

@app.post("/login", response_model=Token)
def login(form_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user :
        raise HTTPException(status_code=401, detail="Invalid Username")
    if not jwtToken.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid Password")
    access_token = jwtToken.create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/admin/books", response_model=list[BookResponse],status_code=200)
def get_books(db: Session = Depends(get_db), user: jwtToken.TokenData = Depends(jwtToken.admin_only)): 
    books = db.query(Book).all()
    if not books:
        return []
    return books

@app.post("/admin/books",status_code=200)
def add_book(book: BookCreate, db: Session = Depends(get_db), user: jwtToken.TokenData = Depends(jwtToken.admin_only)):
    existing_book = db.query(Book).filter(Book.title == book.title, Book.author == book.author).first()
    if existing_book:
        raise HTTPException(status_code=400, detail="Book already exists")
    new_book = Book(
        title=book.title,
        author=book.author,
        genre=book.genre,
        available=book.available,
        borrowed = book.borrowed
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return ({"message": "Book added successfully", "data": new_book})

@app.get("/admin/books/{book_id}", response_model=BookResponse,status_code=200)
def get_book(book_id:int,db: Session = Depends(get_db), user: jwtToken.TokenData = Depends(jwtToken.admin_only)): 
    book = db.query(Book).filter(Book.id ==book_id ).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/admin/books/{book_id}", response_model=BookResponse,status_code=200)
def update_book(book_id: int, book_data: BookUpdate, db: Session = Depends(get_db),user: jwtToken.TokenData = Depends(jwtToken.admin_only)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book_data.title is not None:
        book.title = book_data.title
    if book_data.author is not None:
        book.author = book_data.author
    if book_data.genre is not None:
        book.genre = book_data.genre
    if book_data.available is not None:
        book.available = book_data.available
    db.commit()
    db.refresh(book)
    return book

@app.delete("/admin/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db),user: jwtToken.TokenData = Depends(jwtToken.admin_only)):
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return ({"message": "Book deleted successfully"})

# @app.get("/books", response_model=list[BookResponse])
# def search_books(
#     search: str = Query(..., description="Search by title, author, or genre"),
#     db: Session = Depends(get_db), user: jwtToken.TokenData = Depends(jwtToken.user_only)
# ):
#     books = db.query(Book).filter(
#         (Book.title.ilike(f"%{search}%")) |
#         (Book.author.ilike(f"%{search}%")) |
#         (Book.genre.ilike(f"%{search}%"))
#     ).all()
#     if not books:
#         return []
#     return books
@app.get("/user/books", response_model=list[BookResponse],status_code=200)
def get_books(db: Session = Depends(get_db), user: jwtToken.TokenData = Depends(jwtToken.user_only)): 
    books = db.query(Book).all()
    if not books:
        raise HTTPException(status_code=404, detail="No books found")
    return books

@app.post("/user/borrow/{book_id}", response_model=BorrowResponse)
def borrow_book(book_id:int,borrow_data: BorrowRequest, db: Session = Depends(get_db),user: jwtToken.TokenData = Depends(jwtToken.user_only)):
   book = db.query(Book).filter(Book.id == borrow_data.book_id).first()
   if not book:
        raise HTTPException(status_code=404, detail="Book not found")
   if book.available == 0:
        raise HTTPException(status_code=400, detail="Book not available")

   existing_borrow = db.query(BorrowedBook).filter(
        BorrowedBook.username == borrow_data.username,
        BorrowedBook.bookID == borrow_data.book_id
    ).first()
   if existing_borrow:
        raise HTTPException(status_code=400, detail="You have already borrowed this book")

   borrowed_book = BorrowedBook(username=borrow_data.username, bookID=borrow_data.book_id)
   db.add(borrowed_book)

   book.available = False
   book.borrowed= True
   db.commit()
   return {"message": "success"}

@app.post("/user/return/{book_id}", response_model=ReturnResponse)
def return_book(book_id:int, return_data: ReturnRequest, db: Session = Depends(get_db),user: jwtToken.TokenData = Depends(jwtToken.user_only)):
    borrowed_book = db.query(BorrowedBook).filter(
        BorrowedBook.username == return_data.username, 
        BorrowedBook.bookID == return_data.book_id
    ).first()

    if not borrowed_book:
        raise HTTPException(status_code=404, detail="You have not borrowed this book")

    db.delete(borrowed_book)

    book = db.query(Book).filter(Book.id == book_id).first()
    if book:
        book.available = True
        book.borrowed= False

    db.commit()

    return {"message": "success"}

@app.get("/admin/borrowedBooksAll")
def get_all_borrowed_books( db: Session = Depends(get_db),user: jwtToken.TokenData = Depends(jwtToken.admin_only)):

    borrowed_books = (
        db.query(BorrowedBook)
        .join(Book, BorrowedBook.bookID == Book.id)
        .all()
    )
    return [
        {"id": b.bookID, "title": b.book.title, "author": b.book.author, "genre": b.book.genre, "borrowedBy": b.username}
        for b in borrowed_books
    ]

@app.get("/user/borrowedBooks/{username}")
def get_user_borrowed_books( username: str, db: Session = Depends(get_db), user: jwtToken.TokenData = Depends(jwtToken.user_only)):

    borrowed_books = (  
        db.query(BorrowedBook)
        .join(Book, BorrowedBook.bookID == Book.id)
        .filter(BorrowedBook.username == username)
        .all()
    )

    return [
        {"id": b.bookID, "title": b.book.title, "author": b.book.author, "genre": b.book.genre}
        for b in borrowed_books
    ]