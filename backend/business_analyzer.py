"""Business analysis module for Monday BI Agent.

This module provides the BusinessAnalyzer class that performs business intelligence
calculations on cleaned deal and work order data, including pipeline analysis,
revenue metrics, and work order tracking.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusinessAnalyzer:
    """Performs business intelligence analysis on deals and work orders.
    
    This class provides methods to analyze pipeline data, calculate revenue metrics,
    track work orders, and generate business summaries.
    """
    
    def __init__(self):
        """Initialize BusinessAnalyzer."""
        logger.info("BusinessAnalyzer initialized")
    
    def pipeline_summary(self, deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate pipeline summary with key metrics.
        
        Args:
            deals: List of cleaned deal items from Monday.com.
            
        Returns:
            dict: Pipeline summary with deal counts and financial metrics.
        """
        if not deals:
            logger.warning("No deals provided for pipeline summary")
            return {
                'total_deals': 0,
                'total_pipeline_value': 0.0,
                'average_deal_size': 0.0,
                'won_deals': 0,
                'lost_deals': 0,
                'open_deals': 0,
                'win_rate': 0.0
            }
        
        try:
            total_deals = len(deals)
            total_value = 0.0
            won_count = 0
            lost_count = 0
            open_count = 0
            
            for deal in deals:
                try:
                    # Extract status
                    status = self._extract_field(deal, 'status')
                    
                    # Extract deal value
                    value = self._extract_numeric_field(deal, ['amount', 'value', 'deal value', 'price'])
                    if value is not None:
                        total_value += value
                    
                    # Count by status
                    if status:
                        status_lower = status.lower()
                        if 'won' in status_lower:
                            won_count += 1
                        elif 'lost' in status_lower:
                            lost_count += 1
                        elif 'open' in status_lower or 'pending' in status_lower:
                            open_count += 1
                    else:
                        open_count += 1
                
                except Exception as e:
                    logger.debug(f"Error processing deal {deal.get('id')}: {str(e)}")
                    continue
            
            # Calculate metrics
            average_deal_size = total_value / total_deals if total_deals > 0 else 0.0
            
            # Calculate win rate (won / (won + lost))
            closable_deals = won_count + lost_count
            win_rate = (won_count / closable_deals * 100) if closable_deals > 0 else 0.0
            
            result = {
                'total_deals': total_deals,
                'total_pipeline_value': round(total_value, 2),
                'average_deal_size': round(average_deal_size, 2),
                'won_deals': won_count,
                'lost_deals': lost_count,
                'open_deals': open_count,
                'win_rate': round(win_rate, 2)
            }
            
            logger.info(f"Pipeline summary: {total_deals} deals, ₹{total_value:.2f} total value")
            return result
            
        except Exception as e:
            logger.error(f"Error generating pipeline summary: {str(e)}")
            return {
                'total_deals': 0,
                'total_pipeline_value': 0.0,
                'average_deal_size': 0.0,
                'won_deals': 0,
                'lost_deals': 0,
                'open_deals': 0,
                'win_rate': 0.0,
                'error': str(e)
            }
    
    def revenue_by_sector(self, deals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group and sum revenue by sector.
        
        Args:
            deals: List of cleaned deal items.
            
        Returns:
            list: List of sectors with revenue, sorted descending.
        """
        if not deals:
            logger.warning("No deals provided for sector analysis")
            return []
        
        try:
            sector_revenue = defaultdict(float)
            
            for deal in deals:
                try:
                    sector = self._extract_field(deal, 'sector')
                    value = self._extract_numeric_field(deal, ['amount', 'value', 'deal value', 'price'])
                    
                    if sector and value is not None:
                        sector_revenue[sector] += value
                    elif value is not None and not sector:
                        sector_revenue['Unknown'] += value
                
                except Exception as e:
                    logger.debug(f"Error processing deal for sector: {str(e)}")
                    continue
            
            # Convert to list and sort
            result = [
                {'sector': sector, 'revenue': round(revenue, 2)}
                for sector, revenue in sector_revenue.items()
            ]
            result = sorted(result, key=lambda x: x['revenue'], reverse=True)
            
            logger.info(f"Revenue by sector: {len(result)} sectors analyzed")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing revenue by sector: {str(e)}")
            return []
    
    def top_clients(self, deals: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top clients by deal value.
        
        Args:
            deals: List of cleaned deal items.
            limit: Number of top clients to return.
            
        Returns:
            list: Top clients with their total deal values.
        """
        if not deals:
            logger.warning("No deals provided for client analysis")
            return []
        
        try:
            client_value = defaultdict(float)
            
            for deal in deals:
                try:
                    # Try multiple client field names
                    client = self._extract_field(deal, ['client', 'company', 'customer', 'account'])
                    value = self._extract_numeric_field(deal, ['amount', 'value', 'deal value', 'price'])
                    
                    if client and value is not None:
                        client_value[client] += value
                
                except Exception as e:
                    logger.debug(f"Error processing deal for clients: {str(e)}")
                    continue
            
            # Sort and limit
            result = [
                {'client': client, 'total_value': round(value, 2)}
                for client, value in client_value.items()
            ]
            result = sorted(result, key=lambda x: x['total_value'], reverse=True)[:limit]
            
            logger.info(f"Top {len(result)} clients identified")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing top clients: {str(e)}")
            return []
    
    def deal_stage_distribution(self, deals: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count deals by stage/status.
        
        Args:
            deals: List of cleaned deal items.
            
        Returns:
            dict: Distribution of deals by stage.
        """
        if not deals:
            logger.warning("No deals provided for stage distribution")
            return {}
        
        try:
            distribution = defaultdict(int)
            
            for deal in deals:
                try:
                    status = self._extract_field(deal, 'status')
                    if status:
                        distribution[status] += 1
                    else:
                        distribution['Unknown'] += 1
                
                except Exception as e:
                    logger.debug(f"Error processing deal status: {str(e)}")
                    continue
            
            result = dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))
            logger.info(f"Deal stage distribution: {len(result)} stages")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing deal stage distribution: {str(e)}")
            return {}
    
    def delayed_work_orders(self, work_orders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify overdue work orders.
        
        Args:
            work_orders: List of cleaned work order items.
            
        Returns:
            list: List of overdue work orders.
        """
        if not work_orders:
            logger.warning("No work orders provided")
            return []
        
        try:
            overdue = []
            today = datetime.now().date()
            
            for wo in work_orders:
                try:
                    # Check status - ignore if completed
                    status = self._extract_field(wo, ['execution status', 'status', 'work status'])
                    if status and ('completed' in status.lower() or 'closed' in status.lower() or 'executed' in status.lower()):
                        continue
                    
                    # Check due/completion date - look for work order specific fields
                    due_date = self._extract_date_field(wo, ['probable end date', 'data delivery date', 'due date', 'deadline', 'completion date'])
                    
                    if due_date and due_date.date() < today:
                        overdue.append({
                            'id': wo.get('id'),
                            'name': wo.get('name'),
                            'due_date': due_date.isoformat(),
                            'status': status or 'Unknown',
                            'days_overdue': (today - due_date.date()).days
                        })
                
                except Exception as e:
                    logger.debug(f"Error processing work order {wo.get('id')}: {str(e)}")
                    continue
            
            result = sorted(overdue, key=lambda x: x['days_overdue'], reverse=True)
            logger.info(f"Found {len(result)} overdue work orders")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing delayed work orders: {str(e)}")
            return []
    
    def work_order_summary(self, work_orders: List[Dict[str, Any]]) -> Dict[str, int]:
        """Generate work order summary statistics.
        
        Args:
            work_orders: List of cleaned work order items.
            
        Returns:
            dict: Summary of work order counts by status.
        """
        if not work_orders:
            logger.warning("No work orders provided for summary")
            return {
                'total_work_orders': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'overdue': 0
            }
        
        try:
            total = len(work_orders)
            completed_count = 0
            in_progress_count = 0
            pending_count = 0
            overdue_count = 0
            today = datetime.now().date()
            
            for wo in work_orders:
                try:
                    status = self._extract_field(wo, 'status')
                    
                    if status:
                        status_lower = status.lower()
                        
                        if 'completed' in status_lower or 'closed' in status_lower or 'done' in status_lower:
                            completed_count += 1
                        elif 'progress' in status_lower or 'in progress' in status_lower:
                            in_progress_count += 1
                        elif 'pending' in status_lower or 'open' in status_lower:
                            pending_count += 1
                    else:
                        pending_count += 1
                    
                    # Check if overdue
                    if status and 'completed' not in status.lower():
                        due_date = self._extract_date_field(wo, ['due date', 'deadline', 'completion date'])
                        if due_date and due_date.date() < today:
                            overdue_count += 1
                
                except Exception as e:
                    logger.debug(f"Error processing work order: {str(e)}")
                    continue
            
            result = {
                'total_work_orders': total,
                'completed': completed_count,
                'in_progress': in_progress_count,
                'pending': pending_count,
                'overdue': overdue_count
            }
            
            logger.info(f"Work order summary: {total} total, {completed_count} completed, {overdue_count} overdue")
            return result
            
        except Exception as e:
            logger.error(f"Error generating work order summary: {str(e)}")
            return {
                'total_work_orders': 0,
                'completed': 0,
                'in_progress': 0,
                'pending': 0,
                'overdue': 0,
                'error': str(e)
            }
    
    def monthly_pipeline(self, deals: List[Dict[str, Any]]) -> Dict[str, float]:
        """Group pipeline value by month.
        
        Args:
            deals: List of cleaned deal items.
            
        Returns:
            dict: Pipeline value grouped by month (Jan, Feb, etc.).
        """
        if not deals:
            logger.warning("No deals provided for monthly analysis")
            return {}
        
        try:
            monthly = defaultdict(float)
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            for deal in deals:
                try:
                    # Try to extract date
                    deal_date = self._extract_date_field(deal, ['created', 'date', 'deal date', 'close date'])
                    value = self._extract_numeric_field(deal, ['amount', 'value', 'deal value', 'price'])
                    
                    if deal_date and value is not None:
                        month_name = month_names[deal_date.month - 1]
                        monthly[month_name] += value
                    elif value is not None:
                        # If no date, add to Unknown
                        monthly['Unknown'] += value
                
                except Exception as e:
                    logger.debug(f"Error processing deal for monthly pipeline: {str(e)}")
                    continue
            
            # Sort by calendar order
            result = {}
            for month in month_names:
                if month in monthly:
                    result[month] = round(monthly[month], 2)
            if 'Unknown' in monthly:
                result['Unknown'] = round(monthly['Unknown'], 2)
            
            logger.info(f"Monthly pipeline: {len(result)} months with data")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing monthly pipeline: {str(e)}")
            return {}
    
    def leadership_summary(self, data: Dict[str, Any]) -> str:
        """Generate executive summary of business metrics.
        
        Args:
            data: Processed data with deals and work orders.
            
        Returns:
            str: Concise business summary for leadership.
        """
        try:
            deals = data.get('deals', [])
            if isinstance(deals, dict):
                deals = deals.get('items', [])
            
            work_orders = data.get('work_orders', [])
            if isinstance(work_orders, dict):
                work_orders = work_orders.get('items', [])
            
            # Generate metrics
            pipeline = self.pipeline_summary(deals)
            sectors = self.revenue_by_sector(deals)
            wo_summary = self.work_order_summary(work_orders)
            delayed_wo = self.delayed_work_orders(work_orders)
            
            # Build summary text
            summary_parts = []
            
            # Pipeline overview
            if pipeline['total_deals'] > 0:
                pipeline_text = f"Pipeline consists of {pipeline['total_deals']} active deals"
                if pipeline['total_pipeline_value'] > 0:
                    pipeline_text += f" worth ₹{pipeline['total_pipeline_value']:.1f}."
                else:
                    pipeline_text += "."
                summary_parts.append(pipeline_text)
            
            # Sector contribution
            if sectors:
                top_sector = sectors[0]
                total_revenue = sum(s['revenue'] for s in sectors)
                if total_revenue > 0:
                    sector_pct = (top_sector['revenue'] / total_revenue * 100)
                    summary_parts.append(
                        f"{top_sector['sector']} sector contributes {sector_pct:.0f}% of revenue."
                    )
            
            # Win rate
            if pipeline['total_deals'] > 0:
                summary_parts.append(f"Win rate is {pipeline['win_rate']:.0f}%.")
            
            # Work order status
            if wo_summary['total_work_orders'] > 0:
                wo_text = f"Work orders: {wo_summary['completed']} completed, "
                wo_text += f"{wo_summary['in_progress']} in progress"
                if wo_summary['overdue'] > 0:
                    wo_text += f", {wo_summary['overdue']} overdue requiring attention."
                else:
                    wo_text += "."
                summary_parts.append(wo_text)
            
            # Overdue work orders
            if delayed_wo:
                summary_parts.append(
                    f"There are {len(delayed_wo)} overdue work orders requiring immediate attention."
                )
            
            result = " ".join(summary_parts)
            logger.info(f"Leadership summary generated: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Error generating leadership summary: {str(e)}")
            return "Unable to generate summary due to data processing error."
    
    @staticmethod
    def _extract_field(item: Dict[str, Any], field_names: Any) -> Optional[str]:
        """Extract a field value from an item by searching column titles.
        
        Args:
            item: Deal or work order item.
            field_names: Single field name or list of field names to search.
            
        Returns:
            str: Field value or None.
        """
        if isinstance(field_names, str):
            field_names = [field_names]
        
        columns = item.get('columns', {})
        for col_id, col_data in columns.items():
            if isinstance(col_data, dict):
                title = col_data.get('title', '').lower()
                for field_name in field_names:
                    if field_name.lower() in title:
                        # Prefer text over value, as value can be a dict
                        return col_data.get('text') or col_data.get('value')
        
        return None
    
    @staticmethod
    def _extract_numeric_field(item: Dict[str, Any], field_names: List[str]) -> Optional[float]:
        """Extract a numeric field value from an item.
        
        Args:
            item: Deal or work order item.
            field_names: List of field names to search.
            
        Returns:
            float: Numeric value or None.
        """
        value = BusinessAnalyzer._extract_field(item, field_names)
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        return None
    
    @staticmethod
    def _extract_date_field(item: Dict[str, Any], field_names: List[str]) -> Optional[datetime]:
        """Extract a date field value from an item.
        
        Args:
            item: Deal or work order item.
            field_names: List of field names to search.
            
        Returns:
            datetime: Date value or None.
        """
        value = BusinessAnalyzer._extract_field(item, field_names)
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except (ValueError, TypeError):
                return None
        return None
