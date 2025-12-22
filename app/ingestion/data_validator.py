"""
Data Validation Module

Validates completeness and quality of financial data.
Provides warnings without blocking ingestion.
"""

from typing import List, Dict, Any
from app.ingestion.data_normalizer import StandardizedFinancials
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Validates financial data quality and completeness.
    """
    
    # Minimum expected line items for each statement type
    REQUIRED_INCOME_ITEMS = [
        "Total Revenue", "Revenue", "Net Sales",  # At least one revenue metric
        "Net Income", "Net Profit", "PAT"          # At least one profit metric
    ]
    
    REQUIRED_BALANCE_ITEMS = [
        "Total Assets",                             # Must have total assets
        "Total Liabilities",                        # Must have total liabilities
        "Total Equity", "Stockholders Equity"       # At least one equity metric
    ]
    
    REQUIRED_CASHFLOW_ITEMS = [
        "Operating Cash Flow", "Free Cash Flow", "Cash From Operating Activities"
    ]
    
    def __init__(self):
        self.validation_results = []
    
    def validate_statement(self, financial: StandardizedFinancials) -> Dict[str, Any]:
        """
        Validate a single financial statement.
        
        Args:
            financial: StandardizedFinancials object to validate
            
        Returns:
            Dict with validation results
        """
        result = {
            "statement_type": financial.statement_type,
            "period_type": financial.period_type,
            "period_date": financial.period_date.isoformat(),
            "is_valid": True,
            "warnings": [],
            "line_item_count": len(financial.line_items)
        }
        
        # Check if there are any line items
        if not financial.line_items:
            result["is_valid"] = False
            result["warnings"].append("No line items found in statement")
            return result
        
        # Get list of line item names (case-insensitive)
        line_item_names = [item.name.lower() for item in financial.line_items]
        
        # Check for required items based on statement type
        if financial.statement_type == "income_statement":
            required_items = self.REQUIRED_INCOME_ITEMS
        elif financial.statement_type == "balance_sheet":
            required_items = self.REQUIRED_BALANCE_ITEMS
        elif financial.statement_type == "cash_flow":
            required_items = self.REQUIRED_CASHFLOW_ITEMS
        else:
            result["warnings"].append(f"Unknown statement type: {financial.statement_type}")
            return result
        
        # Check if at least one variant of each required item exists
        missing_items = []
        for required_item in required_items:
            found = any(required_item.lower() in name for name in line_item_names)
            if not found:
                missing_items.append(required_item)
        
        if missing_items:
            # Not a hard failure, but warn about missing items
            result["warnings"].append(
                f"Missing recommended items: {', '.join(missing_items[:3])}"
                + (f" and {len(missing_items) - 3} more" if len(missing_items) > 3 else "")
            )
        
        # Check for suspiciously few line items
        min_expected = 5
        if len(financial.line_items) < min_expected:
            result["warnings"].append(
                f"Only {len(financial.line_items)} line items found, expected at least {min_expected}"
            )
        
        # Check for all-zero or all-null values
        non_zero_count = sum(1 for item in financial.line_items if item.value != 0)
        if non_zero_count == 0:
            result["warnings"].append("All line items have zero values")
        elif non_zero_count < len(financial.line_items) * 0.3:
            result["warnings"].append(
                f"High percentage of zero values: {non_zero_count}/{len(financial.line_items)}"
            )
        
        return result
    
    def validate_company_data(self, 
                             ticker: str,
                             financials_list: List[StandardizedFinancials]) -> Dict[str, Any]:
        """
        Validate all financial data for a company.
        
        Args:
            ticker: Company ticker symbol
            financials_list: List of all financial statements
            
        Returns:
            Dict with overall validation summary
        """
        summary = {
            "ticker": ticker,
            "total_statements": len(financials_list),
            "valid_statements": 0,
            "warnings": [],
            "statements_by_type": {},
            "date_range": None
        }
        
        if not financials_list:
            summary["warnings"].append("No financial statements found")
            return summary
        
        # Validate each statement
        statement_results = []
        for fin in financials_list:
            result = self.validate_statement(fin)
            statement_results.append(result)
            
            if result["is_valid"]:
                summary["valid_statements"] += 1
            
            # Count by statement type
            stmt_type = fin.statement_type
            if stmt_type not in summary["statements_by_type"]:
                summary["statements_by_type"][stmt_type] = {
                    "count": 0,
                    "annual": 0,
                    "quarterly": 0
                }
            summary["statements_by_type"][stmt_type]["count"] += 1
            if fin.period_type == "annual":
                summary["statements_by_type"][stmt_type]["annual"] += 1
            else:
                summary["statements_by_type"][stmt_type]["quarterly"] += 1
        
        # Determine date range
        dates = [fin.period_date for fin in financials_list]
        if dates:
            summary["date_range"] = {
                "earliest": min(dates).isoformat(),
                "latest": max(dates).isoformat()
            }
        
        # Check for statement type balance
        expected_types = ["income_statement", "balance_sheet", "cash_flow"]
        for stmt_type in expected_types:
            if stmt_type not in summary["statements_by_type"]:
                summary["warnings"].append(f"No {stmt_type} data found")
        
        # Check for sufficient historical data
        unique_years = set(fin.fiscal_year for fin in financials_list)
        if len(unique_years) < 2:
            summary["warnings"].append(
                f"Limited historical data: only {len(unique_years)} year(s) available"
            )
        
        # Aggregate warnings from individual statements
        all_warnings = []
        for result in statement_results:
            if result["warnings"]:
                all_warnings.extend([
                    f"{result['statement_type']} ({result['period_date']}): {w}"
                    for w in result["warnings"]
                ])
        
        # Add top warnings to summary (limit to 5)
        if all_warnings:
            summary["detail_warnings"] = all_warnings[:5]
            if len(all_warnings) > 5:
                summary["warnings"].append(f"...and {len(all_warnings) - 5} more warnings")
        
        # Log validation summary
        logger.info(f"Validation complete for {ticker}: "
                   f"{summary['valid_statements']}/{summary['total_statements']} valid statements")
        
        if summary["warnings"]:
            logger.warning(f"Validation warnings for {ticker}: {summary['warnings']}")
        
        return summary
