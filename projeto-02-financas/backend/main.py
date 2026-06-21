from datetime import date
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io
from fastapi.responses import StreamingResponse


from database import Base, engine, get_db, wait_for_database, SessionLocal
from models import Account, Category, Transaction, Budget
from schemas import (
    AccountCreate,
    AccountRead,
    CategoryCreate,
    CategoryRead,
    TransactionCreate,
    TransactionUpdate,
    TransactionRead,
    BudgetCreate,
    BudgetUpdate,
    BudgetRead,
)
from seed import seed_database


app = FastAPI(
    title="API de Finanças Pessoais",
    description="API REST para gestão e análise de receitas, despesas, categorias, contas e orçamentos.",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """
    No arranque da aplicação:
    1. Aguarda pela base de dados.
    2. Cria as tabelas, se ainda não existirem.
    3. Insere dados iniciais, se a base estiver vazia.
    """
    wait_for_database()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "API de Finanças Pessoais a funcionar"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


# -------------------------
# CONTAS
# -------------------------

@app.get("/accounts", response_model=list[AccountRead])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).order_by(Account.id).all()


@app.post("/accounts", response_model=AccountRead)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    new_account = Account(**account.model_dump())
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account

@app.delete("/accounts/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    transactions_count = (
        db.query(Transaction)
        .filter(Transaction.account_id == account_id)
        .count()
    )

    if transactions_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Não é possível remover uma conta que já tem transações associadas."
        )

    db.delete(account)
    db.commit()

    return {
        "message": "Conta removida com sucesso."
    }

# -------------------------
# CATEGORIAS
# -------------------------

@app.get("/categories", response_model=list[CategoryRead])
def list_categories(
    type: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Category)

    if type:
        query = query.filter(Category.type == type)

    return query.order_by(Category.id).all()


@app.post("/categories", response_model=CategoryRead)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    new_category = Category(**category.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


# -------------------------
# TRANSAÇÕES
# -------------------------

@app.get("/transactions", response_model=list[TransactionRead])
def list_transactions(
    type: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    account_id: int | None = Query(default=None),
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Transaction)

    if type:
        query = query.filter(Transaction.type == type)

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    if year:
        query = query.filter(func.extract("year", Transaction.date) == year)

    if month:
        query = query.filter(func.extract("month", Transaction.date) == month)

    return query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()


@app.post("/transactions", response_model=TransactionRead)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    category = db.query(Category).filter(Category.id == transaction.category_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    new_transaction = Transaction(**transaction.model_dump())
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


@app.get("/transactions/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")

    return transaction


@app.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")

    update_data = transaction_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada.")

    db.delete(transaction)
    db.commit()

    return {
        "message": "Transação removida com sucesso."
    }


# -------------------------
# ORÇAMENTOS
# -------------------------

@app.get("/budgets", response_model=list[BudgetRead])
def list_budgets(
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(Budget)

    if year:
        query = query.filter(Budget.year == year)

    if month:
        query = query.filter(Budget.month == month)

    return query.order_by(Budget.year.desc(), Budget.month.desc()).all()


@app.post("/budgets", response_model=BudgetRead)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == budget.category_id).first()

    if not category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada.")

    new_budget = Budget(**budget.model_dump())
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


@app.put("/budgets/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    budget_update: BudgetUpdate,
    db: Session = Depends(get_db)
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    update_data = budget_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(budget, field, value)

    db.commit()
    db.refresh(budget)
    return budget


@app.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado.")

    db.delete(budget)
    db.commit()

    return {
        "message": "Orçamento removido com sucesso."
    }


# -------------------------
# DASHBOARD
# -------------------------

@app.get("/dashboard/summary")
def dashboard_summary(
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query_income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.type == "income"
    )

    query_expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.type == "expense"
    )

    if year:
        query_income = query_income.filter(func.extract("year", Transaction.date) == year)
        query_expense = query_expense.filter(func.extract("year", Transaction.date) == year)

    if month:
        query_income = query_income.filter(func.extract("month", Transaction.date) == month)
        query_expense = query_expense.filter(func.extract("month", Transaction.date) == month)

    total_income = float(query_income.scalar() or 0)
    total_expense = float(query_expense.scalar() or 0)
    balance = total_income - total_expense

    total_budget = 0

    budget_query = db.query(func.coalesce(func.sum(Budget.limit_amount), 0))

    if year:
        budget_query = budget_query.filter(Budget.year == year)

    if month:
        budget_query = budget_query.filter(Budget.month == month)

    total_budget = float(budget_query.scalar() or 0)

    budget_usage = 0

    if total_budget > 0:
        budget_usage = round((total_expense / total_budget) * 100, 2)

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": balance,
        "total_budget": total_budget,
        "budget_usage_percent": budget_usage
    }


@app.get("/dashboard/categories")
def dashboard_categories(
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Category.name, func.coalesce(func.sum(Transaction.amount), 0))
        .join(Transaction, Transaction.category_id == Category.id)
        .filter(Transaction.type == "expense")
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
    )

    if year:
        query = query.filter(func.extract("year", Transaction.date) == year)

    if month:
        query = query.filter(func.extract("month", Transaction.date) == month)

    results = query.all()

    return [
        {
            "category": item[0],
            "total": float(item[1])
        }
        for item in results
    ]


@app.get("/dashboard/monthly")
def dashboard_monthly(
    year: int = Query(default=2026),
    db: Session = Depends(get_db)
):
    data = []

    for month in range(1, 13):
        income = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.type == "income",
            func.extract("year", Transaction.date) == year,
            func.extract("month", Transaction.date) == month
        ).scalar()

        expense = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
            Transaction.type == "expense",
            func.extract("year", Transaction.date) == year,
            func.extract("month", Transaction.date) == month
        ).scalar()

        data.append({
            "month": month,
            "income": float(income or 0),
            "expense": float(expense or 0),
            "balance": float((income or 0) - (expense or 0))
        })

    return data


@app.get("/dashboard/health")
def dashboard_health(
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    summary = dashboard_summary(year=year, month=month, db=db)

    income = summary["total_income"]
    expense = summary["total_expense"]

    if income == 0:
        score = 0
    else:
        score = round(((income - expense) / income) * 100, 2)

    if score >= 30:
        status = "Boa"
    elif score >= 0:
        status = "Moderada"
    else:
        status = "Crítica"

    return {
        "score": score,
        "status": status,
        "message": f"Situação financeira {status.lower()} para o período selecionado."
    }

@app.get("/dashboard/budgets-analysis")
def dashboard_budgets_analysis(
    year: int = Query(default=2026),
    month: int = Query(default=5),
    db: Session = Depends(get_db)
):
    """
    Analisa os orçamentos definidos para um determinado mês e compara
    cada limite com as despesas reais registadas na mesma categoria.
    """

    budgets = (
        db.query(Budget)
        .filter(Budget.year == year, Budget.month == month)
        .order_by(Budget.id)
        .all()
    )

    analysis = []

    for budget in budgets:
        spent = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.type == "expense",
                Transaction.category_id == budget.category_id,
                func.extract("year", Transaction.date) == year,
                func.extract("month", Transaction.date) == month,
            )
            .scalar()
        )

        spent = float(spent or 0)
        limit_amount = float(budget.limit_amount)

        if limit_amount > 0:
            percentage = round((spent / limit_amount) * 100, 2)
        else:
            percentage = 0

        if percentage >= 100:
            status = "Ultrapassado"
        elif percentage >= 80:
            status = "Atenção"
        else:
            status = "Dentro do limite"

        analysis.append({
            "budget_id": budget.id,
            "category_id": budget.category_id,
            "category": budget.category.name,
            "month": budget.month,
            "year": budget.year,
            "limit_amount": limit_amount,
            "spent": spent,
            "remaining": round(limit_amount - spent, 2),
            "percentage": percentage,
            "status": status
        })

    return analysis

# -------------------------
# EXPORTAÇÃO
# -------------------------

@app.get("/export/transactions.csv")
def export_transactions_csv(
    year: int | None = Query(default=None),
    month: int | None = Query(default=None),
    type: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    """
    Exporta as transações para um ficheiro CSV.
    Pode exportar todas as transações ou apenas as transações filtradas
    por ano, mês e tipo.
    """

    query = db.query(Transaction)

    if year:
        query = query.filter(func.extract("year", Transaction.date) == year)

    if month:
        query = query.filter(func.extract("month", Transaction.date) == month)

    if type:
        query = query.filter(Transaction.type == type)

    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")

    writer.writerow([
        "ID",
        "Data",
        "Descrição",
        "Tipo",
        "Categoria",
        "Conta",
        "Valor"
    ])

    for transaction in transactions:
        writer.writerow([
            transaction.id,
            transaction.date,
            transaction.description,
            "Receita" if transaction.type == "income" else "Despesa",
            transaction.category.name if transaction.category else "",
            transaction.account.name if transaction.account else "",
            transaction.amount
        ])

    output.seek(0)

    filename = "transacoes_financas.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@app.get("/dashboard/accounts")
def dashboard_accounts(db: Session = Depends(get_db)):
    """
    Calcula o saldo atual de cada conta com base no saldo inicial,
    nas receitas e nas despesas associadas.
    """

    accounts = db.query(Account).order_by(Account.id).all()
    result = []

    for account in accounts:
        income = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.account_id == account.id,
                Transaction.type == "income"
            )
            .scalar()
        )

        expense = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.account_id == account.id,
                Transaction.type == "expense"
            )
            .scalar()
        )

        income = float(income or 0)
        expense = float(expense or 0)
        initial_balance = float(account.initial_balance or 0)
        current_balance = initial_balance + income - expense

        result.append({
            "id": account.id,
            "name": account.name,
            "type": account.type,
            "initial_balance": initial_balance,
            "income": income,
            "expense": expense,
            "current_balance": current_balance
        })

    return result
