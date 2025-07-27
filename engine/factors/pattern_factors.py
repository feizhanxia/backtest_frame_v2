# -*- coding: utf-8 -*-
"""
K线形态识别因子模块 - 经典K线形态识别
专门处理TA-Lib K线形态函数的数值稳定性问题
"""
import numpy as np
import pandas as pd
import talib
from .base_factor import BaseFactor


class PatternFactors(BaseFactor):
    """K线形态识别因子"""
    
    def __init__(self):
        super().__init__()
    
    def _prepare_ohlc_data(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                          low: pd.DataFrame, close: pd.DataFrame, col: str):
        """预处理OHLC数据，确保数值稳定性
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            col: 股票代码
            
        Returns:
            tuple: (o_vals, h_vals, l_vals, c_vals, common_index) 或 None
        """
        try:
            # 获取数据并处理缺失值
            o_data = open_price[col].ffill().dropna()
            h_data = high[col].ffill().dropna()
            l_data = low[col].ffill().dropna()
            c_data = close[col].ffill().dropna()
            
            # 找到公共索引
            common_index = o_data.index.intersection(h_data.index)\
                                 .intersection(l_data.index)\
                                 .intersection(c_data.index)
            
            if len(common_index) < 10:  # 最少需要10个数据点
                return None
            
            # 转换为numpy数组，确保数据类型
            o_vals = o_data[common_index].values.astype(np.float64)
            h_vals = h_data[common_index].values.astype(np.float64)
            l_vals = l_data[common_index].values.astype(np.float64)
            c_vals = c_data[common_index].values.astype(np.float64)
            
            # 检查并修复数据完整性
            for i in range(len(o_vals)):
                # 确保没有NaN或Inf值
                if not all(np.isfinite([o_vals[i], h_vals[i], l_vals[i], c_vals[i]])):
                    continue
                
                # 确保所有价格都是正数
                if any(val <= 0 for val in [o_vals[i], h_vals[i], l_vals[i], c_vals[i]]):
                    # 用前一个有效值填充
                    if i > 0:
                        o_vals[i] = o_vals[i-1]
                        h_vals[i] = h_vals[i-1]
                        l_vals[i] = l_vals[i-1]
                        c_vals[i] = c_vals[i-1]
                    else:
                        # 如果是第一个值，设置默认值
                        o_vals[i] = h_vals[i] = l_vals[i] = c_vals[i] = 100.0
                
                # 确保OHLC逻辑正确性
                max_oc = max(o_vals[i], c_vals[i])
                min_oc = min(o_vals[i], c_vals[i])
                
                # 高价至少应该等于开盘价和收盘价的最大值
                if h_vals[i] < max_oc:
                    h_vals[i] = max_oc * (1 + abs(np.random.normal(0, 0.001)))
                
                # 低价至多应该等于开盘价和收盘价的最小值
                if l_vals[i] > min_oc:
                    l_vals[i] = min_oc * (1 - abs(np.random.normal(0, 0.001)))
                
                # 添加微小的随机噪声以避免完全相等的情况
                noise_scale = max_oc * 1e-6
                o_vals[i] += np.random.normal(0, noise_scale)
                c_vals[i] += np.random.normal(0, noise_scale)
                
                # 确保价格差异足够大以避免除零
                if abs(h_vals[i] - l_vals[i]) < 1e-8:
                    mid_price = (h_vals[i] + l_vals[i]) / 2
                    h_vals[i] = mid_price * 1.001
                    l_vals[i] = mid_price * 0.999
                
                if abs(o_vals[i] - c_vals[i]) < 1e-8:
                    c_vals[i] = o_vals[i] * (1 + np.random.choice([-1, 1]) * 1e-6)
            
            return o_vals, h_vals, l_vals, c_vals, common_index
            
        except Exception as e:
            print(f"OHLC数据预处理失败 for {col}: {e}")
            return None
    
    def _safe_pattern_calculation(self, pattern_func, o_vals, h_vals, l_vals, c_vals):
        """安全的形态计算函数
        
        Args:
            pattern_func: TA-Lib形态函数
            o_vals, h_vals, l_vals, c_vals: OHLC数据数组
            
        Returns:
            计算结果或None
        """
        try:
            # 最后一次数据验证
            if not all(len(arr) == len(o_vals) for arr in [h_vals, l_vals, c_vals]):
                return None
            
            if len(o_vals) < 3:  # TA-Lib最少需要3个数据点
                return None
            
            # 调用TA-Lib函数
            result = pattern_func(o_vals, h_vals, l_vals, c_vals)
            
            # 检查结果有效性
            if result is None or len(result) == 0:
                return None
            
            # 确保结果是有限数值
            if not all(np.isfinite(result)):
                result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
            
            return result
            
        except Exception as e:
            print(f"Pattern calculation error: {e}")
            return None
    
    def cdl_doji(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                 low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """十字星形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            十字星因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    talib.CDLDOJI, o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_hammer(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                   low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """锤头形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            锤头形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    talib.CDLHAMMER, o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_engulfing(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                      low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """吞没形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            吞没形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    talib.CDLENGULFING, o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_morning_star(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                         low: pd.DataFrame, close: pd.DataFrame, 
                         penetration: float = 0.3) -> pd.DataFrame:
        """启明星形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            penetration: 渗透参数 (默认0.3)
            
        Returns:
            启明星形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    lambda o, h, l, c: talib.CDLMORNINGSTAR(o, h, l, c, penetration),
                    o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_evening_star(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                         low: pd.DataFrame, close: pd.DataFrame,
                         penetration: float = 0.3) -> pd.DataFrame:
        """黄昏星形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            penetration: 渗透参数 (默认0.3)
            
        Returns:
            黄昏星形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    lambda o, h, l, c: talib.CDLEVENINGSTAR(o, h, l, c, penetration),
                    o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_shooting_star(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                          low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """流星形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            流星形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    talib.CDLSHOOTINGSTAR, o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_hanging_man(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                        low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """上吊线形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            上吊线形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    talib.CDLHANGINGMAN, o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_three_black_crows(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                              low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """三只乌鸦形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            三只乌鸦形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    talib.CDL3BLACKCROWS, o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
    
    def cdl_three_white_soldiers(self, open_price: pd.DataFrame, high: pd.DataFrame, 
                                 low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """三个白武士形态
        
        Args:
            open_price: 开盘价矩阵
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            
        Returns:
            三个白武士形态因子矩阵
        """
        if not self.validate_input_data(open_price, high, low, close):
            return pd.DataFrame()
        
        result = pd.DataFrame(index=close.index, columns=close.columns)
        
        for col in close.columns:
            if all(col in df.columns for df in [open_price, high, low]):
                ohlc_data = self._prepare_ohlc_data(open_price, high, low, close, col)
                if ohlc_data is None:
                    continue
                
                o_vals, h_vals, l_vals, c_vals, common_index = ohlc_data
                pattern_result = self._safe_pattern_calculation(
                    talib.CDL3WHITESOLDIERS, o_vals, h_vals, l_vals, c_vals
                )
                
                if pattern_result is not None:
                    result.loc[common_index, col] = pattern_result
        
        return result
