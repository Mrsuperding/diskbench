#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本
用于执行测试用例并生成测试报告
"""

import os
import sys
import pytest
import json
import datetime
import shutil
from argparse import ArgumentParser

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def parse_args():
    """解析命令行参数"""
    parser = ArgumentParser(description='运行IO测试平台测试用例')
    parser.add_argument('-c', '--case', type=str, help='指定测试用例文件或目录')
    parser.add_argument('-r', '--report', type=str, default='html', choices=['html', 'json', 'all'], help='测试报告类型')
    parser.add_argument('-d', '--debug', action='store_true', help='调试模式，显示详细日志')
    return parser.parse_args()

def run_tests(case_path, report_type, debug=False):
    """运行测试用例"""
    # 确保报告目录存在
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # 生成测试报告文件名
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    html_report = os.path.join(reports_dir, f'test_report_{timestamp}.html')
    json_report = os.path.join(reports_dir, f'test_report_{timestamp}.json')
    
    # 构建pytest命令行参数
    pytest_args = [
        '-v',
        '--tb=short' if not debug else '--tb=long',
    ]
    
    # 添加测试报告参数
    if report_type in ['html', 'all']:
        pytest_args.extend(['--html', html_report, '--self-contained-html'])
    
    if report_type in ['json', 'all']:
        pytest_args.extend(['--json-report', '--json-report-file', json_report])
    
    # 添加测试用例路径
    if case_path:
        pytest_args.append(case_path)
    else:
        pytest_args.append('tests/test_case')
    
    # 运行测试
    print(f"\n📋 开始运行测试，测试报告将生成到 {reports_dir} 目录")
    print(f"🎯 测试用例路径: {case_path or 'test_case'}")
    print(f"📊 报告类型: {report_type}")
    print(f"\n{'='*60}")
    
    # 执行pytest
    result = pytest.main(pytest_args)
    
    print(f"{'='*60}")
    print(f"\n🏁 测试运行完成")
    print(f"📋 测试结果: {'通过' if result == 0 else '失败'}")
    
    # 显示报告路径
    if report_type in ['html', 'all']:
        print(f"📄 HTML报告: {html_report}")
    
    if report_type in ['json', 'all']:
        print(f"📊 JSON报告: {json_report}")
    
    return result

def generate_summary_report():
    """生成测试结果汇总报告"""
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'reports')
    summary_file = os.path.join(reports_dir, 'test_summary.json')
    
    # 读取所有测试结果文件
    all_results = {}
    
    # 读取test_results.json
    test_results_file = os.path.join(reports_dir, 'test_results.json')
    if os.path.exists(test_results_file):
        with open(test_results_file, 'r', encoding='utf-8') as f:
            all_results.update(json.load(f))
    
    # 读取所有JSON格式的测试报告
    for filename in os.listdir(reports_dir):
        if filename.endswith('.json') and filename.startswith('test_report_'):
            report_file = os.path.join(reports_dir, filename)
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    # 提取有用信息
                    if 'tests' in report_data:
                        for test in report_data['tests']:
                            test_id = test.get('nodeid')
                            if test_id:
                                all_results[test_id] = {
                                    'outcome': test.get('outcome'),
                                    'duration': test.get('duration'),
                                    'keywords': test.get('keywords', []),
                                    'report_file': filename
                                }
            except Exception as e:
                print(f"⚠️  读取报告文件 {filename} 出错: {e}")
    
    # 生成汇总报告
    summary = {
        'generated_at': datetime.datetime.now().isoformat(),
        'total_tests': len(all_results),
        'passed_tests': sum(1 for result in all_results.values() if result.get('outcome') == 'passed'),
        'failed_tests': sum(1 for result in all_results.values() if result.get('outcome') == 'failed'),
        'skipped_tests': sum(1 for result in all_results.values() if result.get('outcome') == 'skipped'),
        'tests': all_results
    }
    
    # 保存汇总报告
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"📊 汇总报告已生成: {summary_file}")
    print(f"📋 测试统计: 总测试数={summary['total_tests']}, 通过={summary['passed_tests']}, 失败={summary['failed_tests']}, 跳过={summary['skipped_tests']}")

def main():
    """主函数"""
    args = parse_args()
    
    # 运行测试
    result = run_tests(args.case, args.report, args.debug)
    
    # 生成汇总报告
    generate_summary_report()
    
    return result

if __name__ == '__main__':
    sys.exit(main())
