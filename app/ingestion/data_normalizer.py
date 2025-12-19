from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from dateutil import parser

class LineItem(BaseModel):
    name: str
    value: float

class StandardizedFinancials(BaseModel):
    statement_type: str
    period_type: str
    period_date: datetime
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    line_items: List[LineItem]
    raw_data: Dict

class DataNormalizer:
    def normalize(self, raw_data: Dict[str, Any]) -> List[StandardizedFinancials]:
        """Convert raw yfinance data into list of StandardizedFinancials"""
        normalized_data = []
        
        # Process Balance Sheets
        bs_data = raw_data.get("balance_sheet", {})
        normalized_data.extend(self._process_statement(bs_data.get("annual", {}), "balance_sheet", "annual"))
        normalized_data.extend(self._process_statement(bs_data.get("quarterly", {}), "balance_sheet", "quarterly"))
        
        # Process Income Statements
        is_data = raw_data.get("income_statement", {})
        normalized_data.extend(self._process_statement(is_data.get("annual", {}), "income_statement", "annual"))
        normalized_data.extend(self._process_statement(is_data.get("quarterly", {}), "income_statement", "quarterly"))
        
        return normalized_data

    def _process_statement(self, data: Dict, statement_type: str, period_type: str) -> List[StandardizedFinancials]:
        result = []
        if not data:
            return result
            
        # Yahoo Finance structure: { "date_str": { "Line Item": value, ... } }
        # Note: In our fetcher we converted df to dict, so it might be { "date_str": { "Line Item": value } } 
        # But actually df.to_dict() usually gives { "date_col": { "index_row": val } } which matches above.
        
        for date_str, items in data.items():
            try:
                period_date = parser.parse(date_str)
                line_items = []
                
                for name, value in items.items():
                    if value is not None:
                        # Ensure value is float
                        try:
                            val_float = float(value)
                            line_items.append(LineItem(name=name, value=val_float))
                        except (ValueError, TypeError):
                            continue
                
                if not line_items:
                    continue
                    
                # Estimate fiscal year/quarter
                fiscal_year = period_date.year
                fiscal_quarter = (period_date.month - 1) // 3 + 1
                
                result.append(StandardizedFinancials(
                    statement_type=statement_type,
                    period_type=period_type,
                    period_date=period_date,
                    fiscal_year=fiscal_year,
                    fiscal_quarter=fiscal_quarter,
                    line_items=line_items,
                    raw_data=items
                ))
            except Exception as e:
                print(f"Error normalizing data for date {date_str}: {e}")
                continue
                
        return result
