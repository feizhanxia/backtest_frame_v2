#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Universe质量筛选引擎
自动根据数据质量筛选高质量标的池
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob
import yaml
from typing import List, Dict, Tuple
from datetime import datetime
import logging

class UniverseFilter:
    """Universe质量筛选器"""
    
    def __init__(self, config_path: str = "config/factors.yml"):
        """初始化筛选器
        
        Args:
            config_path: 配置文件路径
        """
        self.base_path = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        
    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        config_file = self.base_path / config_path
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger('UniverseFilter')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s', 
                                        datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def analyze_data_quality(self, start_date: str = None, end_date: str = None) -> Dict[str, Dict]:
        """分析数据质量
        
        Args:
            start_date: 开始日期，格式YYYY-MM-DD
            end_date: 结束日期，格式YYYY-MM-DD
            
        Returns:
            数据质量分析结果字典
        """
        start_date = start_date or self.config['data']['start_date']
        end_date = end_date or self.config['data']['end_date']
        
        # 转换日期格式
        start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        
        self.logger.info(f"分析数据质量: {start_date} 到 {end_date}")
        
        # 读取原始universe文件
        universe_file = self.config['data']['universe_file']
        universe_path = self.base_path / universe_file
        
        if not universe_path.exists():
            self.logger.error(f"未找到universe文件: {universe_path}")
            return {}
        
        universe_df = pd.read_csv(universe_path)
        universe_codes = set(universe_df['ts_code'].tolist())
        
        # 扫描数据文件
        processed_path = self.base_path / self.config['paths']['processed_data']
        parquet_files = glob.glob(str(processed_path / "**/*.parquet"), recursive=True)
        
        self.logger.info(f"扫描数据文件: {len(parquet_files)} 个文件")
        
        quality_info = {}
        matched_count = 0
        
        for file_path in parquet_files:
            try:
                file_name = Path(file_path).stem
                code = file_name
                
                if code not in universe_codes:
                    continue
                
                df = pd.read_parquet(file_path)
                
                # 统一处理日期索引
                if df.index.name == 'trade_date':
                    df.index = pd.to_datetime(df.index)
                elif 'trade_date' in df.columns:
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    df = df.set_index('trade_date')
                
                if df.empty:
                    continue
                
                # 过滤到指定日期范围
                mask = (df.index >= start_date) & (df.index <= end_date)
                df_period = df[mask]
                
                if df_period.empty:
                    continue
                
                # 计算数据质量指标
                total_days = len(df_period)
                
                # 检查各字段的完整性
                fields_quality = {}
                for field in ['close', 'vol', 'amount', 'open', 'high', 'low']:
                    if field in df_period.columns:
                        valid_count = df_period[field].notna().sum()
                        fields_quality[field] = {
                            'valid_count': valid_count,
                            'total_count': total_days,
                            'coverage_rate': valid_count / total_days if total_days > 0 else 0
                        }
                
                # 综合评分
                close_coverage = fields_quality.get('close', {}).get('coverage_rate', 0)
                vol_coverage = fields_quality.get('vol', {}).get('coverage_rate', 0)
                amount_coverage = fields_quality.get('amount', {}).get('coverage_rate', 0)
                
                # 加权综合评分：收盘价80%，成交量和成交额各10%
                overall_score = (close_coverage * 0.8 + vol_coverage * 0.1 + amount_coverage * 0.1)
                
                quality_info[code] = {
                    'total_days': total_days,
                    'fields_quality': fields_quality,
                    'overall_score': overall_score,
                    'date_range': (df_period.index.min(), df_period.index.max())
                }
                
                matched_count += 1
                
            except Exception as e:
                self.logger.warning(f"处理文件失败: {file_path} - {e}")
        
        self.logger.info(f"数据质量分析完成: {matched_count} 个标的")
        return quality_info
    
    def filter_high_quality_universe(self, 
                                   min_coverage_rate: float = 0.65,
                                   min_close_coverage: float = 0.8,
                                   min_trading_days: int = 100,
                                   max_universe_size: int = 150) -> List[str]:
        """筛选高质量标的池
        
        Args:
            min_coverage_rate: 最低综合覆盖率
            min_close_coverage: 最低收盘价覆盖率
            min_trading_days: 最少交易天数
            max_universe_size: 最大标的数量
            
        Returns:
            高质量标的代码列表
        """
        quality_info = self.analyze_data_quality()
        
        if not quality_info:
            self.logger.error("无数据质量信息，无法筛选")
            return []
        
        # 筛选条件
        candidates = []
        
        for code, info in quality_info.items():
            # 基本条件筛选
            if info['total_days'] < min_trading_days:
                continue
            
            # 收盘价覆盖率检查
            close_coverage = info['fields_quality'].get('close', {}).get('coverage_rate', 0)
            if close_coverage < min_close_coverage:
                continue
            
            # 综合评分检查
            if info['overall_score'] < min_coverage_rate:
                continue
            
            candidates.append((code, info['overall_score']))
        
        # 按综合评分排序，取前N个
        candidates.sort(key=lambda x: x[1], reverse=True)
        selected_codes = [code for code, score in candidates[:max_universe_size]]
        
        self.logger.info(f"高质量标的筛选完成:")
        self.logger.info(f"  原始标的数: {len(quality_info)}")
        self.logger.info(f"  候选标的数: {len(candidates)}")
        self.logger.info(f"  最终选择数: {len(selected_codes)}")
        
        # 显示筛选统计
        if candidates:
            scores = [score for _, score in candidates[:max_universe_size]]
            self.logger.info(f"  平均质量评分: {np.mean(scores):.3f}")
            self.logger.info(f"  最低质量评分: {np.min(scores):.3f}")
            self.logger.info(f"  最高质量评分: {np.max(scores):.3f}")
        
        return selected_codes
    
    def generate_high_quality_universe(self, output_path: str = None) -> str:
        """生成高质量universe文件
        
        Args:
            output_path: 输出文件路径，默认为config/universe_high_quality.csv
            
        Returns:
            生成的文件路径
        """
        if output_path is None:
            output_path = self.base_path / "config/universe_high_quality.csv"
        else:
            output_path = Path(output_path)
        
        # 获取筛选配置
        filter_config = self.config.get('universe_filter', {})
        min_coverage_rate = filter_config.get('min_coverage_rate', 0.65)
        min_close_coverage = filter_config.get('min_close_coverage', 0.8)
        min_trading_days = filter_config.get('min_trading_days', 100)
        max_universe_size = filter_config.get('max_universe_size', 150)
        
        # 筛选高质量标的
        high_quality_codes = self.filter_high_quality_universe(
            min_coverage_rate=min_coverage_rate,
            min_close_coverage=min_close_coverage,
            min_trading_days=min_trading_days,
            max_universe_size=max_universe_size
        )
        
        if not high_quality_codes:
            self.logger.error("未找到符合条件的高质量标的")
            return ""
        
        # 生成CSV文件
        df = pd.DataFrame({'ts_code': high_quality_codes})
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        self.logger.info(f"高质量universe已保存: {output_path}")
        self.logger.info(f"包含 {len(high_quality_codes)} 个标的")
        
        return str(output_path)
    
    def auto_update_universe(self) -> bool:
        """自动更新universe配置
        
        Returns:
            是否成功更新
        """
        try:
            # 自动生成高质量universe文件路径
            original_universe_file = self.config['data']['universe_file']
            original_path = self.base_path / original_universe_file
            high_quality_path = original_path.parent / "universe_high_quality.csv"
            
            # 检查高质量文件是否需要重新生成
            if high_quality_path.exists():
                # 检查文件是否过期
                filter_config = self.config.get('universe_filter', {})
                auto_update_days = filter_config.get('auto_update_days', 7)
                file_age = datetime.now().timestamp() - high_quality_path.stat().st_mtime
                if file_age < auto_update_days * 24 * 3600:
                    self.logger.info(f"高质量universe文件较新（{file_age/86400:.1f}天），无需重新生成")
                    return True
            
            # 生成新的高质量universe
            self.logger.info("开始生成高质量universe文件...")
            output_path = self.generate_high_quality_universe(str(high_quality_path))
            
            if not output_path:
                return False
            
            self.logger.info(f"高质量universe文件已生成: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"自动更新universe失败: {e}")
            return False
