# -*- coding: utf-8 -*-
"""
数据接口模块 - 统一数据访问接口
提供标准化的数据读取方法，屏蔽底层存储细节
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
import glob
from datetime import datetime, timedelta

class DataInterface:
    """统一数据访问接口"""
    
    def __init__(self, config_path: str = "config/factors.yml"):
        """初始化数据接口
        
        Args:
            config_path: 配置文件路径
        """
        self.base_path = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.universe = self._load_universe()
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = self.base_path / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_universe(self) -> List[str]:
        """加载ETF/指数池"""
        universe_file = self.base_path / self.config['data']['universe_file']
        if universe_file.exists():
            df = pd.read_csv(universe_file)
            return df['ts_code'].tolist()
        else:
            # 如果没有universe文件，从原始数据推断
            raw_path = self.base_path / self.config['paths']['raw_data']
            price_files = glob.glob(str(raw_path / "*_price_*.parquet"))
            universe = [os.path.basename(f).split('_')[0] for f in price_files]
            return sorted(list(set(universe)))
    
    def get_price_data(self, start_date: str = None, end_date: str = None) -> Dict[str, pd.DataFrame]:
        """获取价格数据
        
        Args:
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            
        Returns:
            包含各价格字段的字典 {'close': DataFrame, 'vol': DataFrame, ...}
        """
        start_date = start_date or self.config['data']['start_date']
        end_date = end_date or self.config['data']['end_date']
        
        # 读取processed数据
        processed_path = self.base_path / self.config['paths']['processed_data']
        
        # 初始化结果字典 - 只包含可用字段
        price_data = {
            'close': pd.DataFrame(),
            'vol': pd.DataFrame(), 
            'amount': pd.DataFrame(),
            'open': pd.DataFrame(),
            'high': pd.DataFrame(),
            'low': pd.DataFrame(),
            'pct_chg': pd.DataFrame()
        }
        
        print(f"正在读取价格数据: {start_date} 到 {end_date}")
        
        # 查找所有processed parquet文件
        parquet_files = glob.glob(str(processed_path / "**/*.parquet"), recursive=True)
        
        for parquet_file in parquet_files:
            try:
                df = pd.read_parquet(parquet_file)
                
                # 检查trade_date是否为索引
                if df.index.name == 'trade_date':
                    # 如果trade_date已经是索引，直接使用
                    df.index = pd.to_datetime(df.index)
                elif 'trade_date' in df.columns:
                    # 如果trade_date是列，设置为索引
                    if df['trade_date'].dtype == 'int64':
                        df['trade_date'] = pd.to_datetime(df['trade_date'], unit='ms')
                    else:
                        df['trade_date'] = pd.to_datetime(df['trade_date'])
                    df = df.set_index('trade_date')
                else:
                    print(f"文件 {parquet_file} 没有 trade_date 字段或索引，跳过")
                    continue
                
                # 提取ts_code
                if 'ts_code' not in df.columns:
                    print(f"文件 {parquet_file} 缺少 ts_code 字段，跳过")
                    continue
                
                ts_codes = df['ts_code'].unique()
                
                for ts_code in ts_codes:
                    stock_data = df[df['ts_code'] == ts_code].copy()
                    stock_data = stock_data.sort_index()
                    
                    # 过滤日期范围
                    mask = (stock_data.index >= start_date) & (stock_data.index <= end_date)
                    stock_data = stock_data[mask]
                    
                    if stock_data.empty:
                        continue
                    
                    # 提取各字段 - 只处理存在的字段
                    for field in price_data.keys():
                        if field in stock_data.columns:
                            if price_data[field].empty:
                                price_data[field] = pd.DataFrame(index=stock_data.index)
                            
                            # 确保索引对齐
                            price_data[field] = price_data[field].reindex(
                                price_data[field].index.union(stock_data.index)
                            )
                            price_data[field][ts_code] = stock_data[field]
                        
            except Exception as e:
                print(f"读取文件 {parquet_file} 失败: {e}")
                continue
        
        # 对齐所有数据的索引
        common_index = None
        for field, df in price_data.items():
            if not df.empty:
                if common_index is None:
                    common_index = df.index
                else:
                    common_index = common_index.intersection(df.index)
        
        if common_index is not None and len(common_index) > 0:
            for field in price_data.keys():
                if not price_data[field].empty:
                    price_data[field] = price_data[field].reindex(common_index).sort_index()
                else:
                    # 如果某个字段完全为空，创建空的DataFrame但保持正确的索引
                    price_data[field] = pd.DataFrame(index=common_index)
        
        print(f"价格数据读取完成，共{len(common_index) if common_index is not None else 0}个交易日，"
              f"{len(price_data['close'].columns) if not price_data['close'].empty else 0}个标的")
        
        return price_data
    
    def get_forward_returns(self, days: int = 1, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取前瞻收益率
        
        Args:
            days: 前瞻天数
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            前瞻收益率矩阵 DataFrame(index=date, columns=ts_code)
        """
        price_data = self.get_price_data(start_date, end_date)
        close = price_data['close']
        
        if close.empty:
            return pd.DataFrame()
        
        # 计算前瞻收益率
        forward_ret = close.pct_change(days, fill_method=None).shift(-days)
        
        print(f"前瞻{days}日收益率计算完成")
        return forward_ret
    
    def get_universe(self) -> List[str]:
        """获取标的池"""
        return self.universe
    
    def save_factor_data(self, factor_data: pd.DataFrame, factor_name: str):
        """保存因子数据
        
        Args:
            factor_data: 因子数据
            factor_name: 因子名称
        """
        output_path = self.base_path / self.config['paths']['factors_output']
        output_path.mkdir(parents=True, exist_ok=True)
        
        file_path = output_path / f"{factor_name}.parquet"
        factor_data.to_parquet(file_path)
        print(f"因子数据已保存: {file_path}")
    
    def load_factor_data(self, factor_name: str) -> pd.DataFrame:
        """加载因子数据
        
        Args:
            factor_name: 因子名称
            
        Returns:
            因子数据 DataFrame
        """
        file_path = self.base_path / self.config['paths']['factors_output'] / f"{factor_name}.parquet"
        if file_path.exists():
            return pd.read_parquet(file_path)
        else:
            raise FileNotFoundError(f"因子文件不存在: {file_path}")
    
    def get_all_factor_names(self) -> List[str]:
        """获取所有启用的因子名称"""
        return [name for name, config in self.config['factors'].items() 
                if config.get('enabled', True)]
    
    def _log_progress(self, message: str, **kwargs):
        """日志记录接口（预留扩展）"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [DataInterface] {message}")
