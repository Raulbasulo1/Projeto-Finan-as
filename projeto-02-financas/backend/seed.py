from datetime import date
from sqlalchemy.orm import Session
from models import Account, Category, Transaction, Budget


def seed_database(db: Session):
    """
    Insere dados iniciais apenas se a base de dados estiver vazia.
    Isto ajuda a demonstrar a aplicação logo no primeiro arranque.
    """

    existing_accounts = db.query(Account).count()

    if existing_accounts > 0:
        return

    accounts = [
        Account(name="Conta à ordem", type="bank", initial_balance=500),
        Account(name="Poupança", type="savings", initial_balance=1200),
        Account(name="Dinheiro", type="cash", initial_balance=100),
    ]

    categories = [
        Category(name="Salário", type="income"),
        Category(name="Alimentação", type="expense"),
        Category(name="Transportes", type="expense"),
        Category(name="Casa", type="expense"),
        Category(name="Lazer", type="expense"),
        Category(name="Saúde", type="expense"),
        Category(name="Educação", type="expense"),
        Category(name="Outros", type="expense"),
    ]

    db.add_all(accounts)
    db.add_all(categories)
    db.commit()

    salary = db.query(Category).filter(Category.name == "Salário").first()
    food = db.query(Category).filter(Category.name == "Alimentação").first()
    transport = db.query(Category).filter(Category.name == "Transportes").first()
    house = db.query(Category).filter(Category.name == "Casa").first()
    leisure = db.query(Category).filter(Category.name == "Lazer").first()

    main_account = db.query(Account).filter(Account.name == "Conta à ordem").first()

    transactions = [
        Transaction(
            description="Salário mensal",
            amount=950,
            type="income",
            date=date(2026, 5, 1),
            account_id=main_account.id,
            category_id=salary.id,
        ),
        Transaction(
            description="Supermercado",
            amount=42.35,
            type="expense",
            date=date(2026, 5, 3),
            account_id=main_account.id,
            category_id=food.id,
        ),
        Transaction(
            description="Passe de transportes",
            amount=30,
            type="expense",
            date=date(2026, 5, 5),
            account_id=main_account.id,
            category_id=transport.id,
        ),
        Transaction(
            description="Renda",
            amount=300,
            type="expense",
            date=date(2026, 5, 7),
            account_id=main_account.id,
            category_id=house.id,
        ),
        Transaction(
            description="Cinema",
            amount=12,
            type="expense",
            date=date(2026, 5, 10),
            account_id=main_account.id,
            category_id=leisure.id,
        ),
    ]

    budgets = [
        Budget(month=5, year=2026, category_id=food.id, limit_amount=250),
        Budget(month=5, year=2026, category_id=transport.id, limit_amount=80),
        Budget(month=5, year=2026, category_id=leisure.id, limit_amount=100),
        Budget(month=5, year=2026, category_id=house.id, limit_amount=350),
    ]

    db.add_all(transactions)
    db.add_all(budgets)
    db.commit()
