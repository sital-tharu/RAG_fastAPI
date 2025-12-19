from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, TIMESTAMP, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    statements = relationship("FinancialStatement", back_populates="company", cascade="all, delete-orphan")

class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    statement_type = Column(String(50), nullable=False)  # 'balance_sheet' or 'income_statement'
    period_type = Column(String(20), nullable=False)     # 'quarterly' or 'annual'
    period_date = Column(Date, nullable=False)
    fiscal_year = Column(Integer)
    fiscal_quarter = Column(Integer)
    source = Column(String(50))
    raw_data = Column(JSON)  # Store original API response
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('company_id', 'statement_type', 'period_type', 'period_date', name='uq_company_statement_period'),
    )

    # Relationships
    company = relationship("Company", back_populates="statements")
    line_items = relationship("FinancialLineItem", back_populates="statement", cascade="all, delete-orphan")

class FinancialLineItem(Base):
    __tablename__ = "financial_line_items"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("financial_statements.id", ondelete="CASCADE"))
    line_item_name = Column(String(255), nullable=False, index=True)
    line_item_value = Column(Numeric(20, 2))
    currency = Column(String(10), default="INR")
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('statement_id', 'line_item_name', name='uq_statement_line_item'),
    )

    # Relationships
    statement = relationship("FinancialStatement", back_populates="line_items")
