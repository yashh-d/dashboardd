import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import pytz
import threading
import sqlite3
import os
import json

# Set page configuration
st.set_page_config(
    page_title="Blockchain Metrics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for a more beautiful dashboard
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    h1, h2, h3, h4 {
        color: #000000;
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 10px;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 15px;
        text-align: center;
    }
    .last-updated {
        color: #000000;
        font-size: 0.8em;
        text-align: right;
        padding-top: 5px;
    }
    /* Make all Streamlit text elements black */
    p, span, label, .stMarkdown, .stText, .stSelectbox label, .stDateInput label {
        color: #000000 !important;
    }
    /* Ensure all plot labels and ticks are black */
    .js-plotly-plot .plotly .xtick text, .js-plotly-plot .plotly .ytick text {
        fill: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Dictionary mapping blockchain names to their identifiers in DeFiLlama and CoinGecko
BLOCKCHAIN_MAPPING = {
    "Aptos": {"defillama": "aptos", "coingecko": "aptos"},
    "Avalanche": {"defillama": "Avalanche", "coingecko": "avalanche-2"},
    "Core DAO": {"defillama": "core", "coingecko": "coredaoorg"},
    "Flow": {"defillama": "flow", "coingecko": "flow"},
    "Injective": {"defillama": "injective", "coingecko": "injective-protocol"},
    "Optimism": {"defillama": "optimism", "coingecko": "optimism"},
    "Polygon": {"defillama": "polygon", "coingecko": "matic-network"},
    "XRP/XRPL": {"defillama": "XRPL", "coingecko": "ripple"},
    "Sei": {"defillama": "sei", "coingecko": "sei-network"}
}

# Database setup
DB_PATH = "blockchain_data.db"

def setup_database():
    """Create database and tables if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables for TVL data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tvl_data (
        blockchain TEXT,
        date TEXT,
        timestamp INTEGER,
        tvl REAL,
        PRIMARY KEY (blockchain, timestamp)
    )
    ''')
    
    # Create tables for price data
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_data (
        blockchain TEXT,
        date TEXT,
        timestamp INTEGER,
        price REAL,
        PRIMARY KEY (blockchain, timestamp)
    )
    ''')
    
    # Create table for last update timestamp
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS last_updated (
        id INTEGER PRIMARY KEY,
        timestamp TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
setup_database()

# Cache for data
data_cache = {
    "tvl_data": {},
    "price_data": {},
    "last_updated": None
}

# Database functions
def save_tvl_data_to_db(blockchain, df):
    """Save TVL data to SQLite database"""
    if df.empty:
        return
    
    conn = sqlite3.connect(DB_PATH)
    
    # Convert the dataframe to a format suitable for the database
    db_data = []
    for _, row in df.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        timestamp = int(row['date'].timestamp())
        db_data.append((blockchain, date_str, timestamp, float(row['tvl'])))
    
    # Insert data into the database
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR REPLACE INTO tvl_data (blockchain, date, timestamp, tvl) VALUES (?, ?, ?, ?)",
        db_data
    )
    
    conn.commit()
    conn.close()

def save_price_data_to_db(blockchain, df):
    """Save price data to SQLite database"""
    if df.empty:
        return
    
    conn = sqlite3.connect(DB_PATH)
    
    # Convert the dataframe to a format suitable for the database
    db_data = []
    for _, row in df.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        timestamp = int(row['timestamp'] / 1000)  # Convert from ms to seconds
        db_data.append((blockchain, date_str, timestamp, float(row['price'])))
    
    # Insert data into the database
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR REPLACE INTO price_data (blockchain, date, timestamp, price) VALUES (?, ?, ?, ?)",
        db_data
    )
    
    conn.commit()
    conn.close()

def update_last_updated_time(timestamp):
    """Update the last updated timestamp in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM last_updated")
    cursor.execute(
        "INSERT INTO last_updated (id, timestamp) VALUES (1, ?)",
        (timestamp.isoformat(),)
    )
    
    conn.commit()
    conn.close()

def get_last_updated_time():
    """Get the last updated timestamp from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT timestamp FROM last_updated WHERE id = 1")
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return datetime.fromisoformat(result[0])
    return None

def get_tvl_data_from_db(blockchain):
    """Retrieve TVL data from the database"""
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT date, timestamp, tvl FROM tvl_data WHERE blockchain = ? ORDER BY timestamp"
    df = pd.read_sql_query(query, conn, params=(blockchain,))
    
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    
    return df

def get_price_data_from_db(blockchain):
    """Retrieve price data from the database"""
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT date, timestamp, price FROM price_data WHERE blockchain = ? ORDER BY timestamp"
    df = pd.read_sql_query(query, conn, params=(blockchain,))
    
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['timestamp'] = df['timestamp'] * 1000  # Convert back to ms for consistency
    
    return df

# Get the most recent timestamp in the database for a given blockchain
def get_latest_tvl_timestamp(blockchain):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT MAX(timestamp) FROM tvl_data WHERE blockchain = ?", 
        (blockchain,)
    )
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0] if result and result[0] else 0

def get_latest_price_timestamp(blockchain):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT MAX(timestamp) FROM price_data WHERE blockchain = ?", 
        (blockchain,)
    )
    result = cursor.fetchone()
    
    conn.close()
    
    return result[0] if result and result[0] else 0

# Fetch TVL data from DeFiLlama
def fetch_tvl_data(blockchain_id, blockchain_name):
    try:
        # Get the latest timestamp from the database
        latest_timestamp = get_latest_tvl_timestamp(blockchain_name)
        
        # Check if we have recent data (within the last day)
        if latest_timestamp and (time.time() - latest_timestamp) < 86400:
            # Get data from database
            df = get_tvl_data_from_db(blockchain_name)
            if not df.empty:
                return df
        
        # If no recent data, fetch from API
        url = f"https://api.llama.fi/v2/historicalChainTvl/{blockchain_id}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'], unit='s')
            
            # Save to database
            save_tvl_data_to_db(blockchain_name, df)
            
            return df
        else:
            st.error(f"Error fetching TVL data for {blockchain_id}: {response.status_code}")
            
            # Try to get whatever we have from the database
            return get_tvl_data_from_db(blockchain_name)
    except Exception as e:
        st.error(f"Exception when fetching TVL data for {blockchain_id}: {e}")
        
        # Try to get data from database on error
        return get_tvl_data_from_db(blockchain_name)

# Fetch price data from CoinGecko
def fetch_price_data(coin_id, blockchain_name):
    try:
        # Get the latest timestamp from the database
        latest_timestamp = get_latest_price_timestamp(blockchain_name)
        
        # Check if we have recent data (within the last day)
        if latest_timestamp and (time.time() - latest_timestamp) < 86400:
            # Get data from database
            df = get_price_data_from_db(blockchain_name)
            if not df.empty:
                return df
        
        # If no recent data, fetch from API
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": "90",
            "interval": "daily"
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            prices = data.get("prices", [])
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Save to database
            save_price_data_to_db(blockchain_name, df)
            
            return df
        else:
            st.error(f"Error fetching price data for {coin_id}: {response.status_code}")
            
            # Try to get whatever we have from the database
            return get_price_data_from_db(blockchain_name)
    except Exception as e:
        st.error(f"Exception when fetching price data for {coin_id}: {e}")
        
        # Try to get data from database on error
        return get_price_data_from_db(blockchain_name)

# Update data cache
def update_data():
    global data_cache
    
    new_tvl_data = {}
    new_price_data = {}
    current_time = datetime.now(pytz.UTC)
    
    for blockchain, ids in BLOCKCHAIN_MAPPING.items():
        new_tvl_data[blockchain] = fetch_tvl_data(ids["defillama"], blockchain)
        new_price_data[blockchain] = fetch_price_data(ids["coingecko"], blockchain)
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    data_cache = {
        "tvl_data": new_tvl_data,
        "price_data": new_price_data,
        "last_updated": current_time
    }
    
    # Update the last updated time in the database
    update_last_updated_time(current_time)

# Background update task
def background_update():
    while True:
        update_data()
        time.sleep(3600)  # Update every hour

# Start the background update thread when the app starts
if "thread_started" not in st.session_state:
    # Check if we already have data in the database
    last_updated = get_last_updated_time()
    
    # If we have data that was updated in the last hour, load it from the database
    if last_updated and (datetime.now(pytz.UTC) - last_updated).total_seconds() < 3600:
        # Load data from database
        tvl_data = {}
        price_data = {}
        
        for blockchain in BLOCKCHAIN_MAPPING.keys():
            tvl_data[blockchain] = get_tvl_data_from_db(blockchain)
            price_data[blockchain] = get_price_data_from_db(blockchain)
        
        data_cache = {
            "tvl_data": tvl_data,
            "price_data": price_data,
            "last_updated": last_updated
        }
    else:
        # If we don't have recent data, fetch it
        update_data()
    
    # Start background thread
    update_thread = threading.Thread(target=background_update, daemon=True)
    update_thread.start()
    st.session_state.thread_started = True

# App header
st.title("Token Relations Dashboard 📊")

# Display last updated time
if data_cache["last_updated"]:
    last_updated = data_cache["last_updated"].astimezone(pytz.timezone('UTC'))
    st.markdown(f"<p class='last-updated'>Last updated: {last_updated.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>", unsafe_allow_html=True)

# Manual refresh button
if st.button("🔄 Refresh Data Now"):
    with st.spinner("Fetching latest data..."):
        update_data()
    st.success("Data refreshed successfully!")

# Create dashboard layout
for blockchain in BLOCKCHAIN_MAPPING.keys():
    st.markdown(f"## {blockchain}")
    
    # Create two columns for TVL and Price
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"<h3 style='text-align: center;'>Total Value Locked (TVL)</h3>", unsafe_allow_html=True)
        tvl_data = data_cache["tvl_data"].get(blockchain, pd.DataFrame())
        
        if not tvl_data.empty:
            # Create the TVL figure
            fig_tvl = go.Figure()
            fig_tvl.add_trace(
                go.Scatter(
                    x=tvl_data['date'], 
                    y=tvl_data['tvl'],
                    mode='lines',
                    name='TVL',
                    line=dict(color='#3498db', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(52, 152, 219, 0.2)'
                )
            )
            
            fig_tvl.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor='white',
                plot_bgcolor='white',
                xaxis=dict(
                    title="Date",
                    showgrid=True,
                    gridcolor='rgba(230, 230, 230, 0.8)',
                    tickfont=dict(color='#000000'),
                    title_font=dict(color='#000000')
                ),
                yaxis=dict(
                    title="TVL (USD)",
                    showgrid=True,
                    gridcolor='rgba(230, 230, 230, 0.8)',
                    tickprefix="$",
                    tickfont=dict(color='#000000'),
                    title_font=dict(color='#000000')
                ),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_tvl, use_container_width=True)
            
            # Calculate and display key metrics
            if len(tvl_data) > 0:
                current_tvl = tvl_data['tvl'].iloc[-1]
                if len(tvl_data) > 30:
                    month_ago_tvl = tvl_data['tvl'].iloc[-31]
                    monthly_change = ((current_tvl - month_ago_tvl) / month_ago_tvl) * 100
                    
                    metrics_col1, metrics_col2 = st.columns(2)
                    with metrics_col1:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <h4 style="color: #000000;">Current TVL</h4>
                            <h2>${current_tvl:,.2f}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with metrics_col2:
                        symbol = "+" if monthly_change >= 0 else ""
                        if monthly_change >= 0:
                            color_style = "color: green;"
                        else:
                            color_style = "color: red;"
                        
                        st.markdown(f"""
                        <div class='metric-card'>
                            <h4 style="color: #000000;">30-Day Change</h4>
                            <h2 style="{color_style}">{symbol}{monthly_change:.2f}%</h2>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info(f"No TVL data available for {blockchain}")
    
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>Price (USD)</h3>", unsafe_allow_html=True)
        price_data = data_cache["price_data"].get(blockchain, pd.DataFrame())
        
        if not price_data.empty:
            # Create the price figure
            fig_price = go.Figure()
            fig_price.add_trace(
                go.Scatter(
                    x=price_data['date'], 
                    y=price_data['price'],
                    mode='lines',
                    name='Price',
                    line=dict(color='#2ecc71', width=2),
                    fill='tozeroy',
                    fillcolor='rgba(46, 204, 113, 0.2)'
                )
            )
            
            fig_price.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=30, b=20),
                paper_bgcolor='white',
                plot_bgcolor='white',
                xaxis=dict(
                    title="Date",
                    showgrid=True,
                    gridcolor='rgba(230, 230, 230, 0.8)',
                    tickfont=dict(color='#000000'),
                    title_font=dict(color='#000000')
                ),
                yaxis=dict(
                    title="Price (USD)",
                    showgrid=True,
                    gridcolor='rgba(230, 230, 230, 0.8)',
                    tickprefix="$",
                    tickfont=dict(color='#000000'),
                    title_font=dict(color='#000000')
                ),
                hovermode="x unified"
            )
            
            st.plotly_chart(fig_price, use_container_width=True)
            
            # Calculate and display key metrics
            if len(price_data) > 0:
                current_price = price_data['price'].iloc[-1]
                if len(price_data) > 30:
                    month_ago_price = price_data['price'].iloc[-31]
                    price_monthly_change = ((current_price - month_ago_price) / month_ago_price) * 100
                    
                    price_metrics_col1, price_metrics_col2 = st.columns(2)
                    with price_metrics_col1:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <h4 style="color: #000000;">Current Price</h4>
                            <h2>${current_price:,.4f}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with price_metrics_col2:
                        price_symbol = "+" if price_monthly_change >= 0 else ""
                        if price_monthly_change >= 0:
                            price_color_style = "color: green;"
                        else:
                            price_color_style = "color: red;"
                        
                        st.markdown(f"""
                        <div class='metric-card'>
                            <h4 style="color: #000000;">30-Day Change</h4>
                            <h2 style="{price_color_style}">{price_symbol}{price_monthly_change:.2f}%</h2>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info(f"No price data available for {blockchain}")
    
    st.markdown("---")

