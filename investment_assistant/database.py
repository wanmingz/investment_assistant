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
        
        # Prompt 库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                prompt_content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # GPT Trend 表（存储人工写的趋势报告和对应的 idea，一一对应）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gpt_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                trend_content TEXT NOT NULL,
                idea_content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 如果表已存在但没有 idea_content 字段，添加该字段
        cursor.execute("PRAGMA table_info(gpt_trends)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'idea_content' not in columns:
            cursor.execute("ALTER TABLE gpt_trends ADD COLUMN idea_content TEXT")
        
        # GPT Idea 表（保留用于兼容，但不再使用）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gpt_ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trend_id INTEGER NOT NULL,
                idea_content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(trend_id) REFERENCES gpt_trends(id)
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
                      reasoning: Optional[str] = None,
                      price_at_creation: Optional[float] = None) -> int:
        """添加交易想法."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trade_ideas 
            (symbol, idea_description, entry_price, target_price, stop_loss, reasoning, idea_price_at_creation)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, idea_description, entry_price, target_price, stop_loss, reasoning, price_at_creation))
        
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
    
    def update_trade_idea_price_at_creation(self, idea_id: int, price: float):
        """更新交易想法创建时的价格."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE trade_ideas
            SET idea_price_at_creation = ?
            WHERE id = ?
        """, (price, idea_id))
        
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
    
    # Prompt 库相关方法
    def add_prompt(self, name: str, prompt_content: str, category: str = 'general') -> int:
        """添加 Prompt."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO prompts (name, prompt_content, category)
            VALUES (?, ?, ?)
        """, (name, prompt_content, category))
        
        prompt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return prompt_id
    
    def get_prompts(self, category: Optional[str] = None) -> List[Dict]:
        """获取 Prompt 列表."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if category:
            cursor.execute("""
                SELECT * FROM prompts
                WHERE category = ?
                ORDER BY name ASC
            """, (category,))
        else:
            cursor.execute("""
                SELECT * FROM prompts
                ORDER BY category ASC, name ASC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_prompt_by_id(self, prompt_id: int) -> Optional[Dict]:
        """根据 ID 获取 Prompt."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM prompts
            WHERE id = ?
        """, (prompt_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_prompt(self, prompt_id: int, name: str, prompt_content: str, category: str = 'general'):
        """更新 Prompt."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE prompts
            SET name = ?, prompt_content = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (name, prompt_content, category, prompt_id))
        
        conn.commit()
        conn.close()
    
    def delete_prompt(self, prompt_id: int):
        """删除 Prompt."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        
        conn.commit()
        conn.close()
    
    def get_prompt_categories(self) -> List[str]:
        """获取所有 Prompt 分类."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT category FROM prompts
            ORDER BY category ASC
        """)
        
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return categories
    
    # GPT Trend 相关方法
    def add_gpt_trend(self, title: str, trend_content: str, idea_content: Optional[str] = None) -> int:
        """添加 GPT Trend（包含对应的 idea）."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO gpt_trends (title, trend_content, idea_content)
            VALUES (?, ?, ?)
        """, (title, trend_content, idea_content))
        
        trend_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trend_id
    
    def get_gpt_trends(self, limit: int = 100) -> List[Dict]:
        """获取所有 GPT Trend."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM gpt_trends
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_gpt_trend_by_id(self, trend_id: int) -> Optional[Dict]:
        """根据 ID 获取 GPT Trend."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM gpt_trends
            WHERE id = ?
        """, (trend_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_gpt_trend(self, trend_id: int, title: str, trend_content: str, idea_content: Optional[str] = None):
        """更新 GPT Trend（包含对应的 idea）."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if idea_content is not None:
            cursor.execute("""
                UPDATE gpt_trends
                SET title = ?, trend_content = ?, idea_content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title, trend_content, idea_content, trend_id))
        else:
            cursor.execute("""
                UPDATE gpt_trends
                SET title = ?, trend_content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (title, trend_content, trend_id))
        
        conn.commit()
        conn.close()
    
    def update_gpt_trend_idea(self, trend_id: int, idea_content: str):
        """更新 GPT Trend 对应的 Idea."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE gpt_trends
            SET idea_content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (idea_content, trend_id))
        
        conn.commit()
        conn.close()
    
    def delete_gpt_trend(self, trend_id: int):
        """删除 GPT Trend（同时删除关联的 ideas）."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 先删除关联的 ideas
        cursor.execute("DELETE FROM gpt_ideas WHERE trend_id = ?", (trend_id,))
        # 再删除 trend
        cursor.execute("DELETE FROM gpt_trends WHERE id = ?", (trend_id,))
        
        conn.commit()
        conn.close()
    
    # GPT Idea 相关方法
    def add_gpt_idea(self, trend_id: int, idea_content: str) -> int:
        """添加 GPT Idea（纯文本）."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO gpt_ideas (trend_id, idea_content)
            VALUES (?, ?)
        """, (trend_id, idea_content))
        
        idea_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return idea_id
    
    def get_gpt_ideas_by_trend(self, trend_id: int) -> List[Dict]:
        """获取某个趋势的 GPT Ideas."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM gpt_ideas
            WHERE trend_id = ?
            ORDER BY created_at DESC
        """, (trend_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_gpt_idea_by_id(self, idea_id: int) -> Optional[Dict]:
        """根据 ID 获取 GPT Idea."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM gpt_ideas
            WHERE id = ?
        """, (idea_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_gpt_idea(self, idea_id: int, idea_content: str):
        """更新 GPT Idea（纯文本）."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE gpt_ideas
            SET idea_content = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (idea_content, idea_id))
        
        conn.commit()
        conn.close()
    
    def delete_gpt_idea(self, idea_id: int):
        """删除 GPT Idea."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM gpt_ideas WHERE id = ?", (idea_id,))
        
        conn.commit()
        conn.close()

