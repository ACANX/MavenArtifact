#!/usr/bin/env python3
# DailyStatisticChart.py

import json
import os
import time
from datetime import datetime, time as dtime, timedelta

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
    allowed_end = dtime(23, 59, 59)

    if not (allowed_start <= current_time <= allowed_end):
        print(f"当前时间 {current_time.strftime('%H:%M:%S')} 不在允许的执行窗口内 (01:20:00 - 12:59:59)")
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
        start_timestamp = time.time()
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
        # 修改下面这一行，加入 abs()
        {"name": "数据量偏差", "values": [abs(d['badge'] - d['aio']) for d in data]}
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


def add_xaxis_labels_smart(svg, parsed_dates, timestamps, min_ts, max_ts, plot_width, chart_height, MARGIN, x_for_ts):
    if not parsed_dates:
        return

    # 数据点较少时，直接显示所有数据日期
    if len(parsed_dates) <= 8:
        selected_dates = list(parsed_dates)
    else:
        # 根据时间跨度生成候选刻度
        span_days = (max_ts - min_ts) / 86400
        candidates = []

        if span_days <= 60:
            # 跨度较短：每7天一个候选
            cur = parsed_dates[0]
            end = parsed_dates[-1]
            while cur <= end:
                candidates.append(cur)
                cur += timedelta(days=7)
        else:
            # 跨度较长：每月1日作为候选
            cur = parsed_dates[0].replace(day=1)
            if cur < parsed_dates[0]:
                if cur.month == 12:
                    cur = cur.replace(year=cur.year + 1, month=1, day=1)
                else:
                    cur = cur.replace(month=cur.month + 1, day=1)

            end = parsed_dates[-1]
            while cur <= end:
                candidates.append(cur)
                if cur.month == 12:
                    cur = cur.replace(year=cur.year + 1, month=1, day=1)
                else:
                    cur = cur.replace(month=cur.month + 1, day=1)

        # 去重、排序，并确保首尾日期在候选中
        candidates.append(parsed_dates[0])
        candidates.append(parsed_dates[-1])
        candidates = sorted(set(candidates))

        # 按像素间距筛选，避免文字重叠
        selected_dates = []
        prev_x = None
        min_pixel_gap = 70

        for dt in candidates:
            x = x_for_ts(dt.timestamp())
            if prev_x is None or abs(x - prev_x) >= min_pixel_gap:
                selected_dates.append(dt)
                prev_x = x

        # 确保首尾日期一定显示
        if selected_dates and selected_dates[0] != parsed_dates[0]:
            selected_dates.insert(0, parsed_dates[0])
        if selected_dates and selected_dates[-1] != parsed_dates[-1]:
            selected_dates.append(parsed_dates[-1])

        selected_dates = sorted(set(selected_dates))

    # 渲染刻度标签
    last_year = None
    y_date = chart_height - MARGIN + 20
    y_year = y_date + 16

    for dt in selected_dates:
        x = x_for_ts(dt.timestamp())
        label = dt.strftime("%m-%d")
        svg.append(f'<text x="{x}" y="{y_date}" text-anchor="middle" font-size="12">{label}</text>')

        # 年份变化时，在 mm-dd 下一行标注年份
        if last_year is None or dt.year != last_year:
            svg.append(f'<text x="{x}" y="{y_year}" text-anchor="middle" font-size="11" fill="#555">{dt.year}</text>')
            last_year = dt.year


def generate_svg_chart(dates, metrics):
    """生成多指标趋势图SVG，x轴按实际时间戳对齐"""
    chart_width = CHART_WIDTH
    chart_height = CHART_HEIGHT
    plot_width = chart_width - 2 * MARGIN
    plot_height = chart_height - 2 * MARGIN

    # 解析日期，得到时间戳
    parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    timestamps = [dt.timestamp() for dt in parsed_dates]
    min_ts = min(timestamps)
    max_ts = max(timestamps)
    ts_range = max_ts - min_ts if max_ts != min_ts else 1.0

    def x_for_ts(ts):
        if max_ts == min_ts:
            return MARGIN + plot_width / 2
        return MARGIN + (ts - min_ts) * plot_width / ts_range

    # 计算数值范围
    all_values = [value for metric in metrics for value in metric["values"]]
    min_val = min(all_values) * 0.95
    max_val = max(all_values) * 1.05
    if max_val == min_val:
        max_val += 1.0

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

    # 纵轴刻度
    for i in range(0, 6):
        y = chart_height - MARGIN - i * (plot_height / 5)
        svg.append(f'<line x1="{MARGIN}" y1="{y}" x2="{chart_width - MARGIN}" y2="{y}" stroke="{GRID_COLOR}" stroke-width="1" />')

        value = min_val + i * ((max_val - min_val) / 5)
        if value >= 1000:
            label = f"{value/1000:.1f}k"
        else:
            label = f"{int(value)}"
        svg.append(f'<text x="{MARGIN-10}" y="{y+5}" text-anchor="end">{label}</text>')

    # 坐标轴
    svg.append(f'<line x1="{MARGIN}" y1="{MARGIN}" x2="{MARGIN}" y2="{chart_height - MARGIN}" stroke="{AXIS_COLOR}" stroke-width="2" />')
    svg.append(f'<line x1="{MARGIN}" y1="{chart_height - MARGIN}" x2="{chart_width - MARGIN}" y2="{chart_height - MARGIN}" stroke="{AXIS_COLOR}" stroke-width="2" />')

    # 绘制数据点和折线（按时间戳定位，并处理数据中断）
    MAX_GAP_SECONDS = 7 * 86400  # 7天，根据数据采集频率调整

    for idx, metric in enumerate(metrics):
        segments = []
        current_segment = []
        prev_ts = None

        for ts, value in zip(timestamps, metric["values"]):
            x = x_for_ts(ts)
            y = chart_height - MARGIN - (value - min_val) * plot_height / (max_val - min_val)

            if prev_ts is not None and (ts - prev_ts) > MAX_GAP_SECONDS:
                if current_segment:
                    segments.append(current_segment)
                current_segment = []

            current_segment.append((x, y))
            svg.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{COLORS[idx]}" />')
            prev_ts = ts

        if current_segment:
            segments.append(current_segment)

        for segment in segments:
            if len(segment) >= 2:
                path = f'M {segment[0][0]} {segment[0][1]}'
                for point in segment[1:]:
                    path += f' L {point[0]} {point[1]}'
                svg.append(f'<path d="{path}" fill="none" stroke="{COLORS[idx]}" stroke-width="2" />')

    # 添加X轴日期标签（按时间戳对齐）
    add_xaxis_labels_smart(
        svg,
        parsed_dates,
        timestamps,
        min_ts,
        max_ts,
        plot_width,
        chart_height,
        MARGIN,
        x_for_ts
    )

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
    latest_values = [metric["values"][-1] for metric in metrics]
    for i, metric in enumerate(metrics):
        pos_x = 100 + 200 * i
        val = latest_values[i]
        svg.append(f'<rect x="{pos_x}" y="980" width="15" height="15" fill="{COLORS[i]}" rx="3" />')
        svg.append(f'<text x="{pos_x + 25}" y="990" class="legend-item">{val}</text>')

    # 添加时间戳
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    svg.append(f'<text x="{chart_width - MARGIN}" y="{chart_height - 10}" text-anchor="end" font-size="11" fill="#666">生成时间: {timestamp}</text>')

    # 结束SVG
    svg.append('</svg>')

    return "\n".join(svg)


if __name__ == "__main__":
    main()
