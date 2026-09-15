import streamlit as st
import plotly.express as px
from sor_engine import SmartOrderRouter

st.set_page_config(page_title="Institutional Smart Order Router", layout="wide")
st.title("⚡ Smart Order Routing (SOR) Engine")

# Sidebar inputs
st.sidebar.header("Order Execution Parameters")
side = st.sidebar.selectbox("Order Side", ["BUY", "SELL"])
order_qty = st.sidebar.number_input("Order Quantity", min_value=10, max_value=1000, value=100, step=10)

router = SmartOrderRouter()

if st.sidebar.button("Execute Order"):
    if side == "BUY":
        fills_df, unfilled = router.route_buy_order(order_qty)
        
        # Display Metrics
        avg_price = (fills_df["Total Cost"].sum() / fills_df["Quantity"].sum())
        
        col1, col2, col3 = st.columns(3)
        col1.metric("VWAP (Avg Price)", f"${avg_price:.2f}")
        col2.metric("Total Executed", f"{fills_df['Quantity'].sum()} units")
        col3.metric("Unfilled Liquidity", f"{unfilled} units")
        
        # Visual breakdown of splits
        st.subheader("Liquidity Splits Across Venues")
        fig = px.bar(fills_df, x="Venue", y="Quantity", color="Price", title="Order Fill Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Raw Data Frame
        st.subheader("Execution Execution Logs")
        st.dataframe(fills_df)
