import asyncio
import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class FinancialDataFetcher(ABC):
    @abstractmethod
    async def fetch_financials(self, ticker: str) -> Dict[str, Any]:
        pass

class YahooFinanceFetcher(FinancialDataFetcher):
    async def fetch_financials(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch balance sheet and income statement from Yahoo Finance.
        Runs in a separate thread to avoid blocking the async loop.
        """
        return await asyncio.to_thread(self._fetch_sync, ticker)

    def _fetch_sync(self, ticker: str) -> Dict[str, Any]:
        print(f"Fetching data for {ticker} from Yahoo Finance...")
        stock = yf.Ticker(ticker)
        
        # Fetch data
        balance_sheet = stock.balance_sheet
        quarterly_balance_sheet = stock.quarterly_balance_sheet
        income_stmt = stock.income_stmt
        quarterly_income_stmt = stock.quarterly_income_stmt
        
        # Basic info
        info = stock.info
        
        return {
            "info": info,
            "balance_sheet": {
                "annual": self._df_to_dict(balance_sheet),
                "quarterly": self._df_to_dict(quarterly_balance_sheet)
            },
            "income_statement": {
                "annual": self._df_to_dict(income_stmt),
                "quarterly": self._df_to_dict(quarterly_income_stmt)
            }
        }

    def _df_to_dict(self, df: pd.DataFrame) -> Dict:
        """Convert DataFrame to a serializable dictionary handling dates"""
        if df is None or df.empty:
            return {}
        
        # Convert index to string (Line Items)
        df.index = df.index.astype(str)
        
        # Convert columns (Dates) to string
        df.columns = df.columns.astype(str)
        
        # Replace NaN with None
        return df.where(pd.notnull(df), None).to_dict()
