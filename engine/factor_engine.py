# -*- coding: utf-8 -*-
"""
精简版因子计算引擎 - 模块化重构版本
通过继承各个因子类别实现功能分离
"""
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict
import warnings

# 导入各个因子模块
from .factors.base_factor import BaseFactor
from .factors.price_factors import PriceFactors
from .factors.overlap_factors import OverlapFactors  
from .factors.momentum_factors import MomentumFactors
from .factors.volume_factors import VolumeFactors
from .factors.technical_factors import TechnicalFactors
from .factors.pattern_factors import PatternFactors
from .factors.math_factors import MathFactors

# 抑制 pandas 版本兼容性警告
warnings.filterwarnings('ignore', category=FutureWarning, message='.*fillna.*method.*')
warnings.filterwarnings('ignore', category=FutureWarning, message='.*Downcasting.*')

class FactorEngine(PriceFactors, OverlapFactors, MomentumFactors, VolumeFactors, TechnicalFactors, PatternFactors, MathFactors):
    """
    模块化因子计算引擎
    通过多重继承整合各个因子类别
    """
    
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
                
            # ========== 新增的成交量指标 ==========
            elif factor_name == 'obv_line':
                factor_raw = self.obv_line(price_data['close'], price_data['vol'])
                
            # ========== 新增的重叠研究指标 ==========
            elif factor_name == 'bbands_upper':
                window = factor_config.get('window', 20)
                std_dev = factor_config.get('std_dev', 2.0)
                factor_raw = self.bbands_upper(price_data['close'], window, std_dev)
                
            elif factor_name == 'bbands_lower':
                window = factor_config.get('window', 20)
                std_dev = factor_config.get('std_dev', 2.0)
                factor_raw = self.bbands_lower(price_data['close'], window, std_dev)
                
            elif factor_name == 'mama_adaptive':
                fastlimit = factor_config.get('fastlimit', 0.5)
                slowlimit = factor_config.get('slowlimit', 0.05)
                factor_raw = self.mama_adaptive(price_data['close'], fastlimit, slowlimit)
                
            elif factor_name == 'fama_adaptive':
                fastlimit = factor_config.get('fastlimit', 0.5)
                slowlimit = factor_config.get('slowlimit', 0.05)
                factor_raw = self.fama_adaptive(price_data['close'], fastlimit, slowlimit)
                
            elif factor_name == 'sarext_extended':
                start_value = factor_config.get('start_value', 0.0)
                acceleration = factor_config.get('acceleration', 0.02)
                maximum = factor_config.get('maximum', 0.2)
                factor_raw = self.sarext_extended(price_data['high'], price_data['low'], 
                                                start_value, acceleration, maximum)
                
            elif factor_name == 'ma_sma':
                window = factor_config.get('window', 20)
                ma_type = factor_config.get('ma_type', 0)
                factor_raw = self.ma_controllable(price_data['close'], window, ma_type)
                
            elif factor_name == 'ma_ema':
                window = factor_config.get('window', 20)
                ma_type = factor_config.get('ma_type', 1)
                factor_raw = self.ma_controllable(price_data['close'], window, ma_type)
                
            elif factor_name == 'ma_wma':
                window = factor_config.get('window', 20)
                ma_type = factor_config.get('ma_type', 2)
                factor_raw = self.ma_controllable(price_data['close'], window, ma_type)
                
            # ========== 新增的统计函数 ==========
            elif factor_name == 'linearreg_angle':
                window = factor_config.get('window', 14)
                factor_raw = self.linearreg_angle(price_data['close'], window)
                
            elif factor_name == 'linearreg_intercept':
                window = factor_config.get('window', 14)
                factor_raw = self.linearreg_intercept(price_data['close'], window)
                
            elif factor_name == 'linearreg_slope':
                window = factor_config.get('window', 14)
                factor_raw = self.linearreg_slope(price_data['close'], window)
                
            # ========== K线形态识别指标 ==========
            elif factor_name == 'cdl_doji':
                factor_raw = self.cdl_doji(price_data['open'], price_data['high'], 
                                         price_data['low'], price_data['close'])
                
            elif factor_name == 'cdl_hammer':
                factor_raw = self.cdl_hammer(price_data['open'], price_data['high'], 
                                           price_data['low'], price_data['close'])
                
            elif factor_name == 'cdl_engulfing':
                factor_raw = self.cdl_engulfing(price_data['open'], price_data['high'], 
                                              price_data['low'], price_data['close'])
                
            elif factor_name == 'cdl_morning_star':
                penetration = factor_config.get('penetration', 0.3)
                factor_raw = self.cdl_morning_star(price_data['open'], price_data['high'], 
                                                 price_data['low'], price_data['close'], penetration)
                
            elif factor_name == 'cdl_evening_star':
                penetration = factor_config.get('penetration', 0.3)
                factor_raw = self.cdl_evening_star(price_data['open'], price_data['high'], 
                                                 price_data['low'], price_data['close'], penetration)
                
            elif factor_name == 'cdl_shooting_star':
                factor_raw = self.cdl_shooting_star(price_data['open'], price_data['high'], 
                                                  price_data['low'], price_data['close'])
                
            elif factor_name == 'cdl_hanging_man':
                factor_raw = self.cdl_hanging_man(price_data['open'], price_data['high'], 
                                                price_data['low'], price_data['close'])
                
            elif factor_name == 'cdl_three_black_crows':
                factor_raw = self.cdl_three_black_crows(price_data['open'], price_data['high'], 
                                                      price_data['low'], price_data['close'])
                
            elif factor_name == 'cdl_three_white_soldiers':
                factor_raw = self.cdl_three_white_soldiers(price_data['open'], price_data['high'], 
                                                         price_data['low'], price_data['close'])
                
            # ========== 数学变换指标 ==========
            elif factor_name == 'ln_transform':
                factor_raw = self.ln_transform(price_data['close'])
                
            elif factor_name == 'sqrt_transform':
                factor_raw = self.sqrt_transform(price_data['close'])
                
            elif factor_name == 'tanh_transform':
                factor_raw = self.tanh_transform(price_data['close'])
                
            elif factor_name == 'max_value_30':
                window = factor_config.get('window', 30)
                factor_raw = self.max_value(price_data['close'], window)
                
            elif factor_name == 'min_value_30':
                window = factor_config.get('window', 30)
                factor_raw = self.min_value(price_data['close'], window)
                
            elif factor_name == 'sum_value_30':
                window = factor_config.get('window', 30)
                factor_raw = self.sum_value(price_data['close'], window)
                
            elif factor_name == 'minmax_range':
                window = factor_config.get('window', 30)
                factor_raw = self.minmax_range(price_data['close'], window)
                
            # ========== 新增的慢速随机指标 ==========
            elif factor_name == 'stoch_slow_k':
                fastk_period = factor_config.get('fastk_period', 5)
                slowk_period = factor_config.get('slowk_period', 3)
                slowd_period = factor_config.get('slowd_period', 3)
                factor_raw = self.stoch_slow_k(price_data['high'], price_data['low'], 
                                             price_data['close'], fastk_period, slowk_period, slowd_period)
                
            elif factor_name == 'stoch_slow_d':
                fastk_period = factor_config.get('fastk_period', 5)
                slowk_period = factor_config.get('slowk_period', 3)
                slowd_period = factor_config.get('slowd_period', 3)
                factor_raw = self.stoch_slow_d(price_data['high'], price_data['low'], 
                                             price_data['close'], fastk_period, slowk_period, slowd_period)
                
            # ========== 新增的三角函数变换 ==========
            elif factor_name == 'acos_transform':
                factor_raw = self.acos_transform(price_data['close'])
                
            elif factor_name == 'asin_transform':
                factor_raw = self.asin_transform(price_data['close'])
                
            elif factor_name == 'atan_transform':
                factor_raw = self.atan_transform(price_data['close'])
                
            elif factor_name == 'cosh_transform':
                factor_raw = self.cosh_transform(price_data['close'])
                
            elif factor_name == 'sinh_transform':
                factor_raw = self.sinh_transform(price_data['close'])
                
            elif factor_name == 'tan_transform':
                factor_raw = self.tan_transform(price_data['close'])
                
            # ========== 周期指标已删除 ==========
            # 希尔伯特变换因子存在计算问题，已暂时移除
                
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
            factor_result = self.compute_factor(factor_name, price_data, fin_data)
            if not factor_result.empty:
                factors_dict[factor_name] = factor_result
        
        if not factors_dict:
            print("没有成功计算的因子")
            return pd.DataFrame()
        
        # 创建MultiIndex DataFrame
        result_list = []
        for factor_name, factor_matrix in factors_dict.items():
            factor_stacked = factor_matrix.stack()
            factor_stacked.name = factor_name
            result_list.append(factor_stacked.to_frame().T)
        
        # 合并所有因子
        all_factors = pd.concat(result_list, axis=0).sort_index(axis=0)
        
        self._log_progress(f"所有因子计算完成，最终形状: {all_factors.shape}")
        return all_factors
    
    def _validate_result(self, result: pd.DataFrame, name: str):
        """验证计算结果（预留接口）"""
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
