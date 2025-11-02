"""Database management module."""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import json


class Database:
    """Database manager for investment assistant."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        if db_path is None:
            # 获取当前文件的目录
            current_file = Path(__file__).resolve()
            app_dir = current_file.parent
            # 数据库文件保存在应用目录中
            db_path = str(app_dir / "investment_data.db")
        
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 投资趋势表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS investment_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start_date DATE NOT NULL,
                trend_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(week_start_date)
            )
        """)
        
        # 交易想法表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                idea_description TEXT NOT NULL,
                entry_price DECIMAL,
                target_price DECIMAL,
                stop_loss DECIMAL,
                reasoning TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 交易记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                quantity DECIMAL NOT NULL,
                price DECIMAL NOT NULL,
                amount DECIMAL NOT NULL,
                reasoning TEXT,
                trade_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    # 投资趋势相关方法
    def add_trend(self, week_start_date: str, trend_content: str) -> int:
        """添加或更新投资趋势."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 检查是否已存在该周的趋势
        cursor.execute("SELECT id FROM investment_trends WHERE week_start_date = ?", 
                      (week_start_date,))
        existing = cursor.fetchone()
        
        if existing:
            # 更新现有记录
            cursor.execute("""
                UPDATE investment_trends 
                SET trend_content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE week_start_date = ?
            """, (trend_content, week_start_date))
            trend_id = existing[0]
        else:
            # 插入新记录
            cursor.execute("""
                INSERT INTO investment_trends (week_start_date, trend_content)
                VALUES (?, ?)
            """, (week_start_date, trend_content))
            trend_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return trend_id
    
    def get_trends(self, limit: int = 52) -> List[Dict]:
        """获取投资趋势历史记录."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM investment_trends
            ORDER BY week_start_date DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_trend_by_date(self, week_start_date: str) -> Optional[Dict]:
        """根据日期获取投资趋势."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM investment_trends
            WHERE week_start_date = ?
        """, (week_start_date,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    # 交易想法相关方法
    def add_trade_idea(self, symbol: str, idea_description: str, 
                      entry_price: Optional[float] = None,
                      target_price: Optional[float] = None,
                      stop_loss: Optional[float] = None,
                      reasoning: Optional[str] = None) -> int:
        """添加交易想法."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trade_ideas 
            (symbol, idea_description, entry_price, target_price, stop_loss, reasoning)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (symbol, idea_description, entry_price, target_price, stop_loss, reasoning))
        
        idea_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return idea_id
    
    def get_trade_ideas(self, status: Optional[str] = None) -> List[Dict]:
        """获取交易想法列表."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("""
                SELECT * FROM trade_ideas
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT * FROM trade_ideas
                ORDER BY created_at DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_trade_idea_status(self, idea_id: int, status: str):
        """更新交易想法状态."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE trade_ideas
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, idea_id))
        
        conn.commit()
        conn.close()
    
    def delete_trade_idea(self, idea_id: int):
        """删除交易想法."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM trade_ideas WHERE id = ?", (idea_id,))
        
        conn.commit()
        conn.close()
    
    # 交易记录相关方法
    def add_trade(self, symbol: str, trade_type: str, quantity: float,
                  price: float, amount: float, reasoning: Optional[str] = None,
                  trade_date: Optional[str] = None) -> int:
        """添加交易记录."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if trade_date is None:
            trade_date = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute("""
            INSERT INTO trades 
            (symbol, trade_type, quantity, price, amount, reasoning, trade_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, trade_type, quantity, price, amount, reasoning, trade_date))
        
        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trade_id
    
    def get_trades(self, limit: int = 100) -> List[Dict]:
        """获取交易记录列表."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            ORDER BY trade_date DESC, created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_trades_by_symbol(self, symbol: str) -> List[Dict]:
        """根据标的获取交易记录."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM trades
            WHERE symbol = ?
            ORDER BY trade_date DESC
        """, (symbol,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_trade_statistics(self) -> Dict:
        """获取交易统计信息."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 总交易数
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_trades = cursor.fetchone()[0]
        
        # 总交易金额
        cursor.execute("SELECT SUM(amount) FROM trades")
        total_amount = cursor.fetchone()[0] or 0
        
        # 买入总额
        cursor.execute("SELECT SUM(amount) FROM trades WHERE trade_type = 'buy'")
        buy_amount = cursor.fetchone()[0] or 0
        
        # 卖出总额
        cursor.execute("SELECT SUM(amount) FROM trades WHERE trade_type = 'sell'")
        sell_amount = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_trades": total_trades,
            "total_amount": total_amount,
            "buy_amount": buy_amount,
            "sell_amount": sell_amount,
            "net_amount": buy_amount - sell_amount
        }

