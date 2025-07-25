# -*- coding: utf-8 -*-
"""
因子计算引擎 - 统一因子计算接口
包含所有基础因子的计算逻辑和标准化处理
"""
import numpy as np
import pandas as pd
import talib
from typing import Dict, Optional
import yaml
from pathlib import Path
from datetime import datetime
import warnings

# 抑制 pandas 版本兼容性警告
warnings.filterwarnings('ignore', category=FutureWarning, message='.*fillna.*method.*')
warnings.filterwarnings('ignore', category=FutureWarning, message='.*Downcasting.*')

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
    
    def macd_signal(self, close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD信号线因子
        
        Args:
            close: 收盘价矩阵
            fast: 快线周期
            slow: 慢线周期  
            signal: 信号线周期
            
        Returns:
            MACD信号因子矩阵
        """
        ema_fast = close.ewm(span=fast).mean()
        ema_slow = close.ewm(span=slow).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal).mean()
        macd = 2 * (dif - dea)
        
        return macd
    
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
    
    # ========== Talib 技术指标因子 ==========
    
    def rsi_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """RSI相对强弱指标
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            RSI因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            # 放宽数据量要求，只要有基本的计算窗口即可
            if close[col].notna().sum() >= window:
                try:
                    rsi_values = talib.RSI(close[col].ffill().values, timeperiod=window)
                    result[col] = rsi_values
                except:
                    # 如果计算失败，保持为 NaN
                    continue
        return result
    
    def macd_histogram(self, close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """MACD柱状图因子
        
        Args:
            close: 收盘价矩阵
            fast: 快速EMA周期
            slow: 慢速EMA周期
            signal: 信号线周期
            
        Returns:
            MACD柱状图因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        min_required = max(fast, slow, signal) + 5  # 减少额外的缓冲期要求
        for col in close.columns:
            if close[col].notna().sum() >= min_required:
                try:
                    macd, signal_line, histogram = talib.MACD(
                        close[col].ffill().values, 
                        fastperiod=fast, slowperiod=slow, signalperiod=signal
                    )
                    result[col] = histogram
                except:
                    continue
        return result
    
    def bollinger_position(self, close: pd.DataFrame, window: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """布林带位置因子 (价格在布林带中的相对位置)
        
        Args:
            close: 收盘价矩阵
            window: 计算窗口
            std_dev: 标准差倍数
            
        Returns:
            布林带位置因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:  # 减少额外要求
                try:
                    upper, middle, lower = talib.BBANDS(
                        close[col].ffill().values, 
                        timeperiod=window, nbdevup=std_dev, nbdevdn=std_dev
                    )
                    # 计算价格在布林带中的位置 (0-1之间)
                    bb_position = (close[col].values - lower) / (upper - lower)
                    result[col] = bb_position
                except:
                    continue
        return result
    
    def williams_r(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """威廉指标 Williams %R
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            Williams %R因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (close[col].notna().sum() >= window and 
                col in high.columns and col in low.columns):
                if (high[col].notna().sum() >= window and low[col].notna().sum() >= window):
                    try:
                        result[col] = talib.WILLR(
                            high[col].ffill().values, 
                            low[col].ffill().values, 
                            close[col].ffill().values, 
                            timeperiod=window
                        )
                    except:
                        continue
        return result
    
    def stoch_k(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, 
                k_period: int = 14, d_period: int = 3, smooth_k: int = 3) -> pd.DataFrame:
        """随机指标 KD 中的 K 值
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            k_period: K周期
            d_period: D周期
            smooth_k: K平滑周期
            
        Returns:
            Stoch K因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        min_required = max(k_period, d_period, smooth_k) + 5  # 减少额外要求
        for col in close.columns:
            if (close[col].notna().sum() >= min_required and 
                col in high.columns and col in low.columns):
                if (high[col].notna().sum() >= min_required and low[col].notna().sum() >= min_required):
                    try:
                        k_values, d_values = talib.STOCH(
                            high[col].ffill().values, 
                            low[col].ffill().values, 
                            close[col].ffill().values,
                            fastk_period=k_period, slowk_period=smooth_k, slowd_period=d_period
                        )
                        result[col] = k_values
                    except:
                        continue
        return result
    
    def cci_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """商品通道指标 CCI
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            CCI因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (close[col].notna().sum() >= window + 5 and 
                col in high.columns and col in low.columns):
                if (high[col].notna().sum() >= window + 5 and low[col].notna().sum() >= window + 5):
                    try:
                        result[col] = talib.CCI(
                            high[col].ffill().values, 
                            low[col].ffill().values, 
                            close[col].ffill().values, 
                            timeperiod=window
                        )
                    except:
                        continue
        return result
    
    def adx_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """平均趋向指标 ADX
        
        Args:
            high: 最高价矩阵
            low: 最低价矩阵
            close: 收盘价矩阵
            window: 计算窗口
            
        Returns:
            ADX因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (close[col].notna().sum() > window + 20 and  # ADX需要更多数据
                col in high.columns and col in low.columns):
                if (high[col].notna().sum() >= window + 15 and low[col].notna().sum() >= window + 15):  # 减少ADX的数据要求
                    try:
                        result[col] = talib.ADX(
                            high[col].ffill().values, 
                            low[col].ffill().values, 
                            close[col].ffill().values, 
                            timeperiod=window
                        )
                    except:
                        continue
        return result
    
    def obv_signal(self, close: pd.DataFrame, vol: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """能量潮指标 OBV 的标准化信号
        
        Args:
            close: 收盘价矩阵
            vol: 成交量矩阵
            window: 标准化窗口
            
        Returns:
            OBV信号因子矩阵
        """
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (close[col].notna().sum() > window + 10 and 
                col in vol.columns and vol[col].notna().sum() > window + 10):
                obv_values = talib.OBV(close[col].values, vol[col].values.astype(float))
                # 对OBV进行标准化，计算其相对强度
                obv_series = pd.Series(obv_values, index=close.index)
                result[col] = (obv_series - obv_series.rolling(window).mean()) / obv_series.rolling(window).std()
        return result
    
    # ========== TA-Lib 重叠研究指标 (Overlap Studies) ==========
    
    def sma_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """简单移动平均线"""
        return close.rolling(window).mean()
    
    def ema_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """指数移动平均线"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window:
                try:
                    result[col] = talib.EMA(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def dema_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """双指数移动平均线"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window * 2:  # DEMA需要更多数据
                try:
                    result[col] = talib.DEMA(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def wma_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """加权移动平均线"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window:
                try:
                    result[col] = talib.WMA(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def trima_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """三角移动平均线"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window:
                try:
                    result[col] = talib.TRIMA(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def t3_20(self, close: pd.DataFrame, window: int = 20, vfactor: float = 0.7) -> pd.DataFrame:
        """三重指数移动平均线T3"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window * 3:  # T3需要更多数据
                try:
                    result[col] = talib.T3(close[col].ffill().values, timeperiod=window, vfactor=vfactor)
                except:
                    continue
        return result
    
    def midpoint_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """中点"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window:
                try:
                    result[col] = talib.MIDPOINT(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def midprice_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """中点价格"""
        result = pd.DataFrame(index=high.index, columns=high.columns)
        for col in high.columns:
            if (col in low.columns and
                high[col].notna().sum() >= window and low[col].notna().sum() >= window):
                try:
                    result[col] = talib.MIDPRICE(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def ht_trendline(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换趋势线"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:  # HT需要至少63个数据点
                try:
                    result[col] = talib.HT_TRENDLINE(close[col].ffill().values)
                except:
                    continue
        return result
    
    def tema_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """三重指数移动平均线"""      
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window * 3:  # TEMA 需要更多数据
                try:
                    result[col] = talib.TEMA(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def kama_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """Kaufman 自适应移动平均线"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 10:
                try:
                    result[col] = talib.KAMA(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def sar(self, high: pd.DataFrame, low: pd.DataFrame, acceleration: float = 0.02, maximum: float = 0.2) -> pd.DataFrame:
        """抛物线SAR"""
        result = pd.DataFrame(index=high.index, columns=high.columns)
        for col in high.columns:
            if (high[col].notna().sum() >= 10 and low[col].notna().sum() >= 10 and 
                col in low.columns):
                try:
                    result[col] = talib.SAR(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        acceleration=acceleration, maximum=maximum
                    )
                except:
                    continue
        return result
    
    # ========== TA-Lib 动量指标 (Momentum Indicators) ==========
    
    def apo_12_26(self, close: pd.DataFrame, fast: int = 12, slow: int = 26) -> pd.DataFrame:
        """绝对价格振荡器"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= max(fast, slow) + 5:
                try:
                    result[col] = talib.APO(close[col].ffill().values, 
                                          fastperiod=fast, slowperiod=slow)
                except:
                    continue
        return result
    
    def aroon_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Aroon 指标 - 返回 Aroon Up"""
        result = pd.DataFrame(index=high.index, columns=high.columns)
        for col in high.columns:
            if (high[col].notna().sum() >= window + 5 and low[col].notna().sum() >= window + 5 and 
                col in low.columns):
                try:
                    aroon_up, aroon_down = talib.AROON(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        timeperiod=window
                    )
                    result[col] = aroon_up  # 使用 Aroon Up
                except:
                    continue
        return result
    
    def aroonosc_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Aroon 振荡器"""
        result = pd.DataFrame(index=high.index, columns=high.columns)
        for col in high.columns:
            if (high[col].notna().sum() >= window + 5 and low[col].notna().sum() >= window + 5 and 
                col in low.columns):
                try:
                    result[col] = talib.AROONOSC(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def bop(self, open: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """力量平衡指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in open.columns and col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= 10 for df in [open, high, low, close])):
                try:
                    result[col] = talib.BOP(
                        open[col].ffill().values,
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values
                    )
                except:
                    continue
        return result
    
    def cmo_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """Chande动量振荡器"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.CMO(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def dx_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """方向性运动指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= window + 10 for df in [high, low, close])):
                try:
                    result[col] = talib.DX(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def mfi_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, 
               vol: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """资金流量指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and col in vol.columns and
                all(df[col].notna().sum() >= window + 5 for df in [high, low, close, vol])):
                try:
                    result[col] = talib.MFI(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        vol[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def mom_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """动量指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.MOM(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def ppo_12_26(self, close: pd.DataFrame, fast: int = 12, slow: int = 26) -> pd.DataFrame:
        """价格振荡器百分比"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= max(fast, slow) + 5:
                try:
                    result[col] = talib.PPO(close[col].ffill().values, 
                                          fastperiod=fast, slowperiod=slow)
                except:
                    continue
        return result
    
    def roc_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.ROC(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def stochf_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, 
                  k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
        """快速随机指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= max(k_period, d_period) + 5 for df in [high, low, close])):
                try:
                    k_values, d_values = talib.STOCHF(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        fastk_period=k_period, fastd_period=d_period
                    )
                    result[col] = k_values
                except:
                    continue
        return result
    
    def trix_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """TRIX 指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window * 3:  # TRIX 需要更多数据
                try:
                    result[col] = talib.TRIX(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def ultosc_7_14_28(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame,
                       period1: int = 7, period2: int = 14, period3: int = 28) -> pd.DataFrame:
        """终极振荡器"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= max(period1, period2, period3) + 10 for df in [high, low, close])):
                try:
                    result[col] = talib.ULTOSC(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        timeperiod1=period1, timeperiod2=period2, timeperiod3=period3
                    )
                except:
                    continue
        return result
    
    def adxr_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """ADX评级"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= window + 20 for df in [high, low, close])):
                try:
                    result[col] = talib.ADXR(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def macdext_12_26_9(self, close: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """可控MA类型的MACD"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= max(fast, slow, signal) + 10:
                try:
                    macd, signal_line, histogram = talib.MACDEXT(
                        close[col].ffill().values,
                        fastperiod=fast, fastmatype=0, slowperiod=slow, slowmatype=0,
                        signalperiod=signal, signalmatype=0
                    )
                    result[col] = histogram  # 使用柱状图
                except:
                    continue
        return result
    
    def macdfix_9(self, close: pd.DataFrame, signal: int = 9) -> pd.DataFrame:
        """MACD固定12/26"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 26 + signal:
                try:
                    macd, signal_line, histogram = talib.MACDFIX(
                        close[col].ffill().values, signalperiod=signal
                    )
                    result[col] = histogram
                except:
                    continue
        return result
    
    def minus_di_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """负向指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= window + 15 for df in [high, low, close])):
                try:
                    result[col] = talib.MINUS_DI(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def minus_dm_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """负向运动"""
        result = pd.DataFrame(index=high.index, columns=high.columns)
        for col in high.columns:
            if (col in low.columns and
                high[col].notna().sum() >= window + 10 and low[col].notna().sum() >= window + 10):
                try:
                    result[col] = talib.MINUS_DM(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def plus_di_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """正向指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= window + 15 for df in [high, low, close])):
                try:
                    result[col] = talib.PLUS_DI(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def plus_dm_14(self, high: pd.DataFrame, low: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """正向运动"""
        result = pd.DataFrame(index=high.index, columns=high.columns)
        for col in high.columns:
            if (col in low.columns and
                high[col].notna().sum() >= window + 10 and low[col].notna().sum() >= window + 10):
                try:
                    result[col] = talib.PLUS_DM(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def rocp_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率百分比"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.ROCP(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def rocr_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率比率"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.ROCR(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def rocr100_10(self, close: pd.DataFrame, window: int = 10) -> pd.DataFrame:
        """变化率比率100倍"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.ROCR100(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def stochrsi_14(self, close: pd.DataFrame, window: int = 14, fastk: int = 5, fastd: int = 3) -> pd.DataFrame:
        """随机RSI"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + max(fastk, fastd) + 10:
                try:
                    fastk_values, fastd_values = talib.STOCHRSI(
                        close[col].ffill().values,
                        timeperiod=window, fastk_period=fastk, fastd_period=fastd
                    )
                    result[col] = fastk_values  # 使用FastK
                except:
                    continue
        return result
    
    # ========== TA-Lib 成交量指标 (Volume Indicators) ==========
    
    def ad_line(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
        """累积/派发线"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and col in vol.columns and
                all(df[col].notna().sum() >= 20 for df in [high, low, close, vol])):
                try:
                    result[col] = talib.AD(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        vol[col].ffill().values
                    )
                except:
                    continue
        return result
    
    def adosc_3_10(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, vol: pd.DataFrame,
                   fast: int = 3, slow: int = 10) -> pd.DataFrame:
        """累积/派发振荡器"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and col in vol.columns and
                all(df[col].notna().sum() >= max(fast, slow) + 10 for df in [high, low, close, vol])):
                try:
                    result[col] = talib.ADOSC(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        vol[col].ffill().values,
                        fastperiod=fast, slowperiod=slow
                    )
                except:
                    continue
        return result
    
    def obv_line(self, close: pd.DataFrame, vol: pd.DataFrame) -> pd.DataFrame:
        """净成交量指标"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in vol.columns and
                close[col].notna().sum() >= 20 and vol[col].notna().sum() >= 20):
                try:
                    result[col] = talib.OBV(close[col].values, vol[col].values.astype(float))
                except:
                    continue
        return result

    # ========== TA-Lib 周期指标 (Cycle Indicators) - 全新类别 ==========
    
    def ht_dcperiod(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换 - 主导周期"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:  # 希尔伯特变换需要至少63个数据点
                try:
                    result[col] = talib.HT_DCPERIOD(close[col].ffill().values)
                except:
                    continue
        return result
    
    def ht_dcphase(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换 - 主导周期相位"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:
                try:
                    result[col] = talib.HT_DCPHASE(close[col].ffill().values)
                except:
                    continue
        return result
    
    def ht_phasor_inphase(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换 - 相位分量 (同相)"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:
                try:
                    inphase, quadrature = talib.HT_PHASOR(close[col].ffill().values)
                    result[col] = inphase  # 使用同相分量
                except:
                    continue
        return result
    
    def ht_phasor_quadrature(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换 - 相位分量 (正交)"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:
                try:
                    inphase, quadrature = talib.HT_PHASOR(close[col].ffill().values)
                    result[col] = quadrature  # 使用正交分量 
                except:
                    continue
        return result
    
    def ht_sine(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换 - 正弦波"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:
                try:
                    sine, leadsine = talib.HT_SINE(close[col].ffill().values)
                    result[col] = sine  # 使用正弦波
                except:
                    continue
        return result
    
    def ht_leadsine(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换 - 领先正弦波"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:
                try:
                    sine, leadsine = talib.HT_SINE(close[col].ffill().values)
                    result[col] = leadsine  # 使用领先正弦波
                except:
                    continue
        return result
    
    def ht_trendmode(self, close: pd.DataFrame) -> pd.DataFrame:
        """希尔伯特变换 - 趋势vs周期模式"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= 63:
                try:
                    result[col] = talib.HT_TRENDMODE(close[col].ffill().values)
                except:
                    continue
        return result
    
    # ========== TA-Lib 波动率指标 (Volatility Indicators) ==========
    
    def atr_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """平均真实波幅"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= window + 5 for df in [high, low, close])):
                try:
                    result[col] = talib.ATR(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def natr_14(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """标准化平均真实波幅"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= window + 5 for df in [high, low, close])):
                try:
                    result[col] = talib.NATR(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def trange(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """真实波幅"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= 10 for df in [high, low, close])):
                try:
                    result[col] = talib.TRANGE(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values
                    )
                except:
                    continue
        return result
    
    # ========== TA-Lib 价格变换指标 (Price Transform) ==========
    
    def avgprice(self, open: pd.DataFrame, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """平均价格"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in open.columns and col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= 10 for df in [open, high, low, close])):
                try:
                    result[col] = talib.AVGPRICE(
                        open[col].ffill().values,
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values
                    )
                except:
                    continue
        return result
    
    def medprice(self, high: pd.DataFrame, low: pd.DataFrame) -> pd.DataFrame:
        """中位价格"""
        result = pd.DataFrame(index=high.index, columns=high.columns)
        for col in high.columns:
            if (col in low.columns and
                high[col].notna().sum() >= 5 and low[col].notna().sum() >= 5):
                try:
                    result[col] = talib.MEDPRICE(
                        high[col].ffill().values,
                        low[col].ffill().values
                    )
                except:
                    continue
        return result
    
    def typprice(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """典型价格"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= 5 for df in [high, low, close])):
                try:
                    result[col] = talib.TYPPRICE(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values
                    )
                except:
                    continue
        return result
    
    def wclprice(self, high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
        """加权收盘价格"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if (col in high.columns and col in low.columns and
                all(df[col].notna().sum() >= 5 for df in [high, low, close])):
                try:
                    result[col] = talib.WCLPRICE(
                        high[col].ffill().values,
                        low[col].ffill().values,
                        close[col].ffill().values
                    )
                except:
                    continue
        return result
    
    # ========== TA-Lib 统计函数 (Statistic Functions) ==========
    
    def beta_5(self, close: pd.DataFrame, benchmark_close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Beta系数 (需要基准价格)"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        # 简化版本：使用市场平均作为基准
        market_avg = close.mean(axis=1)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.BETA(
                        close[col].ffill().values,
                        market_avg.ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def correl_5(self, close: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """皮尔逊相关系数 (与市场平均的相关性)"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        market_avg = close.mean(axis=1)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.CORREL(
                        close[col].ffill().values,
                        market_avg.ffill().values,
                        timeperiod=window
                    )
                except:
                    continue
        return result
    
    def linearreg_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """线性回归"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.LINEARREG(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def stddev_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """标准差"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window:
                try:
                    result[col] = talib.STDDEV(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def tsf_14(self, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """时间序列预测"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window + 5:
                try:
                    result[col] = talib.TSF(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result
    
    def var_20(self, close: pd.DataFrame, window: int = 20) -> pd.DataFrame:
        """方差"""
        result = pd.DataFrame(index=close.index, columns=close.columns)
        for col in close.columns:
            if close[col].notna().sum() >= window:
                try:
                    result[col] = talib.VAR(close[col].ffill().values, timeperiod=window)
                except:
                    continue
        return result

    # ========== 财务因子 ==========
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
                      fin_data: Dict[str, pd.DataFrame] = None) -> pd.DataFrame:
        """计算单个因子 (适配ETF/指数，不再需要财务数据)
        
        Args:
            factor_name: 因子名称
            price_data: 价格数据字典
            fin_data: 财务数据字典 (ETF/指数不使用，保留兼容性)
            
        Returns:
            因子矩阵 DataFrame(index=date, columns=ts_code)
        """
        factor_config = self.config['factors'].get(factor_name, {})
        if not factor_config.get('enabled', True):
            return pd.DataFrame()
        
        try:
            # 根据因子名称调用对应的计算函数 - 只保留技术类因子
            if factor_name == 'mom20':
                window = factor_config.get('window', 20)
                factor_raw = self.mom_20(price_data['close'], window)
                
            elif factor_name == 'shortrev5':
                window = factor_config.get('window', 5)
                factor_raw = self.short_rev_5(price_data['close'], window)
                
            elif factor_name == 'vol20':
                window = factor_config.get('window', 20)
                factor_raw = self.volatility_20(price_data['close'], window)
                
            elif factor_name == 'macd_signal':
                fast = factor_config.get('fast', 12)
                slow = factor_config.get('slow', 26)
                signal = factor_config.get('signal', 9)
                factor_raw = self.macd_signal(price_data['close'], fast, slow, signal)
                
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
                
            # ========== Talib 技术指标因子 ==========
            elif factor_name == 'rsi14':
                window = factor_config.get('window', 14)
                factor_raw = self.rsi_14(price_data['close'], window)
                
            elif factor_name == 'macd_histogram':
                fast = factor_config.get('fast', 12)
                slow = factor_config.get('slow', 26)
                signal = factor_config.get('signal', 9)
                factor_raw = self.macd_histogram(price_data['close'], fast, slow, signal)
                
            elif factor_name == 'bollinger_position':
                window = factor_config.get('window', 20)
                std_dev = factor_config.get('std_dev', 2.0)
                factor_raw = self.bollinger_position(price_data['close'], window, std_dev)
                
            elif factor_name == 'williams_r':
                window = factor_config.get('window', 14)
                factor_raw = self.williams_r(
                    price_data['high'], price_data['low'], price_data['close'], window
                )
                
            elif factor_name == 'stoch_k':
                k_period = factor_config.get('k_period', 14)
                d_period = factor_config.get('d_period', 3)
                smooth_k = factor_config.get('smooth_k', 3)
                factor_raw = self.stoch_k(
                    price_data['high'], price_data['low'], price_data['close'], 
                    k_period, d_period, smooth_k
                )
                
            elif factor_name == 'cci14':
                window = factor_config.get('window', 14)
                factor_raw = self.cci_14(
                    price_data['high'], price_data['low'], price_data['close'], window
                )
                
            elif factor_name == 'adx14':
                window = factor_config.get('window', 14)
                factor_raw = self.adx_14(
                    price_data['high'], price_data['low'], price_data['close'], window
                )
                
            elif factor_name == 'obv_signal':
                window = factor_config.get('window', 20)
                factor_raw = self.obv_signal(price_data['close'], price_data['vol'], window)
                
            # ========== TA-Lib 重叠研究指标 ==========
            elif factor_name == 'sma20':
                window = factor_config.get('window', 20)
                factor_raw = self.sma_20(price_data['close'], window)
                
            elif factor_name == 'ema20':
                window = factor_config.get('window', 20)
                factor_raw = self.ema_20(price_data['close'], window)
                
            elif factor_name == 'tema20':
                window = factor_config.get('window', 20)
                factor_raw = self.tema_20(price_data['close'], window)
                
            elif factor_name == 'kama20':
                window = factor_config.get('window', 20)
                factor_raw = self.kama_20(price_data['close'], window)
                
            elif factor_name == 'sar':
                acceleration = factor_config.get('acceleration', 0.02)
                maximum = factor_config.get('maximum', 0.2)
                factor_raw = self.sar(price_data['high'], price_data['low'], acceleration, maximum)
                
            # ========== TA-Lib 动量指标 ==========
            elif factor_name == 'apo_12_26':
                fast = factor_config.get('fast', 12)
                slow = factor_config.get('slow', 26)
                factor_raw = self.apo_12_26(price_data['close'], fast, slow)
                
            elif factor_name == 'aroon14':
                window = factor_config.get('window', 14)
                factor_raw = self.aroon_14(price_data['high'], price_data['low'], window)
                
            elif factor_name == 'aroonosc14':
                window = factor_config.get('window', 14)
                factor_raw = self.aroonosc_14(price_data['high'], price_data['low'], window)
                
            elif factor_name == 'bop':
                factor_raw = self.bop(price_data['open'], price_data['high'], 
                                     price_data['low'], price_data['close'])
                
            elif factor_name == 'cmo14':
                window = factor_config.get('window', 14)
                factor_raw = self.cmo_14(price_data['close'], window)
                
            elif factor_name == 'dx14':
                window = factor_config.get('window', 14)
                factor_raw = self.dx_14(price_data['high'], price_data['low'], 
                                       price_data['close'], window)
                
            elif factor_name == 'mfi14':
                window = factor_config.get('window', 14)
                factor_raw = self.mfi_14(price_data['high'], price_data['low'], 
                                        price_data['close'], price_data['vol'], window)
                
            elif factor_name == 'mom10':
                window = factor_config.get('window', 10)
                factor_raw = self.mom_10(price_data['close'], window)
                
            elif factor_name == 'ppo_12_26':
                fast = factor_config.get('fast', 12)
                slow = factor_config.get('slow', 26)
                factor_raw = self.ppo_12_26(price_data['close'], fast, slow)
                
            elif factor_name == 'roc10':
                window = factor_config.get('window', 10)
                factor_raw = self.roc_10(price_data['close'], window)
                
            elif factor_name == 'stochf14':
                k_period = factor_config.get('k_period', 14)
                d_period = factor_config.get('d_period', 3)
                factor_raw = self.stochf_14(price_data['high'], price_data['low'], 
                                           price_data['close'], k_period, d_period)
                
            elif factor_name == 'trix14':
                window = factor_config.get('window', 14)
                factor_raw = self.trix_14(price_data['close'], window)
                
            elif factor_name == 'ultosc':
                period1 = factor_config.get('period1', 7)
                period2 = factor_config.get('period2', 14)
                period3 = factor_config.get('period3', 28)
                factor_raw = self.ultosc_7_14_28(price_data['high'], price_data['low'], 
                                                price_data['close'], period1, period2, period3)
                
            # ========== TA-Lib 成交量指标 ==========
            elif factor_name == 'ad_line':
                factor_raw = self.ad_line(price_data['high'], price_data['low'], 
                                         price_data['close'], price_data['vol'])
                
            elif factor_name == 'adosc':
                fast = factor_config.get('fast', 3)
                slow = factor_config.get('slow', 10)
                factor_raw = self.adosc_3_10(price_data['high'], price_data['low'], 
                                            price_data['close'], price_data['vol'], fast, slow)
                
            # ========== TA-Lib 波动率指标 ==========
            elif factor_name == 'atr14':
                window = factor_config.get('window', 14)
                factor_raw = self.atr_14(price_data['high'], price_data['low'], 
                                        price_data['close'], window)
                
            elif factor_name == 'natr14':
                window = factor_config.get('window', 14)
                factor_raw = self.natr_14(price_data['high'], price_data['low'], 
                                         price_data['close'], window)
                
            elif factor_name == 'trange':
                factor_raw = self.trange(price_data['high'], price_data['low'], 
                                        price_data['close'])
                
            # ========== TA-Lib 价格变换指标 ==========
            elif factor_name == 'avgprice':
                factor_raw = self.avgprice(price_data['open'], price_data['high'], 
                                          price_data['low'], price_data['close'])
                
            elif factor_name == 'medprice':
                factor_raw = self.medprice(price_data['high'], price_data['low'])
                
            elif factor_name == 'typprice':
                factor_raw = self.typprice(price_data['high'], price_data['low'], 
                                          price_data['close'])
                
            elif factor_name == 'wclprice':
                factor_raw = self.wclprice(price_data['high'], price_data['low'], 
                                          price_data['close'])
                
            # ========== TA-Lib 统计函数 ==========
            elif factor_name == 'beta5':
                window = factor_config.get('window', 5)
                # 需要传入基准，这里简化处理
                factor_raw = self.beta_5(price_data['close'], price_data['close'], window)
                
            elif factor_name == 'correl5':
                window = factor_config.get('window', 5)
                factor_raw = self.correl_5(price_data['close'], window)
                
            elif factor_name == 'linearreg14':
                window = factor_config.get('window', 14)
                factor_raw = self.linearreg_14(price_data['close'], window)
                
            elif factor_name == 'stddev20':
                window = factor_config.get('window', 20)
                factor_raw = self.stddev_20(price_data['close'], window)
                
            elif factor_name == 'tsf14':
                window = factor_config.get('window', 14)
                factor_raw = self.tsf_14(price_data['close'], window)
                
            elif factor_name == 'var20':
                window = factor_config.get('window', 20)
                factor_raw = self.var_20(price_data['close'], window)
                
            # ========== 新增的重叠研究指标 ==========
            elif factor_name == 'dema20':
                window = factor_config.get('window', 20)
                factor_raw = self.dema_20(price_data['close'], window)
                
            elif factor_name == 'wma20':
                window = factor_config.get('window', 20)
                factor_raw = self.wma_20(price_data['close'], window)
                
            elif factor_name == 'trima20':
                window = factor_config.get('window', 20)
                factor_raw = self.trima_20(price_data['close'], window)
                
            elif factor_name == 't3_20':
                window = factor_config.get('window', 20)
                vfactor = factor_config.get('vfactor', 0.7)
                factor_raw = self.t3_20(price_data['close'], window, vfactor)
                
            elif factor_name == 'midpoint14':
                window = factor_config.get('window', 14)
                factor_raw = self.midpoint_14(price_data['close'], window)
                
            elif factor_name == 'midprice14':
                window = factor_config.get('window', 14)
                factor_raw = self.midprice_14(price_data['high'], price_data['low'], window)
                
            elif factor_name == 'ht_trendline':
                factor_raw = self.ht_trendline(price_data['close'])
                
            # ========== 新增的动量指标 ==========
            elif factor_name == 'adxr14':
                window = factor_config.get('window', 14)
                factor_raw = self.adxr_14(price_data['high'], price_data['low'], price_data['close'], window)
                
            elif factor_name == 'macdext_12_26_9':
                fast = factor_config.get('fast', 12)
                slow = factor_config.get('slow', 26)
                signal = factor_config.get('signal', 9)
                factor_raw = self.macdext_12_26_9(price_data['close'], fast, slow, signal)
                
            elif factor_name == 'macdfix9':
                signal = factor_config.get('signal', 9)
                factor_raw = self.macdfix_9(price_data['close'], signal)
                
            elif factor_name == 'minus_di14':
                window = factor_config.get('window', 14)
                factor_raw = self.minus_di_14(price_data['high'], price_data['low'], price_data['close'], window)
                
            elif factor_name == 'minus_dm14':
                window = factor_config.get('window', 14)
                factor_raw = self.minus_dm_14(price_data['high'], price_data['low'], window)
                
            elif factor_name == 'plus_di14':
                window = factor_config.get('window', 14)
                factor_raw = self.plus_di_14(price_data['high'], price_data['low'], price_data['close'], window)
                
            elif factor_name == 'plus_dm14':
                window = factor_config.get('window', 14)
                factor_raw = self.plus_dm_14(price_data['high'], price_data['low'], window)
                
            elif factor_name == 'rocp10':
                window = factor_config.get('window', 10)
                factor_raw = self.rocp_10(price_data['close'], window)
                
            elif factor_name == 'rocr10':
                window = factor_config.get('window', 10)
                factor_raw = self.rocr_10(price_data['close'], window)
                
            elif factor_name == 'rocr100_10':
                window = factor_config.get('window', 10)
                factor_raw = self.rocr100_10(price_data['close'], window)
                
            elif factor_name == 'stochrsi14':
                window = factor_config.get('window', 14)
                fastk = factor_config.get('fastk', 5)
                fastd = factor_config.get('fastd', 3)
                factor_raw = self.stochrsi_14(price_data['close'], window, fastk, fastd)
                
            # ========== 新增的成交量指标 ==========
            elif factor_name == 'obv_line':
                factor_raw = self.obv_line(price_data['close'], price_data['vol'])
                
            # ========== 新增的周期指标 ==========
            elif factor_name == 'ht_dcperiod':
                factor_raw = self.ht_dcperiod(price_data['close'])
                
            elif factor_name == 'ht_dcphase':
                factor_raw = self.ht_dcphase(price_data['close'])
                
            elif factor_name == 'ht_phasor_inphase':
                factor_raw = self.ht_phasor_inphase(price_data['close'])
                
            elif factor_name == 'ht_phasor_quadrature':
                factor_raw = self.ht_phasor_quadrature(price_data['close'])
                
            elif factor_name == 'ht_sine':
                factor_raw = self.ht_sine(price_data['close'])
                
            elif factor_name == 'ht_leadsine':
                factor_raw = self.ht_leadsine(price_data['close'])
                
            elif factor_name == 'ht_trendmode':
                factor_raw = self.ht_trendmode(price_data['close'])
                
            # 删除财务相关因子:
            # elif factor_name == 'inv_pb': (已删除)
            # elif factor_name == 'roe': (已删除)
            # elif factor_name == 'size': (已删除)
                
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
                           fin_data: Dict[str, pd.DataFrame] = None) -> pd.DataFrame:
        """计算所有启用的因子 (适配ETF/指数，财务数据可选)
        
        Args:
            price_data: 价格数据字典
            fin_data: 财务数据字典 (ETF/指数不使用，保留兼容性)
            
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
