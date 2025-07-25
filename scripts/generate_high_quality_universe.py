#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据质量评估和高质量Universe生成工具
筛选数据相对足够的标的进行回测
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob
import yaml
from datetime import datetime, timedelta

class DataQualityFilter:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.config = self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        config_file = self.base_path / "config/factors.yml"
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def evaluate_data_quality(self, min_coverage_rate=0.7, min_history_days=100, 
                            target_date_range=None):
        """评估标的数据质量
        
        Args:
            min_coverage_rate: 最小覆盖率要求 (0-1)
            min_history_days: 最小历史天数要求
            target_date_range: 目标日期范围 (start_date, end_date)
        
        Returns:
            qualified_assets: 合格标的列表及其质量评分
        """
        print("🔍 开始数据质量评估...")
        
        # 设置目标日期范围
        if target_date_range is None:
            start_date = pd.to_datetime(self.config['data']['start_date'])
            end_date = pd.to_datetime(self.config['data']['end_date'])
        else:
            start_date, end_date = target_date_range
        
        target_trading_days = pd.bdate_range(start_date, end_date)
        target_days_count = len(target_trading_days)
        
        print(f"目标时间范围: {start_date.date()} 至 {end_date.date()}")
        print(f"目标交易日数: {target_days_count}")
        
        # 加载universe
        universe_file = self.base_path / self.config['data']['universe_file']
        universe_df = pd.read_csv(universe_file)
        universe_codes = set(universe_df['ts_code'].tolist())
        
        # 扫描数据文件
        processed_path = self.base_path / self.config['paths']['processed_data']
        parquet_files = glob.glob(str(processed_path / "**/*.parquet"), recursive=True)
        
        asset_quality_scores = {}
        detailed_stats = {}
        
        print(f"\n📊 评估 {len(universe_codes)} 个标的的数据质量...")
        
        processed_count = 0
        for file_path in parquet_files:
            file_name = Path(file_path).stem
            code = file_name
            
            if code not in universe_codes:
                continue
                
            try:
                df = pd.read_parquet(file_path)
                
                # 统一处理日期索引
                if df.index.name == 'trade_date':
                    df.index = pd.to_datetime(df.index)
                elif 'trade_date' in df.columns:
                    df['trade_date'] = pd.to_datetime(df['trade_date'])
                    df = df.set_index('trade_date')
                
                # 筛选目标日期范围
                df_filtered = df[(df.index >= start_date) & (df.index <= end_date)]
                
                if df_filtered.empty:
                    continue
                
                # 数据质量评估指标
                quality_metrics = self._calculate_quality_metrics(
                    df_filtered, target_trading_days, target_days_count
                )
                
                # 计算综合质量评分
                quality_score = self._calculate_quality_score(quality_metrics)
                
                # 判断是否满足最低要求
                meets_requirements = (
                    quality_metrics['coverage_rate'] >= min_coverage_rate and
                    quality_metrics['available_days'] >= min_history_days and
                    quality_metrics['close_completeness'] >= 0.8  # 收盘价完整性要求
                )
                
                asset_quality_scores[code] = {
                    'quality_score': quality_score,
                    'meets_requirements': meets_requirements,
                    **quality_metrics
                }
                
                detailed_stats[code] = quality_metrics
                processed_count += 1
                
                if processed_count % 50 == 0:
                    print(f"   已处理: {processed_count}/{len(universe_codes)}")
                
            except Exception as e:
                print(f"   ⚠️  处理 {code} 时出错: {e}")
                continue
        
        return asset_quality_scores, detailed_stats
    
    def _calculate_quality_metrics(self, df, target_trading_days, target_days_count):
        """计算数据质量指标"""
        
        # 基础指标
        available_days = len(df)
        coverage_rate = available_days / target_days_count if target_days_count > 0 else 0
        
        # 各字段完整性
        close_completeness = df['close'].notna().sum() / len(df) if len(df) > 0 else 0
        vol_completeness = df['vol'].notna().sum() / len(df) if 'vol' in df.columns and len(df) > 0 else 0
        amount_completeness = df['amount'].notna().sum() / len(df) if 'amount' in df.columns and len(df) > 0 else 0
        
        # 连续性评估
        df_sorted = df.sort_index()
        date_gaps = []
        if len(df_sorted) > 1:
            for i in range(1, len(df_sorted)):
                gap_days = (df_sorted.index[i] - df_sorted.index[i-1]).days
                if gap_days > 3:  # 超过3天认为是数据缺口
                    date_gaps.append(gap_days)
        
        max_gap = max(date_gaps) if date_gaps else 0
        gap_count = len(date_gaps)
        
        # 数据更新度
        last_date = df.index.max()
        days_since_last_update = (pd.Timestamp.now() - last_date).days
        
        return {
            'available_days': available_days,
            'coverage_rate': coverage_rate,
            'close_completeness': close_completeness,
            'vol_completeness': vol_completeness,
            'amount_completeness': amount_completeness,
            'max_gap_days': max_gap,
            'gap_count': gap_count,
            'days_since_last_update': days_since_last_update,
            'date_range': (df.index.min(), df.index.max())
        }
    
    def _calculate_quality_score(self, metrics):
        """计算综合质量评分 (0-100)"""
        
        # 各项指标权重
        weights = {
            'coverage_rate': 0.3,      # 覆盖率权重30%
            'close_completeness': 0.25, # 收盘价完整性25%
            'vol_completeness': 0.15,   # 成交量完整性15%
            'amount_completeness': 0.15, # 成交额完整性15%
            'continuity': 0.1,          # 连续性10%
            'freshness': 0.05           # 更新度5%
        }
        
        # 计算各项得分
        coverage_score = min(metrics['coverage_rate'] * 100, 100)
        close_score = metrics['close_completeness'] * 100
        vol_score = metrics['vol_completeness'] * 100
        amount_score = metrics['amount_completeness'] * 100
        
        # 连续性得分 (基于数据缺口)
        if metrics['max_gap_days'] == 0:
            continuity_score = 100
        elif metrics['max_gap_days'] <= 7:
            continuity_score = 80
        elif metrics['max_gap_days'] <= 30:
            continuity_score = 60
        else:
            continuity_score = max(0, 60 - metrics['max_gap_days'])
        
        # 更新度得分
        if metrics['days_since_last_update'] <= 3:
            freshness_score = 100
        elif metrics['days_since_last_update'] <= 7:
            freshness_score = 80
        elif metrics['days_since_last_update'] <= 30:
            freshness_score = 60
        else:
            freshness_score = max(0, 60 - metrics['days_since_last_update'])
        
        # 计算加权总分
        total_score = (
            coverage_score * weights['coverage_rate'] +
            close_score * weights['close_completeness'] +
            vol_score * weights['vol_completeness'] +
            amount_score * weights['amount_completeness'] +
            continuity_score * weights['continuity'] +
            freshness_score * weights['freshness']
        )
        
        return round(total_score, 2)
    
    def generate_high_quality_universe(self, min_coverage_rate=0.7, min_history_days=100,
                                     min_quality_score=70, max_assets=None,
                                     output_file="config/universe_high_quality.csv"):
        """生成高质量标的池
        
        Args:
            min_coverage_rate: 最小覆盖率
            min_history_days: 最小历史天数
            min_quality_score: 最小质量评分
            max_assets: 最大标的数量限制
            output_file: 输出文件路径
        """
        
        print("=" * 60)
        print("🏆 生成高质量标的池")
        print("=" * 60)
        
        print(f"筛选条件:")
        print(f"  最小覆盖率: {min_coverage_rate*100:.1f}%")
        print(f"  最小历史天数: {min_history_days}")
        print(f"  最小质量评分: {min_quality_score}")
        if max_assets:
            print(f"  最大标的数量: {max_assets}")
        
        # 评估数据质量
        asset_scores, detailed_stats = self.evaluate_data_quality(
            min_coverage_rate, min_history_days
        )
        
        # 筛选高质量标的
        qualified_assets = []
        for code, metrics in asset_scores.items():
            if (metrics['meets_requirements'] and 
                metrics['quality_score'] >= min_quality_score):
                qualified_assets.append({
                    'ts_code': code,
                    'quality_score': metrics['quality_score'],
                    'coverage_rate': metrics['coverage_rate'],
                    'available_days': metrics['available_days'],
                    'close_completeness': metrics['close_completeness'],
                    'vol_completeness': metrics['vol_completeness'],
                    'amount_completeness': metrics['amount_completeness']
                })
        
        # 按质量评分排序
        qualified_assets.sort(key=lambda x: x['quality_score'], reverse=True)
        
        # 限制数量
        if max_assets and len(qualified_assets) > max_assets:
            qualified_assets = qualified_assets[:max_assets]
        
        print(f"\n📊 筛选结果:")
        print(f"  原始标的数: {len(asset_scores)}")
        print(f"  合格标的数: {len(qualified_assets)}")
        print(f"  筛选成功率: {len(qualified_assets)/len(asset_scores)*100:.1f}%")
        
        if qualified_assets:
            scores = [asset['quality_score'] for asset in qualified_assets]
            coverages = [asset['coverage_rate'] for asset in qualified_assets]
            
            print(f"\n📈 质量统计:")
            print(f"  平均质量评分: {np.mean(scores):.1f}")
            print(f"  最高质量评分: {np.max(scores):.1f}")
            print(f"  最低质量评分: {np.min(scores):.1f}")
            print(f"  平均覆盖率: {np.mean(coverages)*100:.1f}%")
            
            # 显示前10名
            print(f"\n🏅 质量前10名:")
            for i, asset in enumerate(qualified_assets[:10]):
                print(f"  {i+1:2d}. {asset['ts_code']}: "
                      f"评分{asset['quality_score']:.1f}, "
                      f"覆盖{asset['coverage_rate']*100:.1f}%, "
                      f"{asset['available_days']}天")
        
        # 保存结果
        if qualified_assets:
            output_path = self.base_path / output_file
            output_path.parent.mkdir(exist_ok=True)
            
            # 只保存ts_code列用于universe配置
            universe_df = pd.DataFrame([{'ts_code': asset['ts_code']} 
                                      for asset in qualified_assets])
            universe_df.to_csv(output_path, index=False)
            
            # 保存详细报告
            detailed_output = output_path.parent / f"{output_path.stem}_detailed.csv"
            detailed_df = pd.DataFrame(qualified_assets)
            detailed_df.to_csv(detailed_output, index=False)
            
            print(f"\n💾 文件已保存:")
            print(f"  Universe文件: {output_path}")
            print(f"  详细报告: {detailed_output}")
            
            return qualified_assets
        else:
            print("❌ 没有找到符合条件的标的")
            return []
    
    def analyze_coverage_improvement(self, high_quality_universe_file):
        """分析使用高质量Universe后的覆盖率改善"""
        
        print("=" * 60)
        print("📈 覆盖率改善分析")
        print("=" * 60)
        
        # 模拟因子计算的数据要求
        factor_requirements = {
            'mom20': {'fields': ['close'], 'min_history': 20},
            'shortrev5': {'fields': ['close'], 'min_history': 5},
            'vol20': {'fields': ['close'], 'min_history': 20},
            'macd_signal': {'fields': ['close'], 'min_history': 34},
            'turn_mean20': {'fields': ['vol', 'amount'], 'min_history': 20},
            'amihud20': {'fields': ['close', 'amount'], 'min_history': 20}
        }
        
        # 加载高质量universe
        hq_universe_path = self.base_path / high_quality_universe_file
        if not hq_universe_path.exists():
            print(f"❌ 高质量Universe文件不存在: {hq_universe_path}")
            return
        
        hq_universe_df = pd.read_csv(hq_universe_path)
        hq_codes = set(hq_universe_df['ts_code'].tolist())
        
        print(f"高质量Universe标的数: {len(hq_codes)}")
        
        # 评估预期覆盖率
        asset_scores, _ = self.evaluate_data_quality(min_coverage_rate=0.5)
        
        expected_coverage = {}
        for factor_name, req in factor_requirements.items():
            valid_assets = 0
            total_observations = 0
            
            for code in hq_codes:
                if code in asset_scores:
                    metrics = asset_scores[code]
                    
                    # 检查字段要求
                    fields_ok = True
                    if 'close' in req['fields'] and metrics['close_completeness'] < 0.8:
                        fields_ok = False
                    if 'vol' in req['fields'] and metrics['vol_completeness'] < 0.7:
                        fields_ok = False
                    if 'amount' in req['fields'] and metrics['amount_completeness'] < 0.7:
                        fields_ok = False
                    
                    # 检查历史长度
                    history_ok = metrics['available_days'] >= req['min_history']
                    
                    if fields_ok and history_ok:
                        valid_assets += 1
                        # 估算有效观测数
                        effective_days = max(0, metrics['available_days'] - req['min_history'])
                        total_observations += effective_days
            
            coverage_rate = valid_assets / len(hq_codes) * 100 if hq_codes else 0
            expected_coverage[factor_name] = {
                'valid_assets': valid_assets,
                'total_assets': len(hq_codes),
                'coverage_rate': coverage_rate,
                'estimated_observations': total_observations
            }
        
        print(f"\n📊 预期因子覆盖率:")
        for factor_name, info in expected_coverage.items():
            print(f"  {factor_name:12s}: {info['coverage_rate']:5.1f}% "
                  f"({info['valid_assets']}/{info['total_assets']} 标的, "
                  f"~{info['estimated_observations']:,} 观测)")
        
        # 估算总体改善
        avg_coverage = np.mean([info['coverage_rate'] for info in expected_coverage.values()])
        total_estimated_obs = sum([info['estimated_observations'] for info in expected_coverage.values()])
        
        print(f"\n🎯 总体预期:")
        print(f"  平均因子覆盖率: {avg_coverage:.1f}%")
        print(f"  总计预期观测数: ~{total_estimated_obs:,}")
        print(f"  与当前覆盖率对比: 预计提升 {avg_coverage/2.5:.1f} 倍")  # 当前约2.5%

def main():
    """主程序：生成高质量Universe"""
    filter_tool = DataQualityFilter()
    
    print("🚀 数据质量筛选工具")
    print("=" * 60)
    
    # 生成高质量标的池
    qualified_assets = filter_tool.generate_high_quality_universe(
        min_coverage_rate=0.6,    # 至少60%覆盖率
        min_history_days=50,      # 至少50天历史
        min_quality_score=60,     # 至少60分质量评分
        max_assets=100,           # 最多100个标的
        output_file="config/universe_high_quality.csv"
    )
    
    if qualified_assets:
        # 分析预期改善效果
        filter_tool.analyze_coverage_improvement("config/universe_high_quality.csv")
        
        print(f"\n🎉 高质量Universe生成完成！")
        print(f"💡 使用方法: 修改 config/factors.yml 中的 universe_file 为:")
        print(f"   universe_file: \"config/universe_high_quality.csv\"")

if __name__ == "__main__":
    main()
