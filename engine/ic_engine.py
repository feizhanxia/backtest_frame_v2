# -*- coding: utf-8 -*-
"""
IC计算引擎 - 因子有效性分析
计算因子与未来收益的相关性，评估因子预测能力
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.stats import spearmanr, pearsonr
import yaml
from pathlib import Path
from datetime import datetime

class ICEngine:
    """IC计算引擎"""
    
    def __init__(self, config_path: str = "config/factors.yml"):
        """初始化IC引擎
        
        Args:
            config_path: 配置文件路径
        """
        self.base_path = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.ic_config = self.config.get('ic', {})
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = self.base_path / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def calc_ic_timeseries(self, factor_df: pd.DataFrame, ret_df: pd.DataFrame, 
                          method: str = 'spearman') -> pd.Series:
        """计算IC时间序列
        
        Args:
            factor_df: 因子矩阵 DataFrame(index=date, columns=ts_code)
            ret_df: 收益率矩阵 DataFrame(index=date, columns=ts_code)
            method: 相关性计算方法 ('spearman' 或 'pearson')
            
        Returns:
            IC时间序列 Series(index=date)
        """
        if factor_df.empty or ret_df.empty:
            return pd.Series()
        
        # 对齐日期索引
        common_dates = factor_df.index.intersection(ret_df.index)
        if len(common_dates) == 0:
            self._log_progress("因子数据与收益率数据没有重叠日期")
            return pd.Series()
        
        factor_aligned = factor_df.reindex(common_dates)
        ret_aligned = ret_df.reindex(common_dates)
        
        ic_list = []
        min_samples = self.ic_config.get('min_samples', 30)
        
        for date in common_dates:
            try:
                # 获取当日数据
                factor_values = factor_aligned.loc[date].values
                ret_values = ret_aligned.loc[date].values
                
                # 过滤缺失值
                mask = ~pd.isna(factor_values) & ~pd.isna(ret_values)
                
                if mask.sum() < min_samples:
                    ic_list.append(np.nan)
                    continue
                
                factor_clean = factor_values[mask]
                ret_clean = ret_values[mask]
                
                # 计算相关系数
                if method.lower() == 'spearman':
                    ic_value, _ = spearmanr(factor_clean, ret_clean)
                elif method.lower() == 'pearson':
                    ic_value, _ = pearsonr(factor_clean, ret_clean)
                else:
                    raise ValueError(f"不支持的相关性方法: {method}")
                
                ic_list.append(ic_value)
                
            except Exception as e:
                print(f"计算日期 {date} 的IC时出错: {e}")
                ic_list.append(np.nan)
        
        ic_series = pd.Series(ic_list, index=common_dates)
        return ic_series
    
    def calc_ic_summary(self, ic_series: pd.Series, window: int = None) -> Dict[str, float]:
        """计算IC统计摘要
        
        Args:
            ic_series: IC时间序列
            window: 滚动窗口大小，None表示使用全样本
            
        Returns:
            IC统计指标字典
        """
        if ic_series.empty:
            return {}
        
        if window is None:
            window = self.ic_config.get('window', 60)
        
        # 计算滚动统计指标
        ic_mean = ic_series.rolling(window).mean()
        ic_std = ic_series.rolling(window).std()
        ic_ir = ic_mean / ic_std  # Information Ratio
        
        # 最新值
        latest_mean = ic_mean.iloc[-1] if not ic_mean.empty else np.nan
        latest_std = ic_std.iloc[-1] if not ic_std.empty else np.nan
        latest_ir = ic_ir.iloc[-1] if not ic_ir.empty else np.nan
        
        # 全样本统计
        full_mean = ic_series.mean()
        full_std = ic_series.std()
        full_ir = full_mean / full_std if full_std != 0 else np.nan
        
        # 胜率（IC > 0的比例）
        win_rate = (ic_series > 0).mean()
        
        # 绝对IC均值
        abs_ic_mean = ic_series.abs().mean()
        
        summary = {
            f'ic_mean_{window}d': latest_mean,
            f'ic_std_{window}d': latest_std,
            f'ic_ir_{window}d': latest_ir,
            'ic_mean_full': full_mean,
            'ic_std_full': full_std,
            'ic_ir_full': full_ir,
            'win_rate': win_rate,
            'abs_ic_mean': abs_ic_mean,
            'observation_count': len(ic_series.dropna())
        }
        
        return summary
    
    def calc_multi_factor_ic(self, factors_df: pd.DataFrame, ret_df: pd.DataFrame) -> pd.DataFrame:
        """计算多因子IC矩阵
        
        Args:
            factors_df: 多因子矩阵 MultiIndex DataFrame (factor, ts_code)
            ret_df: 收益率矩阵 DataFrame(index=date, columns=ts_code)
            
        Returns:
            IC时间序列矩阵 DataFrame(index=date, columns=factor_name)
        """
        if factors_df.empty or ret_df.empty:
            return pd.DataFrame()
        
        # 检查是否为MultiIndex
        if not isinstance(factors_df.columns, pd.MultiIndex):
            self._log_progress("因子数据不是MultiIndex格式，无法计算多因子IC")
            return pd.DataFrame()
        
        ic_results = {}
        factor_names = factors_df.columns.get_level_values(0).unique()
        method = self.ic_config.get('correlation_method', 'spearman')
        
        self._log_progress(f"开始计算 {len(factor_names)} 个因子的IC")
        
        for factor_name in factor_names:
            try:
                # 提取单个因子数据
                factor_matrix = factors_df[factor_name]
                
                # 计算IC时间序列
                ic_series = self.calc_ic_timeseries(factor_matrix, ret_df, method)
                
                if not ic_series.empty:
                    ic_results[factor_name] = ic_series
                    self._log_progress(f"因子 {factor_name} IC计算完成")
                else:
                    self._log_progress(f"因子 {factor_name} IC计算失败")
                    
            except Exception as e:
                print(f"计算因子 {factor_name} IC时出错: {e}")
                continue
        
        if not ic_results:
            return pd.DataFrame()
        
        # 合并IC结果
        ic_df = pd.DataFrame(ic_results)
        
        self._log_progress(f"多因子IC计算完成，结果形状: {ic_df.shape}")
        return ic_df
    
    def rank_factors(self, ic_summary_dict: Dict[str, Dict[str, float]], 
                    primary_metric: str = 'ic_ir_60d') -> pd.DataFrame:
        """根据IC指标对因子进行排序
        
        Args:
            ic_summary_dict: 因子IC摘要字典 {factor_name: {metric: value}}
            primary_metric: 主要排序指标
            
        Returns:
            因子排名表 DataFrame
        """
        if not ic_summary_dict:
            return pd.DataFrame()
        
        # 转换为DataFrame
        summary_df = pd.DataFrame(ic_summary_dict).T
        
        if summary_df.empty:
            return pd.DataFrame()
        
        # 按主要指标排序（降序）
        if primary_metric in summary_df.columns:
            summary_df = summary_df.sort_values(primary_metric, ascending=False)
        
        # 添加排名列
        summary_df['rank'] = range(1, len(summary_df) + 1)
        
        # 计算综合得分（可选）
        score_components = []
        weights = {'ic_ir_60d': 0.4, 'abs_ic_mean': 0.3, 'win_rate': 0.3}
        
        for metric, weight in weights.items():
            if metric in summary_df.columns:
                # 标准化到0-1范围
                values = summary_df[metric].fillna(0)
                if values.std() > 0:
                    normalized = (values - values.min()) / (values.max() - values.min())
                    score_components.append(normalized * weight)
        
        if score_components:
            summary_df['composite_score'] = sum(score_components)
            # 按综合得分重新排序
            summary_df = summary_df.sort_values('composite_score', ascending=False)
            summary_df['rank'] = range(1, len(summary_df) + 1)
        
        return summary_df
    
    def generate_ic_report(self, ic_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """生成IC分析报告
        
        Args:
            ic_df: IC时间序列矩阵
            
        Returns:
            包含各种IC分析结果的字典
        """
        if ic_df.empty:
            return {}
        
        # 1. IC摘要统计
        ic_summary = {}
        for factor_name in ic_df.columns:
            ic_series = ic_df[factor_name].dropna()
            if len(ic_series) > 0:
                ic_summary[factor_name] = self.calc_ic_summary(ic_series)
        
        # 2. 因子排名
        factor_ranking = self.rank_factors(ic_summary)
        
        # 3. IC相关性矩阵
        ic_corr = ic_df.corr()
        
        # 4. IC滚动统计
        window = self.ic_config.get('window', 60)
        ic_rolling_mean = ic_df.rolling(window).mean()
        ic_rolling_std = ic_df.rolling(window).std()
        
        report = {
            'ic_timeseries': ic_df,
            'ic_summary': pd.DataFrame(ic_summary).T,
            'factor_ranking': factor_ranking,
            'ic_correlation': ic_corr,
            'ic_rolling_mean': ic_rolling_mean,
            'ic_rolling_std': ic_rolling_std
        }
        
        self._log_progress("IC分析报告生成完成")
        return report
    
    def save_ic_results(self, ic_report: Dict[str, pd.DataFrame], output_dir: str = None):
        """保存IC分析结果
        
        Args:
            ic_report: IC分析报告
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = self.base_path / self.config['paths']['ic_output']
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存各类结果
        for report_name, df in ic_report.items():
            if df.empty:
                continue
                
            file_path = output_dir / f"{report_name}.csv"
            df.to_csv(file_path, encoding='utf-8')
            self._log_progress(f"IC结果已保存: {file_path}")
    
    def _validate_result(self, result: pd.DataFrame, name: str) -> bool:
        """验证计算结果（预留接口）
        
        Args:
            result: 计算结果
            name: 结果名称
            
        Returns:
            验证是否通过
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
        print(f"[{timestamp}] [ICEngine] {message}")
