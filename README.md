# Investment Assistant

AI-powered personal investment assistant application to help you manage investment trends, trade ideas, and trade records.

## My Core Belief

I believe investing is one of the fairest systems in the world.

In the market, price doesn't care about your background, where you grew up, your school, or your network. Everyone sees the same price. Everyone has access to information.

What truly makes the difference is understanding — and understanding can be improved through learning and effort.

Technology and AI accelerate this fairness:

- Tech makes information transparent
- AI lowers the learning barrier
- Automation removes emotional bias

In the past, wealth was distributed by connections and privilege. Today, through technology and investing, wealth is increasingly distributed by cognition.

My goal is to build tools that help more people gain clarity, make smarter decisions, and participate in this fairness — not just as observers, but as active participants shaping their own financial future.

## Features

### 1. 📊 6-Month Investment Trends Weekly Updates
- Record and update investment trend analysis for the next 6 months
- View historical trend records
- Support weekly management and tracking of trend changes

### 2. 💡 Trade Ideas Management
- Record investment ideas and strategies
- Set entry price, target price, and stop loss
- Record detailed investment reasoning
- Support idea status management (active/completed/cancelled)

### 3. 💰 Trade Records
- Record detailed information for each trade
- Include trade time, amount, symbol, quantity, and price
- Record trade reasoning
- Automatically calculate trade amounts and statistics

### 4. 📈 Stock Price Lookup
- Real-time stock price and historical data queries
- Support multiple stock symbols simultaneous queries (separated by commas or spaces)
- Multiple time period options (1 day to maximum history)
- Price and volume chart visualization
- Detailed stock information and company data (market cap, volume, 52-week high/low, etc.)
- Multi-stock price comparison and return analysis
- Quick access to popular stocks (Tech, Finance, Consumer, International sectors)

### 5. 📊 Data Overview
- View statistics for all data
- Quick overview of investment activities

## Installation

### Using Poetry (Recommended)

```bash
# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
pip install streamlit openai yfinance pandas python-dotenv
```

## Running

```bash
# Using Poetry
poetry run streamlit run investment_assistant/app.py

# Or run directly
streamlit run investment_assistant/app.py
```

## Data Storage

The application uses SQLite database to store data. The database file `investment_data.db` will be automatically created on first run.

## Environment Variables (Optional)

If you need to use OpenAI API for AI-assisted analysis (future feature), you can create a `.env` file in the project root directory:

```
OPENAI_API_KEY=your_api_key_here
```

## Project Structure

```
investment-assistant/
├── investment_assistant/        # Main application package
│   ├── __init__.py             # Package initialization file
│   ├── app.py                  # Streamlit main application
│   ├── database.py             # Database management module
│   └── investment_data.db      # SQLite database file (auto-generated)
├── pyproject.toml              # Poetry project configuration file
├── poetry.lock                  # Poetry dependency lock file
├── README.md                    # Project documentation
└── .env                         # Environment variables file (optional, needs manual creation)
```

**Notes:**
- `investment_data.db`: The database file will be automatically created in the `investment_assistant/` directory on first run
- `.env`: Optional file for storing sensitive information like API keys, needs to be created manually
- `poetry.lock`: Auto-generated dependency version lock file by Poetry
- `__pycache__/`: Python cache directory (auto-generated, can be ignored)

## Usage

1. **Investment Trends**: Update investment trends for the next 6 months weekly. The system will automatically save historical records
2. **Trade Ideas**: Record investment ideas you want to execute, including symbols, price ranges, and reasoning
3. **Trade Records**: Record detailed trade information after executing actual trades
4. **Stock Price Lookup**: Enter stock symbols (e.g., AAPL, MSFT, TSLA) to query real-time prices, historical data, and detailed information
5. **Data Overview**: View aggregated statistics of all data

## Tech Stack

- **Streamlit**: Web application framework
- **SQLite**: Data storage
- **Pandas**: Data processing
- **yfinance**: Stock data retrieval
- **Python 3.11+**: Runtime environment

## License

MIT License
