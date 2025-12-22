"""
Financial Ratio Calculator

Computes key financial ratios and metrics from financial statements.
All ratios are computed outside the LLM to ensure accuracy.
"""

from typing import Dict, List, Optional
from app.ingestion.data_normalizer import StandardizedFinancials, LineItem
import logging

logger = logging.getLogger(__name__)


class RatioCalculator:
    """
    Calculates financial ratios from standardized financial data.
    Follows strict error handling to prevent crashes.
    """
    
    def __init__(self):
        # Mapping of common line item names to standardized keys
        self.line_item_aliases = {
            # Revenue variations
            "total_revenue": ["Total Revenue", "Revenue", "Net Sales", "Total Sales", "Turnover"],
            # Profit variations
            "net_income": ["Net Income", "Net Profit", "Profit After Tax", "PAT", "Net Earnings"],
            "operating_income": ["Operating Income", "Operating Profit", "EBIT"],
            # Asset variations
            "total_assets": ["Total Assets", "Total Asset"],
            "current_assets": ["Current Assets", "Total Current Assets"],
            # Liability variations
            "total_liabilities": ["Total Liabilities", "Total Liability"],
            "current_liabilities": ["Current Liabilities", "Total Current Liabilities"],
            # Equity variations
            "total_equity": ["Total Equity", "Stockholders Equity", "Shareholders Equity", 
                           "Total Stockholders Equity", "Total Shareholders Equity"],
            # Debt variations
            "total_debt": ["Total Debt", "Long Term Debt", "Total Long Term Debt"],
        }
    
    def find_line_item_value(self, line_items: List[LineItem], target_key: str) -> Optional[float]:
        """
        Find a line item value using aliases.
        
        Args:
            line_items: List of LineItem objects
            target_key: Key from line_item_aliases
            
        Returns:
            Float value if found, None otherwise
        """
        if target_key not in self.line_item_aliases:
            return None
            
        aliases = self.line_item_aliases[target_key]
        
        for item in line_items:
            for alias in aliases:
                if alias.lower() in item.name.lower() or item.name.lower() in alias.lower():
                    return item.value
        
        return None
    
    def calculate_ratios(self, financials_list: List[StandardizedFinancials]) -> List[LineItem]:
        """
        Calculate financial ratios from a list of financial statements.
        
        Args:
            financials_list: List of StandardizedFinancials for a single period
            
        Returns:
            List of LineItem objects representing calculated ratios
        """
        ratios = []
        
        try:
            # Group statements by type
            statements_by_type = {}
            for fin in financials_list:
                statements_by_type[fin.statement_type] = fin
            
            # Get income statement
            income_stmt = statements_by_type.get("income_statement")
            # Get balance sheet
            balance_sheet = statements_by_type.get("balance_sheet")
            
            if not income_stmt and not balance_sheet:
                logger.warning("No income statement or balance sheet found for ratio calculation")
                return ratios
            
            # Calculate Profitability Ratios
            if income_stmt:
                revenue = self.find_line_item_value(income_stmt.line_items, "total_revenue")
                net_income = self.find_line_item_value(income_stmt.line_items, "net_income")
                operating_income = self.find_line_item_value(income_stmt.line_items, "operating_income")
                
                # Net Profit Margin = Net Income / Revenue
                if revenue and net_income and revenue != 0:
                    net_profit_margin = (net_income / revenue) * 100
                    ratios.append(LineItem(
                        name="Net Profit Margin (%)",
                        value=round(net_profit_margin, 2)
                    ))
                
                # Operating Profit Margin = Operating Income / Revenue
                if revenue and operating_income and revenue != 0:
                    operating_margin = (operating_income / revenue) * 100
                    ratios.append(LineItem(
                        name="Operating Profit Margin (%)",
                        value=round(operating_margin, 2)
                    ))
            
            # Calculate Return Ratios (need both income and balance sheet)
            if income_stmt and balance_sheet:
                net_income = self.find_line_item_value(income_stmt.line_items, "net_income")
                total_assets = self.find_line_item_value(balance_sheet.line_items, "total_assets")
                total_equity = self.find_line_item_value(balance_sheet.line_items, "total_equity")
                
                # ROA = Net Income / Total Assets
                if net_income and total_assets and total_assets != 0:
                    roa = (net_income / total_assets) * 100
                    ratios.append(LineItem(
                        name="Return on Assets (ROA) (%)",
                        value=round(roa, 2)
                    ))
                
                # ROE = Net Income / Total Equity
                if net_income and total_equity and total_equity != 0:
                    roe = (net_income / total_equity) * 100
                    ratios.append(LineItem(
                        name="Return on Equity (ROE) (%)",
                        value=round(roe, 2)
                    ))
            
            # Calculate Leverage Ratios
            if balance_sheet:
                total_debt = self.find_line_item_value(balance_sheet.line_items, "total_debt")
                total_equity = self.find_line_item_value(balance_sheet.line_items, "total_equity")
                total_assets = self.find_line_item_value(balance_sheet.line_items, "total_assets")
                total_liabilities = self.find_line_item_value(balance_sheet.line_items, "total_liabilities")
                
                # Debt-to-Equity Ratio
                if total_debt and total_equity and total_equity != 0:
                    debt_to_equity = total_debt / total_equity
                    ratios.append(LineItem(
                        name="Debt-to-Equity Ratio",
                        value=round(debt_to_equity, 2)
                    ))
                
                # Debt-to-Assets Ratio
                if total_debt and total_assets and total_assets != 0:
                    debt_to_assets = (total_debt / total_assets) * 100
                    ratios.append(LineItem(
                        name="Debt-to-Assets Ratio (%)",
                        value=round(debt_to_assets, 2)
                    ))
                
                # Equity Ratio
                if total_equity and total_assets and total_assets != 0:
                    equity_ratio = (total_equity / total_assets) * 100
                    ratios.append(LineItem(
                        name="Equity Ratio (%)",
                        value=round(equity_ratio, 2)
                    ))
            
            # Calculate Liquidity Ratios
            if balance_sheet:
                current_assets = self.find_line_item_value(balance_sheet.line_items, "current_assets")
                current_liabilities = self.find_line_item_value(balance_sheet.line_items, "current_liabilities")
                
                # Current Ratio
                if current_assets and current_liabilities and current_liabilities != 0:
                    current_ratio = current_assets / current_liabilities
                    ratios.append(LineItem(
                        name="Current Ratio",
                        value=round(current_ratio, 2)
                    ))
            
            logger.info(f"Calculated {len(ratios)} financial ratios")
            
        except Exception as e:
            logger.error(f"Error calculating ratios: {e}", exc_info=True)
            # Return partial results if any were calculated before error
        
        return ratios
    
    def calculate_growth_rates(self, current_fin: StandardizedFinancials, 
                              prior_fin: StandardizedFinancials) -> List[LineItem]:
        """
        Calculate year-over-year growth rates for key metrics.
        
        Args:
            current_fin: Current period financial data
            prior_fin: Prior period financial data (same statement type)
            
        Returns:
            List of LineItem objects with growth rates
        """
        growth_rates = []
        
        try:
            if current_fin.statement_type != prior_fin.statement_type:
                logger.warning(f"Cannot compare different statement types: "
                             f"{current_fin.statement_type} vs {prior_fin.statement_type}")
                return growth_rates
            
            # Key metrics to track growth
            key_metrics = ["total_revenue", "net_income", "total_assets", "total_equity"]
            
            for metric_key in key_metrics:
                current_value = self.find_line_item_value(current_fin.line_items, metric_key)
                prior_value = self.find_line_item_value(prior_fin.line_items, metric_key)
                
                if current_value and prior_value and prior_value != 0:
                    growth_rate = ((current_value - prior_value) / abs(prior_value)) * 100
                    
                    # Get human-readable name
                    metric_name = self.line_item_aliases[metric_key][0]
                    
                    growth_rates.append(LineItem(
                        name=f"{metric_name} Growth Rate (YoY) (%)",
                        value=round(growth_rate, 2)
                    ))
            
            logger.info(f"Calculated {len(growth_rates)} growth rates")
            
        except Exception as e:
            logger.error(f"Error calculating growth rates: {e}", exc_info=True)
        
        return growth_rates
