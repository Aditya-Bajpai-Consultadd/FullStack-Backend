from pydantic import BaseModel
from typing import Optional


class UserModel(BaseModel):
    username: str
    password: str
    role: str

    class Config:
        from_attributes = True


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    genre: str
    available: bool
    borrowed: int

    class Config:
        from_attributes = True

class BookCreate(BaseModel):
    title: str
    author: str
    genre: str
    available: int
    borrowed: int

class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None
    genre: str | None = None
    available: bool | None = None
    borrowed: int | None = None

class BorrowRequest(BaseModel):
    book_id: int
    username: str



class BorrowResponse(BaseModel):
    message: str

class ReturnRequest(BaseModel):
    book_id: int
    username: str

class ReturnResponse(BaseModel):
    message: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str 

class UserLogin(BaseModel):
    username: str
    password: str