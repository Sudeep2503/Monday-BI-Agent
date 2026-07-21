"""AI Agent for natural language business question answering.

This module provides the BusinessAIAgent class that interprets natural language
questions, identifies user intent, and leverages the BusinessAnalyzer to
provide comprehensive business intelligence answers.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from business_analyzer import BusinessAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BusinessAIAgent:
    """AI Agent for answering natural language business questions.
    
    This agent identifies user intent from questions and uses BusinessAnalyzer
    to provide data-driven business intelligence responses.
    """
    
    # Intent keywords mapping
    INTENT_KEYWORDS = {
        'pipeline_summary': [
            'pipeline', 'deals', 'how many deals', 'deal count', 'deal status',
            'pipeline value', 'average deal', 'deal performance', 'win rate',
            'won deals', 'lost deals', 'open deals', 'active deals', 'how is',
            'sales overview', 'sales', 'pipeline health', 'how are sales'
        ],
        'revenue_by_sector': [
            'sector', 'industry', 'revenue by sector', 'revenue by industry',
            'sector revenue', 'which sector', 'revenue breakdown', 'sector contribution',
            'top sector', 'biggest sector', 'sector analysis', 'highest revenue',
            'revenue overview', 'highest revenue sector'
        ],
        'top_clients': [
            'client', 'customer', 'account', 'top client', 'biggest client',
            'largest client', 'best client', 'client value', 'client revenue',
            'key account', 'major client', 'who are our clients', 'who are clients',
            'biggest customers', 'largest customers', 'biggest accounts'
        ],
        'deal_stage_distribution': [
            'stage', 'status distribution', 'deal breakdown', 'stage breakdown',
            'how many stages', 'stage count', 'deal by stage', 'stage distribution'
        ],
        'delayed_work_orders': [
            'overdue', 'delayed work', 'late work', 'missed deadline', 'past due',
            'work order overdue', 'delayed order', 'delayed tasks', 'overdue wo',
            'delayed projects', 'late projects', 'overdue projects'
        ],
        'work_order_summary': [
            'work order status', 'work orders', 'wo summary', 'task status',
            'completion status', 'in progress', 'work completed', 'task summary',
            'pending tasks', 'work summary', 'work order summary'
        ],
        'monthly_pipeline': [
            'monthly', 'month', 'pipeline by month', 'monthly breakdown',
            'monthly revenue', 'by month', 'monthly analysis', 'trend', 'month analysis',
            'monthly trend', 'sales trend', 'forecast'
        ],
        'leadership_summary': [
            'summary', 'executive', 'overview', 'brief', 'snapshot', 'dashboard',
            'business summary', 'key metrics', 'at a glance', 'overall',
            'executive summary', 'ceo report', 'founder update', 'business snapshot'
        ]
    }
    
    def __init__(self, business_analyzer: Optional[BusinessAnalyzer] = None):
        """Initialize BusinessAIAgent with BusinessAnalyzer.
        
        Args:
            business_analyzer: Instance of BusinessAnalyzer or None to create one.
        """
        self.analyzer = business_analyzer or BusinessAnalyzer()
        logger.info("BusinessAIAgent initialized")
    
    def identify_intent(self, question: str) -> str:
        """Identify user intent from natural language question.
        
        Uses keyword matching to determine which business metric the user
        is asking about.
        
        Args:
            question: Natural language question from user.
            
        Returns:
            str: Intent identifier (e.g., 'pipeline_summary', 'revenue_by_sector').
                 Returns 'general' if intent cannot be determined.
        """
        if not question:
            logger.debug("Empty question provided")
            return 'general'
        
        question_lower = question.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in question_lower:
                    score += 1
            if score > 0:
                intent_scores[intent] = score
        
        # Return the highest scoring intent, or 'general' if no matches
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            logger.debug(f"Identified intent: {best_intent} (score: {intent_scores[best_intent]})")
            return best_intent
        
        logger.debug("Could not identify specific intent, defaulting to 'general'")
        return 'general'
    
    def answer(self, question: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Answer a business question using processed data.
        
        Args:
            question: Natural language question from user.
            data: Processed data containing deals and work orders.
            
        Returns:
            dict: Response with intent and formatted answer.
        """
        try:
            if not question:
                return {
                    'intent': 'general',
                    'response': "Please ask a business question. I can help with pipeline, revenue, clients, work orders, and more."
                }

            intent = self.identify_intent(question)

            if intent == 'general':
                return {
                    'intent': intent,
                    'response': self.unsupported_question(question)
                }

            deals = self._extract_deals(data)
            work_orders = self._extract_work_orders(data)

            if intent in {'pipeline_summary', 'revenue_by_sector', 'top_clients', 'deal_stage_distribution', 'monthly_pipeline', 'leadership_summary'} and not deals:
                return {
                    'intent': intent,
                    'response': "No deal data is currently available. Please refresh the Monday.com data to continue."
                }

            if intent in {'delayed_work_orders', 'work_order_summary'} and not work_orders:
                return {
                    'intent': intent,
                    'response': "No work order data is currently available. Please refresh the Monday.com data to continue."
                }

            try:
                if intent == 'pipeline_summary':
                    result = self.analyzer.pipeline_summary(deals)
                elif intent == 'revenue_by_sector':
                    result = self.analyzer.revenue_by_sector(deals)
                elif intent == 'top_clients':
                    result = self.analyzer.top_clients(deals, limit=5)
                elif intent == 'deal_stage_distribution':
                    result = self.analyzer.deal_stage_distribution(deals)
                elif intent == 'delayed_work_orders':
                    result = self.analyzer.delayed_work_orders(work_orders)
                elif intent == 'work_order_summary':
                    result = self.analyzer.work_order_summary(work_orders)
                elif intent == 'monthly_pipeline':
                    result = self.analyzer.monthly_pipeline(deals)
                elif intent == 'leadership_summary':
                    result = self.analyzer.leadership_summary(data)
                else:
                    result = None

                formatted_response = self.format_response(result, intent)

                return {
                    'intent': intent,
                    'response': formatted_response
                }

            except Exception as e:
                logger.error(f"Error processing intent '{intent}': {str(e)}")
                return {
                    'intent': intent,
                    'response': f"I encountered an issue analyzing {intent}. Please try again."
                }

        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                'intent': 'error',
                'response': "I encountered an unexpected error. Please try again."
            }
    
    def format_response(self, result: Any, intent: str) -> str:
        """Format analysis result into human-readable response.
        
        Args:
            result: Result from BusinessAnalyzer method.
            intent: The intent identifier.
            
        Returns:
            str: Formatted human-readable response.
        """
        try:
            if result is None:
                return "No data available for this analysis."
            
            # Handle empty results
            if isinstance(result, dict) and not result:
                return "No data available for this analysis."
            
            if isinstance(result, list) and not result:
                return "No results found for this query."
            
            # Format based on intent
            if intent == 'pipeline_summary':
                return self._format_pipeline_summary(result)
            
            elif intent == 'revenue_by_sector':
                return self._format_revenue_by_sector(result)
            
            elif intent == 'top_clients':
                return self._format_top_clients(result)
            
            elif intent == 'deal_stage_distribution':
                return self._format_deal_stage_distribution(result)
            
            elif intent == 'delayed_work_orders':
                return self._format_delayed_work_orders(result)
            
            elif intent == 'work_order_summary':
                return self._format_work_order_summary(result)
            
            elif intent == 'monthly_pipeline':
                return self._format_monthly_pipeline(result)
            
            elif intent == 'leadership_summary':
                # Already formatted as text
                if isinstance(result, str):
                    return result
                return str(result)
            
            else:
                return str(result)
        
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            return "I processed your request but encountered an error formatting the response."
    
    def unsupported_question(self, question: str) -> str:
        """Generate response for unsupported questions.
        
        Args:
            question: The unsupported question.
            
        Returns:
            str: Friendly message about supported capabilities.
        """
        return (
            "I can currently help with:\n"
            "• Pipeline Summary\n"
            "• Revenue Analysis\n"
            "• Top Clients\n"
            "• Work Orders\n"
            "• Monthly Trends\n"
            "• Leadership Summary\n\n"
            "Try asking something like: 'How is our pipeline?' or 'Which sector has the highest revenue?'"
        )
    
    @staticmethod
    def _extract_deals(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract deals from processed data.
        
        Args:
            data: Processed data dictionary.
            
        Returns:
            list: List of deal items.
        """
        if not data:
            return []
        
        deals = data.get('deals', [])
        
        # Handle wrapped response
        if isinstance(deals, dict):
            deals = deals.get('items', [])
        
        return deals if isinstance(deals, list) else []
    
    @staticmethod
    def _extract_work_orders(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract work orders from processed data.
        
        Args:
            data: Processed data dictionary.
            
        Returns:
            list: List of work order items.
        """
        if not data:
            return []
        
        work_orders = data.get('work_orders', [])
        
        # Handle wrapped response
        if isinstance(work_orders, dict):
            work_orders = work_orders.get('items', [])
        
        return work_orders if isinstance(work_orders, list) else []
    
    @staticmethod
    def _format_currency(value: float) -> str:
        """Format currency values in a concise, executive-friendly style."""
        if value is None:
            return '₹0'
        if value >= 1_000_000_000:
            return f"₹{value / 1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"₹{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"₹{value / 1_000:.0f}K"
        return f"₹{value:,.0f}"

    @staticmethod
    def _format_pipeline_summary(summary: Dict[str, Any]) -> str:
        """Format pipeline summary for display."""
        lines = ["📊 Pipeline Summary", "• Total Deals: " + str(summary.get('total_deals', 0)),
                 "• Won Deals: " + str(summary.get('won_deals', 0)),
                 "• Lost Deals: " + str(summary.get('lost_deals', 0)),
                 "• Open Deals: " + str(summary.get('open_deals', 0)),
                 "• Win Rate: " + f"{summary.get('win_rate', 0):.1f}%",
                 "• Pipeline Value: " + BusinessAIAgent._format_currency(summary.get('total_pipeline_value', 0)),
                 "• Average Deal Size: " + BusinessAIAgent._format_currency(summary.get('average_deal_size', 0))]
        return "\n".join(lines)

    @staticmethod
    def _format_revenue_by_sector(sectors: List[Dict[str, Any]]) -> str:
        """Format revenue by sector for display."""
        if not sectors:
            return "No sector data is available right now."

        total_revenue = sum(float(sector.get('revenue', 0) or 0) for sector in sectors)
        lines = ["📈 Revenue by Sector"]

        for idx, sector in enumerate(sectors[:5], 1):
            revenue = float(sector.get('revenue', 0) or 0)
            pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            lines.append(f"{idx}. {sector.get('sector', 'Unknown')} — {BusinessAIAgent._format_currency(revenue)} ({pct:.1f}%)")

        if len(sectors) > 5:
            lines.append(f"...and {len(sectors) - 5} more sectors")

        return "\n".join(lines)

    @staticmethod
    def _format_top_clients(clients: List[Dict[str, Any]]) -> str:
        """Format top clients for display."""
        if not clients:
            return "No client data is available right now."

        lines = ["🏆 Top Clients"]
        for idx, client in enumerate(clients[:5], 1):
            lines.append(f"{idx}. {client.get('client', 'Unknown')} — {BusinessAIAgent._format_currency(client.get('total_value', 0))}")
        return "\n".join(lines)

    @staticmethod
    def _format_deal_stage_distribution(distribution: Dict[str, int]) -> str:
        """Format deal stage distribution for display."""
        if not distribution:
            return "No stage distribution data is available right now."

        lines = ["📊 Deal Stage Distribution"]
        total = sum(distribution.values())
        for stage, count in distribution.items():
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"• {stage}: {count} ({pct:.1f}%)")
        return "\n".join(lines)

    @staticmethod
    def _format_delayed_work_orders(delayed: List[Dict[str, Any]]) -> str:
        """Format delayed work orders for display."""
        if not delayed:
            return "✅ No overdue work orders. Everything appears to be on track."

        lines = ["⚠️ Delayed Work Orders"]
        for wo in delayed:
            lines.append(f"• {wo.get('name', 'Unnamed work order')} — {wo.get('status', 'Unknown')} | Due: {wo.get('due_date', 'N/A')} | Overdue: {wo.get('days_overdue', 0)} days")
        return "\n".join(lines)

    @staticmethod
    def _format_work_order_summary(summary: Dict[str, int]) -> str:
        """Format work order summary for display."""
        lines = ["📋 Work Order Summary"]
        total = summary.get('total_work_orders', 0)
        completed = summary.get('completed', 0)
        in_progress = summary.get('in_progress', 0)
        pending = summary.get('pending', 0)
        overdue = summary.get('overdue', 0)
        completed_pct = (completed / total * 100) if total > 0 else 0

        lines.append(f"• Total Work Orders: {total}")
        lines.append(f"• Completed: {completed} ({completed_pct:.0f}%)")
        lines.append(f"• In Progress: {in_progress}")
        lines.append(f"• Pending: {pending}")
        lines.append(f"• Overdue: {overdue}")
        return "\n".join(lines)

    @staticmethod
    def _format_monthly_pipeline(monthly: Dict[str, float]) -> str:
        """Format monthly pipeline for display."""
        if not monthly:
            return "No monthly pipeline data is available right now."

        lines = ["📅 Monthly Pipeline Trend"]
        max_value = max(monthly.values()) if monthly else 0
        for month, value in monthly.items():
            bar_length = int((value / max_value * 20)) if max_value > 0 else 0
            bar = "█" * bar_length
            lines.append(f"• {month}: {bar} {BusinessAIAgent._format_currency(value)}")
        return "\n".join(lines)

    @staticmethod
    def _format_error(error: str) -> str:
        """Format error message for display."""
        return f"❌ Error: {error}"
