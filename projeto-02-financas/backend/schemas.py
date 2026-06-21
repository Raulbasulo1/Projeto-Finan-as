from datetime import date as date_type
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class AccountBase(BaseModel):
    name: str
    type: str
    initial_balance: float = 0


class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class CategoryBase(BaseModel):
    name: str
    type: str = Field(description="income ou expense")


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    description: str
    amount: float
    type: str = Field(description="income ou expense")
    date: date_type
    account_id: int
    category_id: int


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    date: Optional[date_type] = None
    account_id: Optional[int] = None
    category_id: Optional[int] = None


class TransactionRead(TransactionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BudgetBase(BaseModel):
    month: int
    year: int
    limit_amount: float
    category_id: int


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    month: Optional[int] = None
    year: Optional[int] = None
    limit_amount: Optional[float] = None
    category_id: Optional[int] = None


class BudgetRead(BudgetBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
