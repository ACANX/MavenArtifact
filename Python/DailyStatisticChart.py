#!/usr/bin/env python3
# DailyStatisticChart.py

import json
import os
import time  # 添加time模块
from datetime import datetime, time as dtime  # 重命名time以避免冲突

# 图表配置
CHART_WIDTH = 1600
CHART_HEIGHT = 1000
MARGIN = 80
AXIS_COLOR = "#333333"
GRID_COLOR = "#e0e0e0"
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#66ffbd"]
FONT_FAMILY = "Arial, sans-serif"

def main():
    # 检查当前时间是否在允许的执行窗口内 (00:30:00 - 12:59:59)
    current_time = datetime.now().time()
    allowed_start = dtime(0, 20, 0)
    allowed_end = dtime(12, 59, 59)
    
    if not (allowed_start <= current_time <= allowed_end):
        print(f"当前时间 {current_time.strftime('%H:%M:%S')} 不在允许的执行窗口内 (01:20:00 - 01:59:59)")
        return
    
    print(f"当前时间 {current_time.strftime('%H:%M:%S')} 在允许的执行窗口内，开始处理数据...")
    
    # 文件路径配置
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "../Statistic/DailyIndexStatistic.json")
    output_path = os.path.join(base_dir, "../Statistic/DailyIndexStatistic.svg")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 读取并处理数据
    try:
        start_timestamp = time.time()  # 使用time模块的time函数
        with open(input_path, 'r') as f:
            data = json.load(f)
        load_time = time.time() - start_timestamp
        print(f"数据加载完成，耗时 {load_time:.2f} 秒")
    except FileNotFoundError:
        print(f"错误：在 {input_path} 找不到数据文件")
        return
    except json.JSONDecodeError:
        print("错误：无效的JSON数据")
        return
    
    # 按日期排序
    data.sort(key=lambda x: x['date'])
    
    # 提取数据
    dates = [str(d['date']) for d in data]
    formatted_dates = [f"{d[:4]}-{d[4:6]}-{d[6:]}" for d in dates]
    
    metrics = [
        {"name": "构件聚合数据", "values": [d['aio'] for d in data]},
        {"name": "构件基本信息", "values": [d['artifact'] for d in data]},
        {"name": "构件徽标", "values": [d['badge'] for d in data]},
        {"name": "构件扩展元数据", "values": [d['ext_metadata'] for d in data]},
        {"name": "构件版本信息", "values": [d['version'] for d in data]},
        {"name": "数据量偏差", "values": [d['badge'] - d['aio'] for d in data]}
    ]
    
    # 生成SVG图表
    start_timestamp = time.time()
    svg_content = generate_svg_chart(formatted_dates, metrics)
    gen_time = time.time() - start_timestamp
    print(f"图表生成完成，耗时 {gen_time:.2f} 秒")
    
    # 保存SVG文件
    with open(output_path, 'w') as f:
        f.write(svg_content)
    
    print(f"图表已保存到 {output_path}")


def add_xaxis_labels_smart(svg, dates, plot_width, chart_height, MARGIN):
    if not dates:
        return
    total_points = len(dates)
    available_width = plot_width - 2 * MARGIN
    
    # 根据数据密度自动调整
    if total_points <= 8:
        # 数据量少，全部显示
        indices_to_show = range(total_points)
    elif total_points <= 20:
        # 中等数据量，显示首尾和中间几个
        step = max(2, total_points // 6)
        indices_to_show = set([0, total_points-1])  # 首尾
        # 添加中间点
        mid_point = total_points // 2
        indices_to_show.update([mid_point])
        indices_to_show.update(range(step, total_points-1, step))
    else:
        # 大数据量，基于像素密度采样
        pixels_per_point = available_width / (total_points - 1)
        if pixels_per_point < 30:  # 非常密集
            step = max(5, total_points // 15)
        elif pixels_per_point < 60:  # 中等密度
            step = max(3, total_points // 10)
        else:  # 稀疏
            step = max(2, total_points // 8)
        indices_to_show = set([0, total_points-1])  # 保证首尾
        indices_to_show.update(range(0, total_points, step))
    
    # 渲染标签
    for i in sorted(indices_to_show):
        if i < len(dates):
            date = dates[i]
            x = MARGIN + i * (plot_width / (len(dates) - 1)) if len(dates) > 1 else MARGIN
            y = chart_height - MARGIN + 20
            # 格式化日期
            if len(date) >= 10:
                label = f"{date[5:7]}-{date[8:10]}"
            else:
                label = date
            svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="12">{label}</text>')
            

def generate_svg_chart(dates, metrics):
    """生成多指标趋势图SVG"""
    # 计算图表边界
    chart_width = CHART_WIDTH
    chart_height = CHART_HEIGHT
    plot_width = chart_width - 2 * MARGIN
    plot_height = chart_height - 2 * MARGIN
    
    # 计算数值范围
    all_values = [value for metric in metrics for value in metric["values"]]
    min_val = min(all_values) * 0.95
    max_val = max(all_values) * 1.05
    
    # 创建SVG头部
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{chart_width}" height="{chart_height}" viewBox="0 0 {chart_width} {chart_height}">',
        '<style>',
        '  text {',
        f'    font-family: {FONT_FAMILY};',
        '    font-size: 12px;',
        '    fill: #333;',
        '  }',
        '  .axis-label { font-size: 14px; }',
        '  .title { font-size: 18px; font-weight: bold; }',
        '  .legend-item { font-size: 11px; }',
        '  .legend-box { fill: white; fill-opacity: 0.85; stroke: #cccccc; stroke-width: 1; rx: 5; }',
        '</style>',
        f'<text x="{chart_width/2}" y="30" text-anchor="middle" class="title">Daily Data Growth Trend</text>',
        f'<text x="{chart_width/2}" y="{chart_height-20}" text-anchor="middle" class="axis-label">Date</text>',
        '<g transform="rotate(-90)">',
        f'<text x="-{chart_height/2}" y="20" text-anchor="middle" class="axis-label">Count</text>',
        '</g>'
    ]
    
    # 绘制背景和网格
    svg.append(f'<rect x="0" y="0" width="{chart_width}" height="{chart_height}" fill="#f8f8f8" />')
    
    # 修正纵轴刻度的关键部分：使用反向计算
    for i in range(0, 6):
        # 计算网格线位置（从底部开始）
        y = chart_height - MARGIN - i * (plot_height / 5)
        
        # 绘制网格线
        svg.append(f'<line x1="{MARGIN}" y1="{y}" x2="{chart_width - MARGIN}" y2="{y}" stroke="{GRID_COLOR}" stroke-width="1" />')
        
        # 修正数值计算：从最小值递增到最大值
        value = min_val + i * ((max_val - min_val) / 5)
        # 格式化数值显示
        if value >= 1000:
            label = f"{value/1000:.1f}k"
        else:
            label = f"{int(value)}"
        svg.append(f'<text x="{MARGIN-10}" y="{y+5}" text-anchor="end">{label}</text>')
    
    # 绘制坐标轴
    svg.append(f'<line x1="{MARGIN}" y1="{MARGIN}" x2="{MARGIN}" y2="{chart_height - MARGIN}" stroke="{AXIS_COLOR}" stroke-width="2" />')
    svg.append(f'<line x1="{MARGIN}" y1="{chart_height - MARGIN}" x2="{chart_width - MARGIN}" y2="{chart_height - MARGIN}" stroke="{AXIS_COLOR}" stroke-width="2" />')
    
    # 绘制数据点和折线
    for idx, metric in enumerate(metrics):
        points = []
        for i, value in enumerate(metric["values"]):
            x = MARGIN + i * (plot_width / (len(dates) - 1))
            # 修正数据点位置计算：使用正向映射
            y = chart_height - MARGIN - (value - min_val) * plot_height / (max_val - min_val)
            points.append((x, y))
            # 绘制数据点
            svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{COLORS[idx]}" />')
        # 绘制折线
        path = f'M {points[0][0]} {points[0][1]}'
        for point in points[1:]:
            path += f' L {point[0]} {point[1]}'
        svg.append(f'<path d="{path}" fill="none" stroke="{COLORS[idx]}" stroke-width="2" />')
    
    # 添加X轴日期标签
    # 使用智能版本：
    add_xaxis_labels_smart(svg, dates, plot_width, chart_height, MARGIN)    
    
    # 添加图例（左上角）
    legend_x = MARGIN + 20
    legend_y = MARGIN + 40
    box_height = len(metrics) * 25 + 35
    svg.append(f'<rect x="{legend_x-10}" y="{legend_y-20}" width="130" height="{box_height}" class="legend-box" />')
    svg.append(f'<text x="{legend_x}" y="{legend_y}" class="legend-item">图例:</text>')
    for i, metric in enumerate(metrics):
        y = legend_y + (i+1)*25
        svg.append(f'<rect x="{legend_x}" y="{y-8}" width="15" height="15" fill="{COLORS[i]}" rx="3" />')
        svg.append(f'<text x="{legend_x+20}" y="{y}" class="legend-item">{metric["name"]}</text>')

    # 底部增加指标数据量的展示
    # 方法一：使用列表推导式
    latest_values = [metric["values"][-1] for metric in metrics]
    for i, metric in enumerate(metrics):
        y = 900
        pos_x = 100 + 100 * i
        val = latest_values[i]
        svg.append(f'<rect x="{pos_x}" y="900" width="15" height="15" fill="{COLORS[i]}" rx="3" />')
        svg.append(f'<text x="{pos_x+15}" y="900" class="legend-item">{metric["name"]}-{val}</text>')
    # <rect x="100" y="990" width="15" height="15" fill="#1f77b4" rx="3" />
    # <text x="115" y="990" class="legend-item">构件聚合数据-10000</text>
    # <rect x="200" y="990" width="15" height="15" fill="#ff7f0e" rx="3" />
    # <text x="215" y="990" class="legend-item">构件基本信息-20000</text>
    # <rect x="300" y="990" width="15" height="15" fill="#2ca02c" rx="3" />
    # <text x="315" y="990" class="legend-item">构件徽标-30000</text>
    # <rect x="400" y="990" width="15" height="15" fill="#d62728" rx="3" />
    # <text x="415" y="990" class="legend-item">构件扩展元数据-40000</text>
    # <rect x="500" y="990" width="15" height="15" fill="#9467bd" rx="3" />
    # <text x="515" y="990" class="legend-item">构件版本信息-50000</text>
    # <rect x="600" y="990" width="15" height="15" fill="#66ffbd" rx="3" />
    # <text x="615" y="990" class="legend-item">数据量偏差-60000</text>

    # 添加时间戳
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    svg.append(f'<text x="{chart_width - MARGIN}" y="{chart_height - 10}" text-anchor="end" font-size="10" fill="#666">生成时间: {timestamp}</text>')
    
    # 结束SVG
    svg.append('</svg>')
    
    return "\n".join(svg)

if __name__ == "__main__":
    main()
