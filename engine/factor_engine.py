# -*- coding: utf-8 -*-
"""
因子计算引擎 - 统一因子计算接口
包含所有基础因子的计算逻辑和标准化处理
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional
import yaml
from pathlib import Path
from datetime import datetime

class FactorEngine:
    """因子计算引擎"""
    
    def __init__(self, config_path: str = "config/factors.yml"):
        """初始化因子引擎
        
        Args:
            config_path: 配置文件路径
        """
        self.base_path = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.preprocessing_config = self.config.get('preprocessing', {})
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = self.base_path / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    # ========== 价格衍生因子 ==========
    
    def mom_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """动量因子：N日价格动量
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            动量因子矩阵
        """
        return close.pct_change(window, fill_method=None)
    
    def short_rev_5(self, close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """短期反转因子：N日反转动量
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            短期反转因子矩阵（取负值）
        """
        return -close.pct_change(window, fill_method=None)
    
    def volatility_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """波动率因子：N日收益率标准差
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            波动率因子矩阵
        """
        returns = close.pct_change(fill_method=None)
        return returns.rolling(window).std()
    
    # ========== 量价因子 ==========
    
    def turnover_mean(self, vol: pd.DataFrame, amount: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """换手率因子：N日换手率均值（基于成交量和成交额）
        
        Args:
            vol: 成交量矩阵
            amount: 成交额矩阵
            window: 计算窗口
            
        Returns:
            换手率因子矩阵
        """
        # 使用成交量作为换手率的代理指标
        # 取对数避免极值影响
        log_vol = np.log(vol.replace(0, np.nan))
        return log_vol.rolling(window).mean()
    
    def amihud_20(self, close: pd.DataFrame, amount: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Amihud流动性因子：N日非流动性指标
        
        Args:
            close: 收盘价矩阵
            amount: 成交额矩阵
            window: 计算窗口
            
        Returns:
            流动性因子矩阵（取负值，值越大流动性越好）
        """
        returns = close.pct_change(fill_method=None).abs()
        illiq = (returns / amount.replace(0, np.nan)).rolling(window).mean()
        return -illiq  # 取负值，大值表示流动性好
    
    # ========== 财务因子 ==========
    
    def pb_inverse(self, pb: pd.DataFrame) -> pd.DataFrame:
        """估值因子：PB倒数
        
        Args:
            pb: PB矩阵
            
        Returns:
            PB倒数矩阵（值越高越便宜）
        """
        return 1 / pb.replace(0, np.nan)
    
    def roe_ttm(self, fin_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """质量因子：ROE_TTM
        
        Args:
            fin_data: 财务数据字典
            
        Returns:
            ROE因子矩阵
        """
        return fin_data.get("roe_ttm", pd.DataFrame())
    
    # ========== 规模因子 ==========
    
    def size_mv(self, mv: pd.DataFrame) -> pd.DataFrame:
        """规模因子：对数流通市值
        
        Args:
            mv: 流通市值矩阵
            
        Returns:
            规模因子矩阵（取负值，小市值溢价）
        """
        return -np.log(mv.replace(0, np.nan))
    
    # ========== 数据预处理函数 ==========
    
    def winsorize(self, df: pd.DataFrame, quantiles: tuple = (0.01, 0.99)) -> pd.DataFrame:
        """分位数截断处理
        
        Args:
            df: 输入数据框
            quantiles: 截断分位数 (下限, 上限)
            
        Returns:
            截断后的数据框
        """
        if df.empty:
            return df
            
        # 按行（日期）计算分位数
        lower = df.quantile(quantiles[0], axis=1)
        upper = df.quantile(quantiles[1], axis=1)
        
        # 进行截断
        result = df.copy()
        for date in df.index:
            if date in lower.index and date in upper.index:
                mask = result.loc[date].notna()
                result.loc[date, mask] = result.loc[date, mask].clip(
                    lower=lower[date], upper=upper[date]
                )
        
        return result
    
    def zscore(self, df: pd.DataFrame) -> pd.DataFrame:
        """Z-score标准化
        
        Args:
            df: 输入数据框
            
        Returns:
            标准化后的数据框
        """
        if df.empty:
            return df
            
        # 按行（日期）进行标准化
        mean = df.mean(axis=1)
        std = df.std(axis=1, ddof=0)
        
        # 避免除零
        std = std.replace(0, np.nan)
        
        result = df.sub(mean, axis=0).div(std, axis=0)
        return result
    
    def forward_fill(self, df: pd.DataFrame, max_days: int = 5) -> pd.DataFrame:
        """前向填充缺失值
        
        Args:
            df: 输入数据框
            max_days: 最大填充天数
            
        Returns:
            填充后的数据框
        """
        if df.empty:
            return df
            
        return df.ffill(limit=max_days)
    
    def standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化处理流程：前向填充 -> 分位截断 -> Z-score标准化
        
        Args:
            df: 输入因子矩阵
            
        Returns:
            标准化后的因子矩阵
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        # 1. 前向填充
        if self.preprocessing_config.get('forward_fill', {}).get('enabled', True):
            max_days = self.preprocessing_config.get('forward_fill', {}).get('max_days', 5)
            result = self.forward_fill(result, max_days)
        
        # 2. 分位截断
        if self.preprocessing_config.get('winsorize', {}).get('enabled', True):
            quantiles = self.preprocessing_config.get('winsorize', {}).get('quantiles', [0.01, 0.99])
            result = self.winsorize(result, tuple(quantiles))
        
        # 3. Z-score标准化
        if self.preprocessing_config.get('zscore', {}).get('enabled', True):
            result = self.zscore(result)
        
        return result
    
    def compute_factor(self, factor_name: str, price_data: Dict[str, pd.DataFrame], 
                      fin_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """计算单个因子
        
        Args:
            factor_name: 因子名称
            price_data: 价格数据字典
            fin_data: 财务数据字典
            
        Returns:
            因子矩阵 DataFrame(index=date, columns=ts_code)
        """
        factor_config = self.config['factors'].get(factor_name, {})
        if not factor_config.get('enabled', True):
            return pd.DataFrame()
        
        try:
            # 根据因子名称调用对应的计算函数
            if factor_name == 'mom20':
                window = factor_config.get('window', 20)
                factor_raw = self.mom_20(price_data['close'], window)
                
            elif factor_name == 'shortrev5':
                window = factor_config.get('window', 5)
                factor_raw = self.short_rev_5(price_data['close'], window)
                
            elif factor_name == 'vol20':
                window = factor_config.get('window', 20)
                factor_raw = self.volatility_20(price_data['close'], window)
                
            elif factor_name == 'turn_mean20':
                window = factor_config.get('window', 20)
                factor_raw = self.turnover_mean(
                    price_data['vol'], price_data['amount'], window
                )
                
            elif factor_name == 'amihud20':
                window = factor_config.get('window', 20)
                factor_raw = self.amihud_20(
                    price_data['close'], price_data['amount'], window
                )
                
            elif factor_name == 'inv_pb':
                factor_raw = self.pb_inverse(fin_data['pb'])
                
            elif factor_name == 'roe':
                factor_raw = self.roe_ttm(fin_data)
                
            elif factor_name == 'size':
                factor_raw = self.size_mv(price_data['mv'])
                
            else:
                print(f"未知因子: {factor_name}")
                return pd.DataFrame()
            
            # 标准化处理
            factor_std = self.standardize(factor_raw)
            
            self._log_progress(f"因子 {factor_name} 计算完成，数据形状: {factor_std.shape}")
            return factor_std
            
        except Exception as e:
            print(f"计算因子 {factor_name} 时出错: {e}")
            return pd.DataFrame()
    
    def compute_all_factors(self, price_data: Dict[str, pd.DataFrame], 
                           fin_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """计算所有启用的因子
        
        Args:
            price_data: 价格数据字典
            fin_data: 财务数据字典
            
        Returns:
            所有因子的MultiIndex DataFrame (factor, ts_code)
        """
        factors_dict = {}
        enabled_factors = [name for name, config in self.config['factors'].items() 
                          if config.get('enabled', True)]
        
        self._log_progress(f"开始计算 {len(enabled_factors)} 个因子: {enabled_factors}")
        
        for factor_name in enabled_factors:
            factor_matrix = self.compute_factor(factor_name, price_data, fin_data)
            if not factor_matrix.empty:
                factors_dict[factor_name] = factor_matrix
        
        if not factors_dict:
            self._log_progress("没有成功计算的因子")
            return pd.DataFrame()
        
        # 创建MultiIndex DataFrame
        result_list = []
        for factor_name, factor_matrix in factors_dict.items():
            # 创建MultiIndex columns
            factor_matrix.columns = pd.MultiIndex.from_product(
                [[factor_name], factor_matrix.columns],
                names=['factor', 'ts_code']
            )
            result_list.append(factor_matrix)
        
        # 合并所有因子
        all_factors = pd.concat(result_list, axis=1).sort_index(axis=1)
        
        self._log_progress(f"所有因子计算完成，最终形状: {all_factors.shape}")
        return all_factors
    
    def _validate_result(self, result: pd.DataFrame, name: str):
        """验证计算结果（预留接口）
        
        Args:
            result: 计算结果
            name: 结果名称
        """
        if result.empty:
            print(f"警告: {name} 计算结果为空")
            return False
        
        if result.isna().all().all():
            print(f"警告: {name} 计算结果全为NaN")
            return False
        
        return True
    
    def _log_progress(self, message: str, **kwargs):
        """日志记录接口（预留扩展）"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [FactorEngine] {message}")
