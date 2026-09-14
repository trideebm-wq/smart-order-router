import numpy as np
import pandas as pd

class SmartOrderRouter:
    def __init__(self):
        # Simulate static order books for Exchanges A, B, and C
        # Format: [Price, Available Volume]
        self.exchange_books = {
            "Exchange A": {"bid": [[99.5, 100], [99.0, 200]], "ask": [[100.5, 50], [101.0, 150]]},
            "Exchange B": {"bid": [[99.6,  30], [99.2, 300]], "ask": [[100.4, 40], [100.9, 250]]},
            "Exchange C": {"bid": [[99.4, 150], [99.1, 100]], "ask": [[100.6, 80], [101.2, 400]]}
        }

    def route_buy_order(self, total_qty):
        remaining_qty = total_qty
        fills = []
        
        # Flatten and sort all available asks across venues by lowest price
        all_asks = []
        for venue, book in self.exchange_books.items():
            for level in book["ask"]:
                all_asks.append({"venue": venue, "price": level[0], "qty": level[1]})
        
        # Sort by price (ascending for buy orders)
        all_asks = sorted(all_asks, key=lambda x: x["price"])
        
        # Sweep books
        for ask in all_asks:
            if remaining_qty <= 0:
                break
                
            allocated_qty = min(remaining_qty, ask["qty"])
            fills.append({
                "Venue": ask["venue"],
                "Price": ask["price"],
                "Quantity": allocated_qty,
                "Total Cost": allocated_qty * ask["price"]
            })
            remaining_qty -= allocated_qty
            
        df_fills = pd.DataFrame(fills)
        
        if remaining_qty > 0:
            # Handle unfilled size (e.g., partial fill or post to book)
            pass
            
        return df_fills, remaining_qty