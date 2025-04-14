import pandas as pd
import plotly.graph_objects as go
from flask import Flask, Markup # Import Flask and Markup

# 日志文件名
log_file = "cpu_usage_bitz.log"
# 移动平均窗口大小
window_size = 10
# 服务器端口
PORT = 8000

# 创建 Flask 应用
app = Flask(__name__)

# 定义根路由
@app.route('/')
def index():
    try:
        # --- 数据读取和处理 --- 
        df = pd.read_csv(log_file, skiprows=1, names=['Timestamp', 'CPU%'], parse_dates=['Timestamp'])
        if df.empty:
            return "<p>错误：日志文件为空或无法解析。</p>"
        
        # 计算移动平均
        df['CPU%_smoothed'] = df['CPU%'].rolling(window=window_size, center=True, min_periods=1).mean()

        # --- Plotly 图表生成 --- 
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Timestamp'], 
            y=df['CPU%'], 
            mode='lines+markers', 
            name='Original CPU%', 
            marker=dict(size=3),
            line=dict(width=1),
            opacity=0.6
        ))
        fig.add_trace(go.Scatter(
            x=df['Timestamp'], 
            y=df['CPU%_smoothed'], 
            mode='lines', 
            name=f'Smoothed CPU% (Window={window_size})',
            line=dict(width=2)
        ))
        fig.update_layout(
            title=f'BITZ Process CPU Usage Over Time ({log_file}) - Refresh page to update',
            xaxis_title='Time',
            yaxis_title='CPU Usage (%)',
            hovermode="x unified",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        # --- 转换为 HTML --- 
        # full_html=True 包含完整的 HTML 结构和必要的 JS
        # include_plotlyjs='cdn' 从 CDN 加载 Plotly.js，减小 HTML 大小
        chart_html = fig.to_html(full_html=True, include_plotlyjs='cdn')
        
        # 使用 Markup 告诉 Flask 这个字符串是安全的 HTML
        return Markup(chart_html)

    except FileNotFoundError:
        return f"<p>错误：找不到日志文件 '{log_file}'。</p>"
    except Exception as e:
        return f"<p>处理日志或生成图表时发生错误：{e}</p>"

# 启动 Flask 开发服务器
if __name__ == '__main__':
    print(f"Flask 服务器正在启动...")
    print(f"请在浏览器中打开: http://localhost:{PORT}/")
    print(f"日志文件 '{log_file}' 将在每次页面刷新时重新读取。")
    print(f"按 Ctrl+C 停止服务器。")
    # debug=True 会在代码更改时自动重启服务器，方便开发
    # host='0.0.0.0' 使服务器可以被局域网内其他设备访问
    app.run(host='0.0.0.0', port=PORT, debug=True)
