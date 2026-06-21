import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@db:5432/financas"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def wait_for_database():
    """
    Aguarda até a base de dados estar pronta.
    Isto evita erros quando o backend arranca antes do PostgreSQL estar disponível.
    """
    for attempt in range(10):
        try:
            connection = engine.connect()
            connection.close()
            print("Base de dados ligada com sucesso.")
            return
        except OperationalError:
            print(f"A aguardar pela base de dados... tentativa {attempt + 1}/10")
            time.sleep(2)

    raise Exception("Não foi possível ligar à base de dados.")


def get_db():
    """
    Cria uma sessão de base de dados para cada pedido da API.
    No final do pedido, a sessão é fechada.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
