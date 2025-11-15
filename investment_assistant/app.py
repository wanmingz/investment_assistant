"""Streamlit main application."""
import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import requests
from database import Database

# Helper function for symbol search
def search_stock_symbol(company_name):
    """通过公司名称搜索股票 symbol"""
    try:
        # 使用 Yahoo Finance 的搜索 API
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={company_name}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            quotes = data.get('quotes', [])
            results = []
            for quote in quotes[:10]:  # 限制返回前10个结果
                symbol = quote.get('symbol', '')
                longname = quote.get('longname', '')
                shortname = quote.get('shortname', '')
                exchange = quote.get('exchange', '')
                quote_type = quote.get('quoteType', '')
                
                # 只返回股票类型的结果
                if quote_type in ['EQUITY', 'ETF']:
                    results.append({
                        'symbol': symbol,
                        'name': longname or shortname,
                        'exchange': exchange
                    })
            return results
    except Exception as e:
        return []
    return []

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

# Clear cache if needed: uncomment the line below and save, then comment it again
# st.cache_resource.clear()

db = init_database()

# Sidebar navigation
st.sidebar.title("📈 Investment Assistant")
page = st.sidebar.radio(
    "Select Feature",
    ["GPT Trends & Ideas", "Trade Ideas", "Trade Records", "Stock Prices", "Prompt Library", "Overview"]
)

# Clear cache button
st.sidebar.divider()
if st.sidebar.button("🔄 Clear Cache"):
    st.cache_resource.clear()
    st.rerun()

# GPT Trends & Ideas page
if page == "GPT Trends & Ideas":
    st.header("🤖 GPT Trends & Ideas")
    st.markdown("Store your manually written trends and corresponding GPT-generated ideas (text only).")
    
    tab1, tab2 = st.tabs(["📊 View", "➕ Manage"])
    
    with tab1:
        st.subheader("Browse Trends and Ideas")
        
        try:
            gpt_trends = db.get_gpt_trends()
        except AttributeError:
            # Clear cache and reinitialize if method doesn't exist
            st.cache_resource.clear()
            db = init_database()
            gpt_trends = db.get_gpt_trends()
        
        if gpt_trends:
            for trend in gpt_trends:
                with st.expander(f"📈 {trend['title']} (Updated: {trend['updated_at'][:10]})", expanded=False):
                    st.markdown("### Trend Report")
                    st.markdown(trend['trend_content'])
                    st.caption(f"Created: {trend['created_at']}")
                    
                    st.divider()
                    
                    # 显示对应的 Idea（一一对应）
                    st.markdown("### 💡 Corresponding Idea")
                    if trend.get('idea_content'):
                        st.markdown(trend['idea_content'])
                    else:
                        st.info("No idea for this trend yet.")
        else:
            st.info("No GPT trends saved yet. Add your first trend in the 'Manage' tab.")
    
    with tab2:
        st.subheader("Add or Edit Trend and Ideas")
        
        # 初始化 session state
        if 'edit_trend_id' not in st.session_state:
            st.session_state.edit_trend_id = None
        if 'edit_trend_title' not in st.session_state:
            st.session_state.edit_trend_title = ""
        if 'edit_trend_content' not in st.session_state:
            st.session_state.edit_trend_content = ""
        if 'edit_trend_idea' not in st.session_state:
            st.session_state.edit_trend_idea = ""
        
        # 选择编辑模式
        edit_mode = st.checkbox("Edit existing trend", value=False)
        selected_trend_id = None
        
        if edit_mode:
            try:
                gpt_trends = db.get_gpt_trends()
            except AttributeError:
                st.cache_resource.clear()
                db = init_database()
                gpt_trends = db.get_gpt_trends()
            if gpt_trends:
                trend_options = {t['title']: t['id'] for t in gpt_trends}
                selected_trend_title = st.selectbox(
                    "Select trend to edit",
                    options=["-- Select --"] + list(trend_options.keys()),
                    key="select_trend_dropdown"
                )
                
                if selected_trend_title and selected_trend_title != "-- Select --":
                    selected_trend_id = trend_options[selected_trend_title]
                    
                    # 如果选择了新的 trend，更新 session state
                    if selected_trend_id != st.session_state.edit_trend_id:
                        trend_to_edit = db.get_gpt_trend_by_id(selected_trend_id)
                        if trend_to_edit:
                            st.session_state.edit_trend_id = selected_trend_id
                            st.session_state.edit_trend_title = trend_to_edit.get('title', '')
                            st.session_state.edit_trend_content = trend_to_edit.get('trend_content', '')
                            st.session_state.edit_trend_idea = trend_to_edit.get('idea_content', '')
            else:
                st.session_state.edit_trend_id = None
                st.session_state.edit_trend_title = ""
                st.session_state.edit_trend_content = ""
                st.session_state.edit_trend_idea = ""
                edit_mode = False
                st.info("No trends to edit. Create a new one below.")
        else:
            # 非编辑模式，清空 session state
            if st.session_state.edit_trend_id is not None:
                st.session_state.edit_trend_id = None
                st.session_state.edit_trend_title = ""
                st.session_state.edit_trend_content = ""
                st.session_state.edit_trend_idea = ""
        
        # Trend 表单
        st.markdown("### 📈 Trend Information")
        
        # 根据编辑模式使用不同的值
        if edit_mode and st.session_state.edit_trend_id:
            default_title = st.session_state.edit_trend_title
            default_content = st.session_state.edit_trend_content
            default_idea = st.session_state.edit_trend_idea
        else:
            default_title = ""
            default_content = ""
            default_idea = ""
        
        # 使用动态 key，基于 trend_id，这样选择不同 trend 时会更新
        trend_key_suffix = f"_{st.session_state.edit_trend_id}" if st.session_state.edit_trend_id else "_new"
        
        trend_title = st.text_input(
            "Trend Title *",
            value=default_title,
            help="Give your trend a descriptive title",
            key=f"gpt_trend_title{trend_key_suffix}"
        )
        
        trend_content = st.text_area(
            "Trend Content *",
            height=300,
            value=default_content,
            help="Enter your manually written trend analysis",
            key=f"gpt_trend_content{trend_key_suffix}"
        )
        
        st.divider()
        
        # Idea 表单（一一对应）
        st.markdown("### 💡 Corresponding Idea")
        
        idea_content = st.text_area(
            "Idea Content",
            height=300,
            value=default_idea,
            help="Enter GPT-generated idea content for this trend",
            key=f"gpt_idea_content{trend_key_suffix}"
        )
        
        col_save_trend, col_delete_trend = st.columns([1, 1])
        
        # 检查是否有刚保存的 trend（通过 session state）
        if 'gpt_trend_id' not in st.session_state:
            st.session_state.gpt_trend_id = None
        
        with col_save_trend:
            if edit_mode and selected_trend_id:
                if st.button("💾 Update Trend & Idea", type="primary", key="update_gpt_trend"):
                    if trend_title.strip() and trend_content.strip():
                        # 处理 idea_content，如果为空字符串则设为 None
                        idea_val = idea_content.strip() if idea_content and idea_content.strip() else None
                        try:
                            # 尝试使用新的方法签名（包含 idea_content）
                            db.update_gpt_trend(
                                selected_trend_id, 
                                trend_title.strip(), 
                                trend_content.strip(),
                                idea_val
                            )
                        except TypeError as e:
                            # 如果失败，清除缓存并重新初始化
                            st.cache_resource.clear()
                            db = init_database()
                            db.update_gpt_trend(
                                selected_trend_id, 
                                trend_title.strip(), 
                                trend_content.strip(),
                                idea_val
                            )
                        st.session_state.gpt_trend_id = selected_trend_id
                        st.success("✅ Trend & Idea updated!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields")
            else:
                if st.button("💾 Save Trend & Idea", type="primary", key="save_gpt_trend"):
                    if trend_title.strip() and trend_content.strip():
                        new_trend_id = db.add_gpt_trend(
                            trend_title.strip(), 
                            trend_content.strip(),
                            idea_content.strip() if idea_content.strip() else None
                        )
                        st.session_state.gpt_trend_id = new_trend_id
                        st.success("✅ Trend & Idea saved!")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields")
        
        with col_delete_trend:
            if edit_mode and selected_trend_id:
                if st.button("🗑️ Delete Trend", type="secondary", key="delete_gpt_trend"):
                    db.delete_gpt_trend(selected_trend_id)
                    st.session_state.gpt_trend_id = None
                    st.success("✅ Trend deleted!")
                    st.rerun()

# Trade Ideas page
elif page == "Trade Ideas":
    st.header("💡 Trade Ideas Management")
    
    tab1, tab2 = st.tabs(["➕ Add Idea", "📋 Idea List"])
    
    with tab1:
        st.subheader("Record New Trade Idea")
        
        # Symbol 搜索功能
        with st.expander("🔍 Search Symbol by Company Name", expanded=False):
            company_search = st.text_input(
                "Enter company name",
                placeholder="e.g., Apple, Microsoft, Tesla",
                key="company_search"
            )
            
            if company_search and company_search.strip():
                if st.button("🔍 Search", key="search_symbol"):
                    with st.spinner("Searching..."):
                        results = search_stock_symbol(company_search.strip())
                        
                        if results:
                            st.success(f"Found {len(results)} result(s):")
                            for i, result in enumerate(results):
                                col1, col2, col3 = st.columns([3, 2, 1])
                                with col1:
                                    st.write(f"**{result['name']}**")
                                    if result.get('exchange'):
                                        st.caption(f"Exchange: {result['exchange']}")
                                with col2:
                                    st.code(result['symbol'], language=None)
                                with col3:
                                    if st.button("✓ Select", key=f"select_{i}"):
                                        st.session_state['selected_symbol'] = result['symbol']
                                        st.rerun()
                        else:
                            st.warning("No results found. Please try a different search term.")
        
        # Symbol 输入框（自动填充选中的 symbol）
        selected_symbol = st.session_state.get('selected_symbol', '')
        if selected_symbol:
            symbol_default = selected_symbol
            # 清除 session state，避免下次自动填充
            del st.session_state['selected_symbol']
        else:
            symbol_default = ""
        
        col1, col2 = st.columns(2)
        with col1:
            symbol = st.text_input(
                "Symbol (Optional)", 
                value=symbol_default,
                placeholder="e.g., AAPL, TSLA or use search above"
            )
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
                price_at_creation = None
                # 如果有 symbol，尝试获取当前价格
                if symbol and symbol.strip():
                    try:
                        ticker = yf.Ticker(symbol.strip().upper())
                        hist = ticker.history(period="1d")
                        if not hist.empty:
                            price_at_creation = float(hist['Close'][-1])
                    except Exception as e:
                        st.warning(f"Could not fetch price for {symbol.strip()}: {str(e)}")
                
                db.add_trade_idea(
                    symbol=symbol if symbol else None,
                    idea_description=idea_description,
                    entry_price=entry_price if entry_price > 0 else None,
                    target_price=target_price if target_price > 0 else None,
                    stop_loss=stop_loss if stop_loss > 0 else None,
                    reasoning=reasoning if reasoning.strip() else None,
                    price_at_creation=price_at_creation
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
                col1, col2, col3 = st.columns([3, 2, 1])
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
                    # Performance 显示在右侧，更明显
                    if idea['symbol'] and idea.get('idea_price_at_creation'):
                        try:
                            # 获取当前价格
                            ticker = yf.Ticker(idea['symbol'])
                            hist = ticker.history(period="1d")
                            if not hist.empty:
                                current_price = float(hist['Close'][-1])
                                price_at_creation = float(idea['idea_price_at_creation'])
                                
                                # 计算 performance
                                price_change = current_price - price_at_creation
                                price_change_pct = (price_change / price_at_creation * 100) if price_at_creation > 0 else 0
                                
                                # 使用 st.metric 显示 performance，更醒目
                                st.markdown("### 📊 Performance")
                                st.metric(
                                    label="Since Creation",
                                    value=f"{price_change_pct:+.2f}%",
                                    delta=f"${price_change:+.2f}",
                                    delta_color="normal" if price_change >= 0 else "inverse"
                                )
                                
                                st.caption(f"${price_at_creation:.2f} → ${current_price:.2f}")
                                
                                # 如果有 entry_price，也显示相对于 entry_price 的 performance
                                if idea['entry_price']:
                                    entry_price = float(idea['entry_price'])
                                    entry_change = current_price - entry_price
                                    entry_change_pct = (entry_change / entry_price * 100) if entry_price > 0 else 0
                                    st.metric(
                                        label="vs Entry Price",
                                        value=f"{entry_change_pct:+.2f}%",
                                        delta=f"${entry_change:+.2f}",
                                        delta_color="normal" if entry_change >= 0 else "inverse"
                                    )
                        except Exception as e:
                            st.caption(f"⚠️ Could not fetch current price: {str(e)}")
                    elif idea['symbol'] and not idea.get('idea_price_at_creation'):
                        # 如果有 symbol 但没有历史价格，尝试获取并更新
                        try:
                            ticker = yf.Ticker(idea['symbol'])
                            # 尝试从创建日期获取历史价格
                            created_date = datetime.strptime(idea['created_at'][:10], "%Y-%m-%d")
                            end_date = created_date + timedelta(days=5)  # 获取创建日期后几天的数据
                            hist = ticker.history(start=created_date.strftime("%Y-%m-%d"), 
                                                end=end_date.strftime("%Y-%m-%d"))
                            if not hist.empty:
                                price_at_creation = float(hist['Close'][0])
                                db.update_trade_idea_price_at_creation(idea['id'], price_at_creation)
                                st.rerun()
                        except Exception:
                            pass
                    else:
                        st.info("No performance data")
                
                with col3:
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

# Prompt Library page
elif page == "Prompt Library":
    st.header("📋 Prompt Library")
    st.markdown("Manage your ChatGPT prompts for investment analysis. Store, edit, and organize prompts that you frequently use.")
    
    tab1, tab2 = st.tabs(["➕ Add New Prompt", "📚 Browse & Edit Prompts"])
    
    with tab1:
        st.subheader("Add New Prompt")
        st.markdown("Enter your prompt below and save it for future use in ChatGPT.")
        
        try:
            # Get categories for dropdown
            prompt_categories = db.get_prompt_categories()
            
            # Form for adding prompt
            col1, col2 = st.columns([2, 1])
            
            with col1:
                prompt_name = st.text_input(
                    "Prompt Name *",
                    value="",
                    help="Give your prompt a descriptive name (e.g., '6-Month Market Analysis')",
                    key="new_prompt_name"
                )
            
            with col2:
                # Get unique categories or allow custom
                category_options = list(set(prompt_categories + ['general', 'investment', 'analysis', 'market', 'trend']))
                category = st.selectbox(
                    "Category",
                    options=sorted(category_options),
                    index=0,
                    key="new_prompt_category"
                )
            
            prompt_content = st.text_area(
                "Prompt Content *",
                height=400,
                value="",
                help="Enter your prompt text here. This is what you'll copy and use in ChatGPT or other AI tools.",
                key="new_prompt_content",
                placeholder="Example: Analyze the current market trends for the next 6 months and provide investment recommendations..."
            )
            
            col_save, col_clear = st.columns([1, 1])
            
            with col_save:
                if st.button("💾 Save Prompt", type="primary", key="save_new_prompt"):
                    if prompt_name.strip() and prompt_content.strip():
                        try:
                            db.add_prompt(prompt_name.strip(), prompt_content.strip(), category)
                            st.success("✅ Prompt saved successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error saving prompt: {str(e)}")
                    else:
                        st.error("Please fill in both Prompt Name and Prompt Content")
            
            with col_clear:
                if st.button("🗑️ Clear Form", key="clear_new_prompt"):
                    st.rerun()
                    
        except AttributeError as e:
            st.error("Database error. Please restart the application.")
            st.code(str(e))
    
    with tab2:
        st.subheader("Browse & Edit Saved Prompts")
        
        try:
            # Filter by category
            all_categories = db.get_prompt_categories()
            if all_categories:
                filter_category = st.selectbox(
                    "Filter by Category",
                    options=["All"] + sorted(all_categories),
                    index=0,
                    key="filter_category_browse"
                )
            else:
                filter_category = "All"
            
            # Get prompts
            if filter_category == "All":
                display_prompts = db.get_prompts()
            else:
                display_prompts = db.get_prompts(category=filter_category)
            
            if display_prompts:
                # Edit section
                st.markdown("### ✏️ Edit Prompt")
                prompt_options = {f"{p['name']} ({p['category']})": p['id'] for p in display_prompts}
                selected_prompt_display = st.selectbox(
                    "Select prompt to edit or delete",
                    options=["-- Select a prompt --"] + list(prompt_options.keys()),
                    key="edit_prompt_select"
                )
                
                if selected_prompt_display and selected_prompt_display != "-- Select a prompt --":
                    selected_prompt_id = prompt_options[selected_prompt_display]
                    prompt_to_edit = db.get_prompt_by_id(selected_prompt_id)
                    
                    if prompt_to_edit:
                        st.divider()
                        
                        col_edit1, col_edit2 = st.columns([2, 1])
                        
                        with col_edit1:
                            edit_prompt_name = st.text_input(
                                "Prompt Name *",
                                value=prompt_to_edit['name'],
                                key="edit_prompt_name"
                            )
                        
                        with col_edit2:
                            edit_category_options = list(set(all_categories + ['general', 'investment', 'analysis', 'market', 'trend']))
                            edit_category = st.selectbox(
                                "Category",
                                options=sorted(edit_category_options),
                                index=sorted(edit_category_options).index(prompt_to_edit['category']) if prompt_to_edit['category'] in edit_category_options else 0,
                                key="edit_prompt_category"
                            )
                        
                        edit_prompt_content = st.text_area(
                            "Prompt Content *",
                            height=300,
                            value=prompt_to_edit['prompt_content'],
                            key="edit_prompt_content"
                        )
                        
                        col_update, col_delete = st.columns([1, 1])
                        
                        with col_update:
                            if st.button("💾 Update Prompt", type="primary", key="update_prompt_btn"):
                                if edit_prompt_name.strip() and edit_prompt_content.strip():
                                    try:
                                        db.update_prompt(selected_prompt_id, edit_prompt_name.strip(), edit_prompt_content.strip(), edit_category)
                                        st.success("✅ Prompt updated!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error updating prompt: {str(e)}")
                                else:
                                    st.error("Please fill in all required fields")
                        
                        with col_delete:
                            if st.button("🗑️ Delete Prompt", type="secondary", key="delete_prompt_btn"):
                                try:
                                    db.delete_prompt(selected_prompt_id)
                                    st.success("✅ Prompt deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting prompt: {str(e)}")
                
                st.divider()
                st.markdown("### 📚 All Saved Prompts")
                
                # Group by category
                prompts_by_category = {}
                for prompt in display_prompts:
                    cat = prompt['category']
                    if cat not in prompts_by_category:
                        prompts_by_category[cat] = []
                    prompts_by_category[cat].append(prompt)
                
                for category, category_prompts in sorted(prompts_by_category.items()):
                    st.markdown(f"#### 📁 {category}")
                    
                    for prompt in category_prompts:
                        with st.expander(f"📝 {prompt['name']} (Updated: {prompt['updated_at'][:10]})"):
                            st.text_area(
                                "Content",
                                value=prompt['prompt_content'],
                                height=200,
                                disabled=True,
                                key=f"view_{prompt['id']}"
                            )
                            st.caption(f"Created: {prompt['created_at']}")
                            
                            # Display prompt content in code block for easy copying
                            st.markdown("**Copy this prompt:**")
                            st.code(prompt['prompt_content'], language=None)
            else:
                st.info("No prompts saved yet. Add your first prompt in the 'Add New Prompt' tab!")
                
        except AttributeError as e:
            st.error("Database error. Please restart the application.")
            st.code(str(e))

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

