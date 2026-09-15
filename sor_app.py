import streamlit as st
import websocket
import json
import threading
import pandas as pd
import plotly.express as px
import time

st.set_page_config(page_title="Real-Time SOR Engine", layout="wide")
st.title("⚡ Real-Time Smart Order Routing (SOR) Engine")

# -------------------------------------------------------------------
# 📊 THREAD-SAFE STATE STORAGE
# -------------------------------------------------------------------
# Using streamlit's session state to persist exchange data across UI updates
if "order_books" not in st.session_state:
    st.session_state.order_books = {
        "Binance Spot": {"bid": 0.0, "bid_qty": 0.0, "ask": 0.0, "ask_qty": 0.0},
        "Binance Futures": {"bid": 0.0, "bid_qty": 0.0, "ask": 0.0, "ask_qty": 0.0}
    }

# -------------------------------------------------------------------
# 🔄 BACKGROUND WEBSOCKET THREADS
# -------------------------------------------------------------------
def run_websocket(url, exchange_key):
    """Listens to the public websocket stream and updates session state."""
    def on_message(ws, message):
        data = json.loads(message)
        # Parse data from Binance bookTicker stream
        # 'b'=best bid, 'B'=bid qty, 'a'=best ask, 'A'=ask qty
        st.session_state.order_books[exchange_key] = {
            "bid": float(data.get("b", 0)),
            "bid_qty": float(data.get("B", 0)),
            "ask": float(data.get("a", 0)),
            "ask_qty": float(data.get("A", 0))
        }

    def on_error(ws, error):
        pass # Handle or log errors gracefully for production

    # Establish the connection
    ws = websocket.WebSocketApp(
        url, 
        on_message=on_message, 
        on_error=on_error
    )
    ws.run_forever()

# Start background threads for liquidity venues if they aren't already running
if "threads_started" not in st.session_state:
    # 1. Binance Spot Stream (BTCUSDT)
    spot_url = "wss://://binance.com"
    t1 = threading.Thread(target=run_websocket, args=(spot_url, "Binance Spot"), daemon=True)
    t1.start()
    
    # 2. Binance USDⓈ-M Futures Stream (BTCUSDT)
    futures_url = "wss://://binance.com"
    t2 = threading.Thread(target=run_websocket, args=(futures_url, "Binance Futures"), daemon=True)
    t2.start()
    
    st.session_state.threads_started = True

# -------------------------------------------------------------------
# 📐 SMART ORDER ROUTING LOGIC
# -------------------------------------------------------------------
def route_market_buy(target_qty):
    books = st.session_state.order_books
    
    # Consolidate Ask liquidity across venues
    all_asks = [
        {"venue": "Binance Spot", "price": books["Binance Spot"]["ask"], "qty": books["Binance Spot"]["ask_qty"]},
        {"venue": "Binance Futures", "price": books["Binance Futures"]["ask"], "qty": books["Binance Futures"]["ask_qty"]}
    ]
    
    # Sort venues by cheapest available ask price
    sorted_asks = sorted(all_asks, key=lambda x: x["price"])
    
    remaining_qty = target_qty
    allocations = []
    
    for ask in sorted_asks:
        if remaining_qty <= 0 or ask["price"] == 0.0:
            break
        
        fill_qty = min(remaining_qty, ask["qty"])
        if fill_qty > 0:
            allocations.append({
                "Venue": ask["venue"],
                "Executed Price": ask["price"],
                "Allocated Qty": fill_qty,
                "Subtotal Cost": fill_qty * ask["price"]
            })
            remaining_qty -= fill_qty
            
    return pd.DataFrame(allocations), remaining_qty

# -------------------------------------------------------------------
# 🖥️ FRONTEND INTERACTION AND DISPLAY
# -------------------------------------------------------------------
st.sidebar.header("⚡ Live Order Parameters")
order_size = st.sidebar.number_input("Buy Size (BTC)", min_value=0.01, max_value=50.0, value=2.5, step=0.1)

# Display real-time top of book metrics
st.subheader("👀 Consolidated Live Top-of-Book")
col1, col2 = st.columns(2)

with col1:
    spot = st.session_state.order_books["Binance Spot"]
    st.metric("Binance Spot Ask Price", f"${spot['ask']:,}", f"Liquidity: {spot['ask_qty']} BTC")

with col2:
    fut = st.session_state.order_books["Binance Futures"]
    st.metric("Binance Futures Ask Price", f"${fut['ask']:,}", f"Liquidity: {fut['ask_qty']} BTC")

# Execute Routing Optimization
fills_df, unfilled_qty = route_market_buy(order_size)

if not fills_df.empty:
    st.markdown("---")
    st.subheader("🎯 Executed Routing Simulation Summary")
    
    total_spent = fills_df["Subtotal Cost"].sum()
    total_filled = fills_df["Allocated Qty"].sum()
    vwap = total_spent / total_filled
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Dynamic VWAP", f"${vwap:,.2f}")
    m2.metric("Total Filled Qty", f"{total_filled:.4f} BTC")
    m3.metric("Unfilled Residual Qty", f"{unfilled_qty:.4f} BTC")
    
    # Visualizing allocation splits
    fig = px.pie(fills_df, values="Allocated Qty", names="Venue", title="Liquidity Splitting Distribution Across Venues")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(fills_df, use_container_width=True)
else:
    st.warning("Connecting to public websocket streams... Waiting for initial data ticks.")

# Forces Streamlit UI to re-render data details every 2 seconds
time.sleep(2)
st.rerun()
