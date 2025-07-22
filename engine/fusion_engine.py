# -*- coding: utf-8 -*-
"""
因子融合引擎 - 多因子融合方法
支持等权、IC加权、LightGBM等模块化融合方式
"""
import pandas as pd
import numpy as np
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class FusionEngine:
    """多因子融合引擎"""
    
    def __init__(self, config_path: str = "config/factors.yml"):
        self.base_path = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.fusion_config = self.config.get('fusion', {})

    def _load_config(self, config_path: str) -> dict:
        config_file = self.base_path / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def equal_weight_fusion(self, factor_names: List[str]) -> Dict[str, float]:
        """等权融合 - 生成等权重字典
        
        Args:
            factor_names: 因子名称列表
            
        Returns:
            等权重字典
        """
        if not factor_names:
            return {}
        
        n_factors = len(factor_names)
        weight = 1.0 / n_factors
        
        weights = {factor_name: weight for factor_name in factor_names}
        
        self._log_progress(f"等权融合完成，{n_factors}个因子，每个权重: {weight:.4f}")
        return weights

    def ic_weight_fusion(self, ic_df: pd.DataFrame) -> Dict[str, float]:
        """基于IC的加权融合 - 生成基于IC表现的权重字典
        
        Args:
            ic_df: IC时间序列矩阵 DataFrame(index=date, columns=factor_name)
            
        Returns:
            IC权重字典
        """
        if ic_df.empty:
            return {}
        
        # 计算各因子的IC统计指标
        weights = {}
        
        for factor_name in ic_df.columns:
            ic_series = ic_df[factor_name].dropna()
            
            if len(ic_series) > 0:
                ic_mean = ic_series.mean()
                ic_std = ic_series.std()
                
                # 使用IC_IR作为权重基础
                ic_ir = ic_mean / ic_std if ic_std > 0 else 0
                # 使用绝对值IC_IR作为权重
                weights[factor_name] = abs(ic_ir)
            else:
                weights[factor_name] = 0
        
        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        else:
            # 如果没有有效IC，回退到等权
            n_factors = len(ic_df.columns)
            weights = {k: 1.0/n_factors for k in ic_df.columns}
            self._log_progress("无有效IC数据，回退到等权融合")
        
        self._log_progress(f"IC加权融合完成，权重: {weights}")
        return weights
    
    def apply_weights(self, factors_df: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
        """应用权重到因子矩阵
        
        Args:
            factors_df: MultiIndex DataFrame (columns=[factor_name, ts_code], index=date)
            weights: 权重字典 {factor_name: weight}
            
        Returns:
            融合因子矩阵 DataFrame(index=date, columns=ts_code)
        """
        if factors_df.empty or not weights:
            return pd.DataFrame()
        
        # 检查是否为MultiIndex
        if not isinstance(factors_df.columns, pd.MultiIndex):
            self._log_progress("警告: 输入数据不是MultiIndex格式")
            return pd.DataFrame()
        
        # 获取股票列表
        ts_codes = factors_df.columns.get_level_values(1).unique()
        result_data = {}
        
        for ts_code in ts_codes:
            weighted_sum = None
            
            for factor_name, weight in weights.items():
                if (factor_name, ts_code) in factors_df.columns:
                    factor_series = factors_df[(factor_name, ts_code)] * weight
                    
                    if weighted_sum is None:
                        weighted_sum = factor_series
                    else:
                        weighted_sum += factor_series
            
            if weighted_sum is not None:
                result_data[ts_code] = weighted_sum
        
        if result_data:
            result = pd.DataFrame(result_data)
            self._log_progress(f"权重应用完成，结果形状: {result.shape}")
            return result
        else:
            return pd.DataFrame()

    def lgb_fusion(self, factors_df: pd.DataFrame, ret_df: pd.DataFrame) -> pd.DataFrame:
        """LightGBM融合：使用LightGBM训练因子融合模型
        
        Args:
            factors_df: MultiIndex DataFrame (columns=[factor_name, ts_code], index=date)
            ret_df: 前瞻收益率 DataFrame(index=date, columns=ts_code)
            
        Returns:
            融合因子矩阵 DataFrame(index=date, columns=ts_code)
        """
        try:
            import lightgbm as lgb
        except ImportError:
            self._log_progress("LightGBM未安装，跳过LGB融合")
            return pd.DataFrame()
        
        if factors_df.empty or ret_df.empty:
            return pd.DataFrame()
        
        # 数据对齐
        common_dates = factors_df.index.intersection(ret_df.index)
        common_codes = set(factors_df.columns.get_level_values(1)).intersection(set(ret_df.columns))
        
        if len(common_dates) < 100 or len(common_codes) < 10:
            self._log_progress("数据量不足，跳过LGB融合")
            return pd.DataFrame()
        
        # 准备训练数据
        X_list, y_list = [], []
        factor_names = factors_df.columns.get_level_values(0).unique()
        
        for date in common_dates:
            for code in common_codes:
                # 构建特征向量
                features = []
                for factor in factor_names:
                    if (factor, code) in factors_df.columns:
                        features.append(factors_df.loc[date, (factor, code)])
                    else:
                        features.append(np.nan)
                
                # 获取标签
                if code in ret_df.columns:
                    target = ret_df.loc[date, code]
                    
                    # 过滤缺失值
                    if not pd.isna(target) and not any(pd.isna(features)):
                        X_list.append(features)
                        y_list.append(target)
        
        if len(X_list) < 100:
            self._log_progress("有效样本不足，跳过LGB融合")
            return pd.DataFrame()
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        # 训练测试分割
        split_idx = int(len(X) * self.fusion_config.get('train_test_split', 0.7))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # 训练LightGBM模型
        lgb_params = self.fusion_config.get('lgb_params', {})
        train_data = lgb.Dataset(X_train, label=y_train)
        
        model = lgb.train(
            lgb_params,
            train_data,
            num_boost_round=100,
            valid_sets=[train_data],
            callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)]
        )
        
        # 预测融合因子
        result_data = {}
        for code in common_codes:
            predictions = []
            
            for date in common_dates:
                features = []
                for factor in factor_names:
                    if (factor, code) in factors_df.columns:
                        features.append(factors_df.loc[date, (factor, code)])
                    else:
                        features.append(0)  # 缺失值填0
                
                if not any(pd.isna(features)):
                    pred = model.predict([features])[0]
                    predictions.append(pred)
                else:
                    predictions.append(np.nan)
            
            result_data[code] = pd.Series(predictions, index=common_dates)
        
        result = pd.DataFrame(result_data)
        self._log_progress(f"LightGBM融合完成，训练样本: {len(X_train)}, 测试样本: {len(X_test)}")
        
        return result
    
    def fuse_factors(self, factors_df: pd.DataFrame, ic_summary: pd.DataFrame = None, 
                    ret_df: pd.DataFrame = None, methods: List[str] = None) -> Dict[str, pd.DataFrame]:
        """执行多种融合方法
        
        Args:
            factors_df: 因子矩阵
            ic_summary: IC统计摘要
            ret_df: 前瞻收益率（用于LGB融合）
            methods: 融合方法列表
            
        Returns:
            不同融合方法的结果字典
        """
        if methods is None:
            methods = self.fusion_config.get('methods', ['equal_weight'])
        
        results = {}
        
        for method in methods:
            try:
                if method == 'equal_weight':
                    results[method] = self.equal_weight_fusion(factors_df)
                elif method == 'ic_weight' and ic_summary is not None:
                    results[method] = self.ic_weight_fusion(factors_df, ic_summary)
                elif method == 'lgb' and ret_df is not None:
                    results[method] = self.lgb_fusion(factors_df, ret_df)
                else:
                    self._log_progress(f"跳过融合方法: {method} (缺少必要数据)")
                    
            except Exception as e:
                self._log_progress(f"融合方法 {method} 执行失败: {e}")
                continue
        
        return results
    
    def save_fusion_results(self, fusion_results: Dict[str, pd.DataFrame], output_dir: str = None):
        """保存融合结果
        
        Args:
            fusion_results: 融合结果字典
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = self.base_path / self.config['paths']['fusion_output']
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for method, result_df in fusion_results.items():
            if result_df.empty:
                continue
                
            file_path = output_dir / f"fusion_{method}.csv"
            result_df.to_csv(file_path, encoding='utf-8')
            self._log_progress(f"融合结果已保存: {file_path}")
    
    def _log_progress(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [FusionEngine] {message}")
