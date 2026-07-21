"""Data processing and normalization module for Monday.com data.

This module provides the DataProcessor class that handles data cleaning,
normalization, and quality reporting for board data from Monday.com API.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and normalize data from Monday.com boards.
    
    This class handles cleaning inconsistent data, normalizing values,
    and generating quality reports for data validation.
    """
    
    # Status normalization mappings
    STATUS_MAPPINGS = {
        'won': 'Won',
        'closed won': 'Won',
        'closed-won': 'Won',
        'lost': 'Lost',
        'closed lost': 'Lost',
        'closed-lost': 'Lost',
        'pending': 'Pending',
        'open': 'Open',
        'active': 'Open',
    }
    
    # Sector normalization mappings
    SECTOR_MAPPINGS = {
        'energy': 'Energy',
        'energy sector': 'Energy',
        'manufacturing': 'Manufacturing',
        'technology': 'Technology',
        'tech': 'Technology',
        'finance': 'Finance',
        'financial services': 'Finance',
        'healthcare': 'Healthcare',
        'health': 'Healthcare',
        'retail': 'Retail',
        'retail & consumer': 'Retail',
        'telecommunications': 'Telecommunications',
        'telecom': 'Telecommunications',
        'infrastructure': 'Infrastructure',
        'utilities': 'Utilities',
        'agriculture': 'Agriculture',
        'agritech': 'Agriculture',
        'logistics': 'Logistics',
        'transportation': 'Logistics',
        'real estate': 'Real Estate',
        'realestate': 'Real Estate',
        'education': 'Education',
        'edtech': 'Education',
    }
    
    def __init__(self):
        """Initialize DataProcessor."""
        logger.info("DataProcessor initialized")
    
    @staticmethod
    def clean_text(value: Any) -> Optional[str]:
        """Clean text values by handling None, NaN, and extra spaces.
        
        Args:
            value: Input value to clean.
            
        Returns:
            str: Cleaned string or None if empty.
        """
        # Handle None
        if value is None:
            return None
        
        # Handle NaN (pandas)
        if isinstance(value, float):
            if pd.isna(value):
                return None
        
        # Convert to string and strip whitespace
        text = str(value).strip()
        
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Return None for empty strings
        if not text or text.lower() == 'nan':
            return None
        
        return text
    
    def normalize_sector(self, value: Optional[str]) -> Optional[str]:
        """Normalize sector values to standard format.
        
        Args:
            value: Raw sector value.
            
        Returns:
            str: Normalized sector or 'Unknown'.
        """
        if not value:
            return 'Unknown'
        
        # Clean and normalize
        cleaned = self.clean_text(value)
        if not cleaned:
            return 'Unknown'
        
        # Check mapping
        normalized = self.SECTOR_MAPPINGS.get(cleaned.lower())
        if normalized:
            return normalized
        
        # If exact match exists, return as is
        return cleaned if cleaned else 'Unknown'
    
    def normalize_status(self, value: Optional[str]) -> Optional[str]:
        """Normalize status values to standard format.
        
        Args:
            value: Raw status value.
            
        Returns:
            str: Normalized status or None.
        """
        if not value:
            return None
        
        # Clean text
        cleaned = self.clean_text(value)
        if not cleaned:
            return None
        
        # Check mapping
        normalized = self.STATUS_MAPPINGS.get(cleaned.lower())
        if normalized:
            return normalized
        
        # Return cleaned version if not in mapping
        return cleaned if cleaned else None
    
    @staticmethod
    def normalize_dates(value: Any) -> Optional[datetime]:
        """Normalize date values to datetime object.
        
        Accepts multiple date formats:
        - YYYY-MM-DD
        - DD/MM/YYYY
        - MM/DD/YYYY
        - Month DD YYYY
        
        Args:
            value: Raw date value.
            
        Returns:
            datetime: Python datetime object or None if invalid.
        """
        if not value:
            return None
        
        # Convert to string
        date_str = str(value).strip()
        
        # List of date formats to try
        date_formats = [
            '%Y-%m-%d',      # YYYY-MM-DD
            '%d/%m/%Y',      # DD/MM/YYYY
            '%m/%d/%Y',      # MM/DD/YYYY
            '%B %d %Y',      # Month DD YYYY
            '%b %d %Y',      # Mon DD YYYY
            '%d-%m-%Y',      # DD-MM-YYYY
            '%m-%d-%Y',      # MM-DD-YYYY
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If no format matched, return None
        logger.debug(f"Could not parse date: {date_str}")
        return None
    
    @staticmethod
    def normalize_currency(value: Any) -> Optional[float]:
        """Normalize currency values to float.
        
        Handles:
        - Currency symbols (₹, $, €, £, etc.)
        - Thousands separators (,)
        - Decimal points (.)
        
        Args:
            value: Raw currency value.
            
        Returns:
            float: Numeric value or None if invalid.
        """
        if value is None:
            return None
        
        # Handle already numeric values
        if isinstance(value, (int, float)):
            if pd.notna(value):
                return float(value)
            return None
        
        # Convert to string
        curr_str = str(value).strip()
        if not curr_str:
            return None
        
        try:
            # Remove common currency symbols
            curr_str = re.sub(r'[₹$€£¥₽₩₪₨]', '', curr_str)
            
            # Remove whitespace
            curr_str = curr_str.replace(' ', '')
            
            # Remove thousands separator (comma before digits or last 3 digits)
            # But keep decimal point
            curr_str = curr_str.replace(',', '')
            
            # Convert to float
            return float(curr_str)
            
        except (ValueError, AttributeError):
            logger.debug(f"Could not parse currency: {value}")
            return None
    
    def clean_board(self, board_items: List[Dict[str, Any]]) -> tuple:
        """Clean and normalize all items in a board.
        
        Args:
            board_items: List of items from a Monday.com board.
            
        Returns:
            tuple: (cleaned_items, quality_report)
        """
        if not board_items:
            logger.warning("No items to clean")
            return [], self._empty_quality_report()
        
        cleaned_items = []
        quality_report = {
            'missing_values': {},
            'invalid_dates': [],
            'empty_rows': [],
            'normalized_fields': {}
        }
        
        for idx, item in enumerate(board_items):
            try:
                cleaned_item = {
                    'id': item.get('id'),
                    'name': self.clean_text(item.get('name')),
                    'columns': {}
                }
                
                # Process columns
                columns = item.get('columns', {})
                for col_id, col_data in columns.items():
                    if isinstance(col_data, dict):
                        # Try to normalize based on column title
                        title = col_data.get('title', '').lower()
                        raw_value = col_data.get('text') or col_data.get('value')
                        
                        normalized_value = raw_value
                        
                        # Normalize by column type
                        if 'sector' in title or 'industry' in title:
                            normalized_value = self.normalize_sector(raw_value)
                            if title not in quality_report['normalized_fields']:
                                quality_report['normalized_fields'][title] = 0
                            quality_report['normalized_fields'][title] += 1
                        
                        elif 'status' in title or 'state' in title:
                            normalized_value = self.normalize_status(raw_value)
                            if title not in quality_report['normalized_fields']:
                                quality_report['normalized_fields'][title] = 0
                            quality_report['normalized_fields'][title] += 1
                        
                        elif 'date' in title or 'time' in title:
                            normalized_value = self.normalize_dates(raw_value)
                            if normalized_value is None and raw_value:
                                quality_report['invalid_dates'].append({
                                    'item_id': item.get('id'),
                                    'field': title,
                                    'value': raw_value
                                })
                            if title not in quality_report['normalized_fields']:
                                quality_report['normalized_fields'][title] = 0
                            quality_report['normalized_fields'][title] += 1
                        
                        elif 'amount' in title or 'value' in title or 'price' in title or 'cost' in title:
                            normalized_value = self.normalize_currency(raw_value)
                            if title not in quality_report['normalized_fields']:
                                quality_report['normalized_fields'][title] = 0
                            quality_report['normalized_fields'][title] += 1
                        
                        else:
                            # Clean text for other fields
                            normalized_value = self.clean_text(raw_value)
                        
                        # Track missing values
                        if normalized_value is None:
                            if col_id not in quality_report['missing_values']:
                                quality_report['missing_values'][col_id] = 0
                            quality_report['missing_values'][col_id] += 1
                        
                        cleaned_item['columns'][col_id] = {
                            'title': col_data.get('title'),
                            'value': normalized_value,
                            'original': raw_value
                        }
                
                # Check if row is empty (only has id and name)
                if not cleaned_item['columns']:
                    quality_report['empty_rows'].append(item.get('id'))
                
                cleaned_items.append(cleaned_item)
                
            except Exception as e:
                logger.error(f"Error processing item {idx}: {str(e)}")
                continue
        
        logger.info(f"Cleaned {len(cleaned_items)} items from board")
        return cleaned_items, quality_report
    
    def process_all(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process all data from boards.
        
        Args:
            data: Raw data with 'deals' and 'work_orders' keys.
            
        Returns:
            dict: Processed data with quality reports.
        """
        logger.info("Processing all board data...")
        
        result = {
            'deals': None,
            'work_orders': None,
            'quality_report': {}
        }
        
        try:
            # Process deals
            if 'deals' in data and data['deals']:
                deals_data = data['deals']
                
                # Extract items if wrapped in response object
                if isinstance(deals_data, dict) and 'items' in deals_data:
                    deals_items = deals_data.get('items', [])
                else:
                    deals_items = deals_data if isinstance(deals_data, list) else []
                
                deals_cleaned, deals_report = self.clean_board(deals_items)
                result['deals'] = {
                    'items': deals_cleaned,
                    'item_count': len(deals_cleaned),
                    'quality_report': deals_report
                }
                result['quality_report']['deals'] = deals_report
                logger.info(f"Processed {len(deals_cleaned)} deals")
            
            # Process work orders
            if 'work_orders' in data and data['work_orders']:
                work_orders_data = data['work_orders']
                
                # Extract items if wrapped in response object
                if isinstance(work_orders_data, dict) and 'items' in work_orders_data:
                    work_orders_items = work_orders_data.get('items', [])
                else:
                    work_orders_items = work_orders_data if isinstance(work_orders_data, list) else []
                
                work_orders_cleaned, work_orders_report = self.clean_board(work_orders_items)
                result['work_orders'] = {
                    'items': work_orders_cleaned,
                    'item_count': len(work_orders_cleaned),
                    'quality_report': work_orders_report
                }
                result['quality_report']['work_orders'] = work_orders_report
                logger.info(f"Processed {len(work_orders_cleaned)} work orders")
            
            logger.info("Data processing complete")
            return result
            
        except Exception as e:
            logger.error(f"Error processing all data: {str(e)}")
            return {
                'deals': None,
                'work_orders': None,
                'error': str(e),
                'quality_report': {}
            }
    
    @staticmethod
    def _empty_quality_report() -> Dict[str, Any]:
        """Generate empty quality report structure.
        
        Returns:
            dict: Empty quality report.
        """
        return {
            'missing_values': {},
            'invalid_dates': [],
            'empty_rows': [],
            'normalized_fields': {}
        }
