"""Debug script to inspect work order data structure."""

import json
import logging
from monday_client import MondayClient
from data_processor import DataProcessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize clients
monday_client = MondayClient()
data_processor = DataProcessor()

# Fetch raw work orders
print("Fetching raw work order data...")
raw_data = monday_client.fetch_all()

work_orders_raw = raw_data.get('work_orders', {}).get('items', [])

if work_orders_raw:
    print(f"\nTotal work orders: {len(work_orders_raw)}")
    print("\n=== First 3 work orders structure ===")
    
    for idx, wo in enumerate(work_orders_raw[:3]):
        print(f"\n--- Work Order {idx + 1} ---")
        print(f"ID: {wo.get('id')}")
        print(f"Name: {wo.get('name')}")
        print(f"\nColumns:")
        
        columns = wo.get('columns', {})
        for col_id, col_data in columns.items():
            if isinstance(col_data, dict):
                title = col_data.get('title', 'Unknown')
                text = col_data.get('text')
                value = col_data.get('value')
                print(f"  - {title}: text='{text}', value={value}")
else:
    print("No work orders found")

# Now process and show cleaned structure
print("\n\n=== Processing data ===")
processed = data_processor.process_all(raw_data)
cleaned_work_orders = processed.get('work_orders', {}).get('items', [])

if cleaned_work_orders:
    print(f"Total cleaned work orders: {len(cleaned_work_orders)}")
    print("\n=== First 3 cleaned work orders structure ===")
    
    for idx, wo in enumerate(cleaned_work_orders[:3]):
        print(f"\n--- Cleaned Work Order {idx + 1} ---")
        print(f"ID: {wo.get('id')}")
        print(f"Name: {wo.get('name')}")
        print(f"Columns keys: {list(wo.get('columns', {}).keys())}")
        print(f"Columns data:")
        for key, val in wo.get('columns', {}).items():
            print(f"  - {key}: {val}")
