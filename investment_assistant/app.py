"""Streamlit main application."""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from database import Database

# Page configuration
st.set_page_config(
    page_title="Investment Assistant",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    """Initialize database connection."""
    return Database()

db = init_database()

# Sidebar navigation
st.sidebar.title("📈 Investment Assistant")
page = st.sidebar.radio(
    "Select Feature",
    ["Investment Trends", "Trade Ideas", "Trade Records", "Stock Prices", "Overview"]
)

# Investment Trends page
if page == "Investment Trends":
    st.header("📊 6-Month Investment Trends")
    
    tab1, tab2 = st.tabs(["📝 Update Trend", "📚 History"])
    
    with tab1:
        st.subheader("Weekly Investment Trend Update")
        
        # Calculate week start date for next 26 weeks (6 months)
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        col1, col2 = st.columns(2)
        with col1:
            week_start_date = st.date_input(
                "Select Week Start Date",
                value=week_start,
                min_value=week_start,
                max_value=week_start + timedelta(weeks=26)
            )
        
        with col2:
            existing_trend = db.get_trend_by_date(week_start_date.strftime("%Y-%m-%d"))
            if existing_trend:
                st.info(f"Record exists for this week, created at: {existing_trend['created_at']}")
        
        trend_content = st.text_area(
            "Investment Trend Content",
            height=300,
            help="Enter investment trend analysis and predictions for the next 6 months. Supports Markdown format and tables.",
            value=existing_trend.get('trend_content', '') if existing_trend else ""
        )
        
        if st.button("💾 Save Trend", type="primary"):
            if trend_content.strip():
                db.add_trend(
                    week_start_date.strftime("%Y-%m-%d"),
                    trend_content
                )
                st.success("✅ Trend saved!")
                st.rerun()
            else:
                st.error("Please enter trend content")
    
    with tab2:
        st.subheader("Trend History")
        
        trends = db.get_trends(limit=52)
        
        if trends:
            for trend in trends:
                with st.expander(
                    f"📅 {trend['week_start_date']} (Updated: {trend['updated_at']})",
                    expanded=False
                ):
                    st.write(trend['trend_content'])
                    st.caption(f"Created: {trend['created_at']}")
        else:
            st.info("No history records")

# Trade Ideas page
elif page == "Trade Ideas":
    st.header("💡 Trade Ideas Management")
    
    tab1, tab2 = st.tabs(["➕ Add Idea", "📋 Idea List"])
    
    with tab1:
        st.subheader("Record New Trade Idea")
        
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Symbol", placeholder="e.g., AAPL, TSLA")
            entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f")
            target_price = st.number_input("Target Price", min_value=0.0, format="%.2f")
        
        with col2:
            stop_loss = st.number_input("Stop Loss", min_value=0.0, format="%.2f")
            status = st.selectbox("Status", ["active", "completed", "cancelled"], index=0)
        
        idea_description = st.text_area(
            "Idea Description",
            height=150,
            placeholder="Describe the core content of this trade idea..."
        )
        
        reasoning = st.text_area(
            "Investment Reasoning",
            height=150,
            placeholder="Explain in detail why you are bullish on this investment opportunity..."
        )
        
        if st.button("💾 Save Idea", type="primary"):
            if idea_description.strip():
                db.add_trade_idea(
                    symbol=symbol if symbol else None,
                    idea_description=idea_description,
                    entry_price=entry_price if entry_price > 0 else None,
                    target_price=target_price if target_price > 0 else None,
                    stop_loss=stop_loss if stop_loss > 0 else None,
                    reasoning=reasoning if reasoning.strip() else None
                )
                st.success("✅ Trade idea saved!")
                st.rerun()
            else:
                st.error("Please enter idea description")
    
    with tab2:
        st.subheader("Trade Ideas List")
        
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "active", "completed", "cancelled"],
            index=0
        )
        
        ideas = db.get_trade_ideas(
            status=None if status_filter == "All" else status_filter
        )
        
        if ideas:
            for idea in ideas:
                col1, col2 = st.columns([4, 1])
                with col1:
                    status_color = {
                        "active": "🟢",
                        "completed": "✅",
                        "cancelled": "❌"
                    }
                    st.markdown(
                        f"### {status_color.get(idea['status'], '⚪')} "
                        f"{idea['symbol'] or 'No Symbol'} - {idea['idea_description'][:50]}..."
                    )
                    
                    details = []
                    if idea['entry_price']:
                        details.append(f"Entry: ${idea['entry_price']:.2f}")
                    if idea['target_price']:
                        details.append(f"Target: ${idea['target_price']:.2f}")
                    if idea['stop_loss']:
                        details.append(f"Stop Loss: ${idea['stop_loss']:.2f}")
                    
                    if details:
                        st.caption(" | ".join(details))
                    
                    if idea['reasoning']:
                        with st.expander("View Details"):
                            st.write("**Idea Description:**")
                            st.write(idea['idea_description'])
                            st.write("**Investment Reasoning:**")
                            st.write(idea['reasoning'])
                    
                    st.caption(f"Created: {idea['created_at']}")
                
                with col2:
                    if st.button("Delete", key=f"delete_{idea['id']}"):
                        db.delete_trade_idea(idea['id'])
                        st.rerun()
                    if idea['status'] == 'active':
                        if st.button("Complete", key=f"complete_{idea['id']}"):
                            db.update_trade_idea_status(idea['id'], 'completed')
                            st.rerun()
                st.divider()
        else:
            st.info("No trade ideas")

# Trade Records page
elif page == "Trade Records":
    st.header("💰 Trade Records")
    
    tab1, tab2 = st.tabs(["➕ Add Trade", "📋 Trade History"])
    
    with tab1:
        st.subheader("Record New Trade")
        
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input("Symbol *", placeholder="e.g., AAPL")
            trade_type = st.selectbox("Trade Type *", ["buy", "sell"], index=0)
            quantity = st.number_input("Quantity *", min_value=0.0, format="%.4f")
        
        with col2:
            price = st.number_input("Price *", min_value=0.0, format="%.2f")
            trade_date = st.date_input(
                "Trade Date *",
                value=datetime.now()
            )
        
        # Auto-calculate amount
        calculated_amount = quantity * price if quantity > 0 and price > 0 else 0.0
        
        st.number_input(
            "Amount (Auto-calculated)",
            min_value=0.0,
            format="%.2f",
            value=calculated_amount,
            disabled=True,
            help="Auto-calculated: Quantity × Price"
        )
        
        reasoning = st.text_area(
            "Trade Reasoning",
            height=150,
            placeholder="Explain why you made this trade..."
        )
        
        if st.button("💾 Save Trade", type="primary"):
            if symbol.strip() and quantity > 0 and price > 0:
                db.add_trade(
                    symbol=symbol,
                    trade_type=trade_type,
                    quantity=quantity,
                    price=price,
                    amount=calculated_amount,
                    reasoning=reasoning if reasoning.strip() else None,
                    trade_date=trade_date.strftime("%Y-%m-%d")
                )
                st.success("✅ Trade record saved!")
                st.rerun()
            else:
                st.error("Please fill in all required fields (Symbol, Quantity, Price)")
    
    with tab2:
        st.subheader("Trade History")
        
        trades = db.get_trades(limit=100)
        
        if trades:
            # Convert to DataFrame for display
            df = pd.DataFrame(trades)
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            stats = db.get_trade_statistics()
            
            with col1:
                st.metric("Total Trades", stats['total_trades'])
            with col2:
                st.metric("Total Buy", f"${stats['buy_amount']:,.2f}")
            with col3:
                st.metric("Total Sell", f"${stats['sell_amount']:,.2f}")
            with col4:
                st.metric("Net Amount", f"${stats['net_amount']:,.2f}")
            
            st.divider()
            
            # Trade list
            for trade in trades:
                trade_type_icon = "🟢 Buy" if trade['trade_type'] == 'buy' else "🔴 Sell"
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                with col1:
                    st.markdown(f"**{trade['symbol']}**")
                    st.caption(trade_type_icon)
                with col2:
                    st.write(f"Quantity: {trade['quantity']:.4f}")
                    st.write(f"Price: ${trade['price']:.2f}")
                with col3:
                    st.write(f"Amount: ${trade['amount']:,.2f}")
                    st.caption(f"Date: {trade['trade_date']}")
                with col4:
                    if trade['reasoning']:
                        with st.expander("View Reasoning"):
                            st.write(trade['reasoning'])
                
                st.divider()
        else:
            st.info("No trade records")

# Stock Prices page
elif page == "Stock Prices":
    st.header("📊 Stock Price Lookup")
    
    # Initialize session state for stock symbols and period
    if 'stock_symbols' not in st.session_state:
        st.session_state.stock_symbols = ""
    if 'stock_period' not in st.session_state:
        st.session_state.stock_period = "6mo"
    
    # Input section
    col1, col2 = st.columns([3, 1])
    with col1:
        # Remove key to avoid session_state conflicts with quick access buttons
        # The value parameter will control the input, synced with session_state
        symbols_input = st.text_input(
            "Enter Stock Symbols",
            value=st.session_state.stock_symbols,
            placeholder="e.g., AAPL, MSFT, TSLA or AAPL MSFT TSLA",
            help="Enter one or more stock symbols separated by commas or spaces"
        )
        # Sync: update session state from input
        st.session_state.stock_symbols = symbols_input
    
    with col2:
        # Find current period index
        period_options = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        current_index = period_options.index(st.session_state.stock_period) if st.session_state.stock_period in period_options else 4
        
        period = st.selectbox(
            "Time Period",
            period_options,
            index=current_index,
            help="Select the time period for historical data",
            key="period_select_key"
        )
        # Update session state with current period
        st.session_state.stock_period = period
    
    if symbols_input:
        # Parse symbols
        symbols = [s.strip().upper() for s in symbols_input.replace(",", " ").split() if s.strip()]
        
        if symbols:
            # Create tabs for different views
            view_tabs = st.tabs(["📈 Price Chart", "📋 Details", "📊 Comparison"])
            
            with view_tabs[0]:
                # Fetch data for each symbol
                for symbol in symbols:
                    try:
                        with st.spinner(f"Loading {symbol}..."):
                            ticker = yf.Ticker(symbol)
                            hist = ticker.history(period=period)
                            
                            if not hist.empty:
                                st.subheader(f"{symbol}")
                                
                                # Get current price info
                                current_price = hist['Close'][-1]
                                prev_close = hist['Close'][-2] if len(hist) > 1 else current_price
                                change = current_price - prev_close
                                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                                
                                # Display key metrics
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Current Price", f"${current_price:.2f}")
                                with col2:
                                    st.metric("Change", f"${change:.2f}", f"{change_pct:+.2f}%")
                                with col3:
                                    day_high = hist['High'][-1] if len(hist) > 0 else current_price
                                    st.metric("Day High", f"${day_high:.2f}")
                                with col4:
                                    day_low = hist['Low'][-1] if len(hist) > 0 else current_price
                                    st.metric("Day Low", f"${day_low:.2f}")
                                
                                # Price chart
                                st.markdown("**Price Chart**")
                                st.line_chart(hist['Close'])
                                
                                # Volume chart
                                st.markdown("**Volume**")
                                st.bar_chart(hist['Volume'])
                            else:
                                st.error(f"No data available for {symbol}")
                    except Exception as e:
                        st.error(f"Error loading {symbol}: {str(e)}")
                        st.info(f"Make sure {symbol} is a valid stock symbol (e.g., AAPL, MSFT, TSLA)")
            
            with view_tabs[1]:
                # Detailed information for each symbol
                for symbol in symbols:
                    try:
                        with st.spinner(f"Loading details for {symbol}..."):
                            ticker = yf.Ticker(symbol)
                            info = ticker.info
                            hist = ticker.history(period="1mo")
                            
                            if info and not hist.empty:
                                company_name = info.get('longName', info.get('shortName', symbol))
                                st.subheader(f"{company_name} ({symbol})")
                                
                                # Key statistics
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.markdown("### Market Data")
                                    current_price = info.get('currentPrice', hist['Close'][-1])
                                    prev_close = info.get('previousClose', 0)
                                    market_cap = info.get('marketCap', 0)
                                    volume = info.get('volume', hist['Volume'][-1] if len(hist) > 0 else 0)
                                    week_high = info.get('fiftyTwoWeekHigh', 0)
                                    week_low = info.get('fiftyTwoWeekLow', 0)
                                    
                                    metrics = {
                                        "Current Price": f"${current_price:.2f}" if current_price else "N/A",
                                        "Previous Close": f"${prev_close:.2f}" if prev_close else "N/A",
                                        "Market Cap": f"${market_cap:,.0f}" if market_cap else "N/A",
                                        "Volume": f"{volume:,.0f}" if volume else "N/A",
                                        "52 Week High": f"${week_high:.2f}" if week_high else "N/A",
                                        "52 Week Low": f"${week_low:.2f}" if week_low else "N/A",
                                    }
                                    for key, value in metrics.items():
                                        st.write(f"**{key}:** {value}")
                                
                                with col2:
                                    st.markdown("### Company Info")
                                    company_info = {
                                        "Sector": info.get('sector', 'N/A'),
                                        "Industry": info.get('industry', 'N/A'),
                                        "Exchange": info.get('exchange', 'N/A'),
                                        "Currency": info.get('currency', 'USD'),
                                    }
                                    for key, value in company_info.items():
                                        st.write(f"**{key}:** {value}")
                                
                                # Recent data table
                                st.markdown("### Recent Price Data (Last 10 Days)")
                                recent_data = hist.tail(10)[['Open', 'High', 'Low', 'Close', 'Volume']]
                                recent_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                                st.dataframe(recent_data, use_container_width=True, hide_index=True)
                            else:
                                st.error(f"Could not load details for {symbol}")
                    except Exception as e:
                        st.error(f"Error loading {symbol}: {str(e)}")
            
            with view_tabs[2]:
                # Compare multiple symbols
                if len(symbols) > 1:
                    st.subheader("Price Comparison")
                    
                    try:
                        # Fetch data for all symbols
                        data_dict = {}
                        for symbol in symbols:
                            ticker = yf.Ticker(symbol)
                            hist = ticker.history(period=period)
                            if not hist.empty:
                                data_dict[symbol] = hist['Close']
                        
                        if data_dict:
                            # Normalize prices (start from 100 for easier comparison)
                            comparison_df = pd.DataFrame(data_dict)
                            normalized_df = comparison_df / comparison_df.iloc[0] * 100
                            
                            st.line_chart(normalized_df)
                            
                            # Performance comparison table
                            st.markdown("### Performance Comparison")
                            performance_data = []
                            for symbol in symbols:
                                if symbol in data_dict:
                                    series = data_dict[symbol]
                                    start_price = series.iloc[0]
                                    end_price = series.iloc[-1]
                                    total_return = ((end_price - start_price) / start_price) * 100
                                    performance_data.append({
                                        "Symbol": symbol,
                                        "Start Price": f"${start_price:.2f}",
                                        "End Price": f"${end_price:.2f}",
                                        "Total Return": f"{total_return:+.2f}%"
                                    })
                            
                            if performance_data:
                                st.dataframe(pd.DataFrame(performance_data), use_container_width=True, hide_index=True)
                        else:
                            st.error("Could not load data for comparison")
                    except Exception as e:
                        st.error(f"Error in comparison: {str(e)}")
                else:
                    st.info("Enter multiple symbols to compare (e.g., AAPL MSFT TSLA)")
        
        else:
            st.warning("Please enter at least one valid stock symbol")
    else:
        st.info("Enter stock symbols above to get started. Examples: AAPL, MSFT, TSLA, GOOGL")
        
        # Popular stocks quick access
        st.markdown("### Quick Access")
        popular_stocks = {
            "Tech": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
            "Finance": ["JPM", "BAC", "GS", "WFC"],
            "Consumer": ["AMZN", "TSLA", "NKE", "WMT", "MC.PA"],
            "International": ["TSM", "ASML", "BABA", "PDD"]
        }
        
        for category, stocks in popular_stocks.items():
            st.markdown(f"**{category}**")
            cols = st.columns(len(stocks))
            for i, stock in enumerate(stocks):
                with cols[i]:
                    if st.button(stock, key=f"quick_{stock}", use_container_width=True):
                        # Update session state - input field will read this value on rerun
                        st.session_state.stock_symbols = stock
                        st.rerun()

# Overview page
elif page == "Overview":
    st.header("📊 Data Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📈 Investment Trends")
        trends = db.get_trends(limit=1)
        if trends:
            st.metric("Latest Trend Date", trends[0]['week_start_date'])
            st.metric("Total Trend Records", len(db.get_trends(limit=1000)))
        else:
            st.info("No trend records")
    
    with col2:
        st.subheader("💡 Trade Ideas")
        ideas = db.get_trade_ideas()
        active_ideas = [i for i in ideas if i['status'] == 'active']
        st.metric("Active Ideas", len(active_ideas))
        st.metric("Total Ideas", len(ideas))
    
    with col3:
        st.subheader("💰 Trade Records")
        stats = db.get_trade_statistics()
        st.metric("Total Trades", stats['total_trades'])
        st.metric("Total Amount", f"${stats['total_amount']:,.2f}")
    
    # Recent trades
    st.divider()
    st.subheader("📋 Recent Trades")
    recent_trades = db.get_trades(limit=10)
    if recent_trades:
        df_trades = pd.DataFrame(recent_trades)
        df_trades['trade_date'] = pd.to_datetime(df_trades['trade_date'])
        st.dataframe(
            df_trades[['symbol', 'trade_type', 'quantity', 'price', 'amount', 'trade_date']],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No trade records")

