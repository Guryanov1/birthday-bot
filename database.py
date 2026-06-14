from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime

Base = declarative_base()
engine = create_engine("sqlite:///birthdays.db", echo=False)
Session = sessionmaker(bind=engine)

class Birthday(Base):
    __tablename__ = "birthdays"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    telegram_username = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    """Создаёт таблицы в базе данных"""
    Base.metadata.create_all(engine)