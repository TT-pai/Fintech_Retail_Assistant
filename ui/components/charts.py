"""
图表组件
基于Plotly和Pyecharts的交互式图表
"""
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


def create_candlestick_chart(
    df: pd.DataFrame,
    title: str = "K线图",
    show_volume: bool = True,
    show_ma: bool = True
) -> go.Figure:
    """
    创建K线图
    
    Args:
        df: 包含日期、开盘、收盘、最高、最低、成交量的DataFrame
        title: 图表标题
        show_volume: 是否显示成交量
        show_ma: 是否显示均线
        
    Returns:
        Plotly Figure对象
    """
    # 确保列名正确
    required_cols = ['日期', '开盘', '收盘', '最高', '最低', '成交量']
    for col in required_cols:
        if col not in df.columns:
            # 尝试英文列名
            mapping = {
                '日期': ['Date', 'date'],
                '开盘': ['Open', 'open'],
                '收盘': ['Close', 'close'],
                '最高': ['High', 'high'],
                '最低': ['Low', 'low'],
                '成交量': ['Volume', 'volume']
            }
            for eng in mapping.get(col, []):
                if eng in df.columns:
                    df = df.rename(columns={eng: col})
                    break
    
    if show_volume:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3]
        )
    else:
        fig = make_subplots(rows=1, cols=1)
    
    # K线图
    fig.add_trace(
        go.Candlestick(
            x=df['日期'],
            open=df['开盘'],
            high=df['最高'],
            low=df['最低'],
            close=df['收盘'],
            name="K线",
            increasing_line_color='#00C853',
            decreasing_line_color='#FF5252'
        ),
        row=1, col=1
    )
    
    # 均线
    if show_ma and '收盘' in df.columns:
        close = df['收盘'].astype(float)
        
        ma5 = close.rolling(5).mean()
        ma10 = close.rolling(10).mean()
        ma20 = close.rolling(20).mean()
        
        fig.add_trace(
            go.Scatter(x=df['日期'], y=ma5, name='MA5', line=dict(color='#FFB800', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['日期'], y=ma10, name='MA10', line=dict(color='#0A84FF', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['日期'], y=ma20, name='MA20', line=dict(color='#FF6B6B', width=1)),
            row=1, col=1
        )
    
    # 成交量
    if show_volume and '成交量' in df.columns:
        colors = ['#00C853' if df['收盘'].iloc[i] >= df['开盘'].iloc[i] else '#FF5252'
                  for i in range(len(df))]
        
        fig.add_trace(
            go.Bar(x=df['日期'], y=df['成交量'], name='成交量', marker_color=colors),
            row=2, col=1
        )
    
    fig.update_layout(
        title=title,
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_xaxes(title_text="日期", row=2, col=1)
    fig.update_yaxes(title_text="价格", row=1, col=1)
    if show_volume:
        fig.update_yaxes(title_text="成交量", row=2, col=1)
    
    return fig


def create_line_chart(
    data: Dict[str, List],
    title: str = "折线图",
    x_label: str = "X",
    y_label: str = "Y"
) -> go.Figure:
    """
    创建折线图
    
    Args:
        data: 数据字典，key为系列名，value为数值列表
        title: 图表标题
        x_label: X轴标签
        y_label: Y轴标签
        
    Returns:
        Plotly Figure对象
    """
    fig = go.Figure()
    
    colors = ['#0A84FF', '#FFB800', '#00C853', '#FF5252', '#9C27B0']
    
    for i, (name, values) in enumerate(data.items()):
        fig.add_trace(go.Scatter(
            y=values,
            mode='lines+markers',
            name=name,
            line=dict(color=colors[i % len(colors)])
        ))
    
    fig.update_layout(
        title=title,
        template='plotly_dark',
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=400
    )
    
    return fig


def create_bar_chart(
    categories: List[str],
    values: List[float],
    title: str = "柱状图",
    color: str = '#0A84FF'
) -> go.Figure:
    """
    创建柱状图
    
    Args:
        categories: 类别列表
        values: 数值列表
        title: 图表标题
        color: 柱子颜色
        
    Returns:
        Plotly Figure对象
    """
    fig = go.Figure(data=[
        go.Bar(x=categories, y=values, marker_color=color)
    ])
    
    fig.update_layout(
        title=title,
        template='plotly_dark',
        height=400
    )
    
    return fig


def create_pie_chart(
    labels: List[str],
    values: List[float],
    title: str = "饼图"
) -> go.Figure:
    """
    创建饼图
    
    Args:
        labels: 标签列表
        values: 数值列表
        title: 图表标题
        
    Returns:
        Plotly Figure对象
    """
    fig = go.Figure(data=[
        go.Pie(labels=labels, values=values, hole=0.4)
    ])
    
    fig.update_layout(
        title=title,
        template='plotly_dark',
        height=400
    )
    
    return fig


def create_radar_chart(
    categories: List[str],
    values: List[float],
    title: str = "雷达图"
) -> go.Figure:
    """
    创建雷达图
    
    Args:
        categories: 类别列表
        values: 数值列表
        title: 图表标题
        
    Returns:
        Plotly Figure对象
    """
    fig = go.Figure(data=[
        go.Scatterpolar(
            r=values + [values[0]],  # 闭合
            theta=categories + [categories[0]],
            fill='toself',
            name=title,
            line_color='#0A84FF'
        )
    ])
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, max(values) * 1.2])),
        showlegend=False,
        template='plotly_dark',
        height=400
    )
    
    return fig


def create_gauge_chart(
    value: float,
    title: str = "仪表盘",
    max_value: float = 100,
    thresholds: Dict[str, tuple] = None
) -> go.Figure:
    """
    创建仪表盘图表
    
    Args:
        value: 当前值
        title: 标题
        max_value: 最大值
        thresholds: 阈值配置，如 {"低": (0, 30), "中": (30, 60), "高": (60, 100)}
        
    Returns:
        Plotly Figure对象
    """
    if thresholds is None:
        thresholds = {"低": (0, 30), "中": (30, 60), "高": (60, 100)}
    
    steps = []
    colors = ["#00C853", "#FFB800", "#FF5252"]
    
    for i, (name, (low, high)) in enumerate(thresholds.items()):
        steps.append({
            "range": [low, high],
            "color": colors[i % len(colors)]
        })
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={
            "axis": {"range": [0, max_value]},
            "bar": {"color": "white"},
            "steps": steps,
            "threshold": {
                "line": {"color": "white", "width": 4},
                "thickness": 0.75,
                "value": value
            }
        }
    ))
    
    fig.update_layout(
        template='plotly_dark',
        height=300
    )
    
    return fig
