import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from fpdf import FPDF
import base64

st.set_page_config(
    page_title="Free Stock Portfolio & Risk Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📈 Smart Financial Portfolio & Risk Analyzer")
st.write("Apna stock portfolio manage karein, live prices track karein, aur risk analyze karein.")

# Session state initialization
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

st.sidebar.header("⚙️ Portfolio Management")

# Option 1: Add single stock manually
with st.sidebar.form("stock_form"):
    st.subheader("Add Single Stock")
    ticker = st.text_input("Stock Ticker (e.g., RELIANCE.NS, TCS.NS)", "RELIANCE.NS").upper()
    shares = st.number_input("Number of Shares", min_value=1, value=10)
    buy_price = st.number_input("Purchase Price per Share (₹)", min_value=0.1, value=1000.0)
    
    submitted = st.form_submit_button("Add to Portfolio")
    if submitted:
        st.session_state.portfolio.append({
            'Ticker': ticker,
            'Shares': shares,
            'Buy Price': buy_price
        })
        st.success(f"Added {ticker}!")

# Option 2: Upload CSV for bulk stocks
st.sidebar.subheader("📂 Or Upload CSV File")
uploaded_file = st.sidebar.file_uploader("Upload CSV (Columns: Ticker, Shares, Buy Price)", type=["csv"])
if uploaded_file is not None:
    df_upload = pd.read_csv(uploaded_file)
    for index, row in df_upload.iterrows():
        st.session_state.portfolio.append({
            'Ticker': str(row['Ticker']).upper(),
            'Shares': int(row['Shares']),
            'Buy Price': float(row['Buy Price'])
        })
    st.sidebar.success("Portfolio imported successfully!")

if st.sidebar.button("🗑️ Clear Portfolio"):
    st.session_state.portfolio = []
    st.rerun()

# Function to generate PDF Report
def generate_pdf(df, total_inv, total_val, total_pnl):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Financial Portfolio & Risk Report", ln=True, align='C')
    
    pdf.set_font("Arial", '', 11)
    pdf.cell(200, 10, txt=f"Total Investment: INR {total_inv:,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Current Portfolio Value: INR {total_val:,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Total Profit/Loss: INR {total_pnl:,.2f}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Stock Breakdown:", ln=True)
    pdf.set_font("Arial", '', 10)
    
    for index, row in df.iterrows():
        line = f"{row['Ticker']} | Shares: {row['Shares']} | Inv: {row['Total Investment (₹)']} | Val: {row['Current Value (₹)']} | P&L: {row['P&L (₹)']}"
        pdf.cell(200, 8, txt=line, ln=True)
        
    return pdf.output(dest='S').encode('latin1')

# Main Dashboard Logic
if len(st.session_state.portfolio) > 0:
    st.subheader("📊 Your Live Portfolio Dashboard")
    
    portfolio_data = []
    total_investment = 0
    total_current_value = 0
    
    for item in st.session_state.portfolio:
        try:
            stock = yf.Ticker(item['Ticker'])
            current_price = stock.history(period='1d')['Close'].iloc[0]
            
            investment = item['Shares'] * item['Buy Price']
            curr_val = item['Shares'] * current_price
            pnl = curr_val - investment
            pnl_pct = (pnl / investment) * 100 if investment > 0 else 0
            
            total_investment += investment
            total_current_value += curr_val
            
            portfolio_data.append({
                'Ticker': item['Ticker'],
                'Shares': item['Shares'],
                'Buy Price (₹)': round(item['Buy Price'], 2),
                'Current Price (₹)': round(current_price, 2),
                'Total Investment (₹)': round(investment, 2),
                'Current Value (₹)': round(curr_val, 2),
                'P&L (₹)': round(pnl, 2),
                'P&L (%)': round(pnl_pct, 2)
            })
        except Exception as e:
            st.error(f"Error fetching data for {item['Ticker']}: {e}")
            
    df = pd.DataFrame(portfolio_data)
    
    # Top Metrics Display
    total_pnl = total_current_value - total_investment
    total_pnl_pct = (total_pnl / total_investment) * 100 if total_investment > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Investment", f"₹ {total_investment:,.2f}")
    col2.metric("Current Portfolio Value", f"₹ {total_current_value:,.2f}")
    col3.metric("Total Profit / Loss", f"₹ {total_pnl:,.2f}", f"{total_pnl_pct:.2f}%")
    
    # Display Dataframe Table
    st.dataframe(df, use_container_width=True)
    
    # PDF Download Button
    st.subheader("📥 Download Report")
    pdf_bytes = generate_pdf(df, total_investment, total_current_value, total_pnl)
    st.download_button(
        label="Download Portfolio PDF Report",
        data=pdf_bytes,
        file_name="Portfolio_Risk_Report.pdf",
        mime="application/pdf"
    )
    
    # Visualizations & Risk Section
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("📈 Asset Allocation")
        fig = px.pie(df, names='Ticker', values='Current Value (₹)', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_chart2:
        st.subheader("⚠️ Risk & Health Check")
        if len(df) < 3:
            st.warning("Low Diversification! Consider adding stocks from different sectors to lower risk.")
        else:
            st.success("Good Portfolio Diversification! Your risk is balanced across multiple assets.")
            
        st.info("💡 **Finance Tip:** Regularly rebalance your portfolio semi-annually to lock in profits.")

else:
    st.info("👈 Sidebar ka use karke stocks add karein ya CSV file upload karein.") 