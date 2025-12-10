import streamlit as st
import plotly.graph_objects as go
import pandas as pd

CYBERPUNK_CSS = """
    <style>
        .stApp { background-color: #0e1117; }
        .block-container { padding-top: 1rem; padding-bottom: 2rem; }
        div[data-testid="stMetricValue"] { font-family: "Courier New", monospace; color: #00FF00; text-shadow: 0 0 5px #00FF00; }
        div[data-testid="stMetricLabel"] { color: #888; }
        .stDataFrame { border: 1px solid #333; }
        /* Custom scrollbar for cyberpunk feel */
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: #000; }
        ::-webkit-scrollbar-thumb { background: #00FF00; }
    </style>
"""

def render_radar_graph(nodes_dict, max_range_limit):

    node_x, node_y, node_color, node_text, node_size = [], [], [], [], []
    line_x, line_y = [], [] 

    for n in nodes_dict.values():
        node_x.append(n.x)
        node_y.append(n.y)
        dist = (n.x**2 + n.y**2)**0.5
        out_of_range = dist > max_range_limit
        
        if not n.alive:
            status_color = "#333333" 
        elif n.is_compromised:
            status_color = "#FFA500" 
        elif out_of_range:
            status_color = "#FF0000" 
        else:
            status_color = "#00FF00" 

        node_color.append(status_color)
        
        status_txt = "OOR" if out_of_range else ("KIA" if not n.alive else "OK")
        info = f"{n.node_id}<br>Bat: {int(n.battery)}%<br>Stat: {status_txt}"
        node_text.append(info)
        
        sz = 25 if n.is_sending else 15
        node_size.append(sz)

        if n.is_sending and n.alive and not out_of_range:
            line_x.extend([0, n.x, None])
            line_y.extend([0, n.y, None])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=line_x, y=line_y,
        mode='lines',
        line=dict(color='#00FF00', width=1, dash='dot'),
        hoverinfo='skip'
    ))

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[n.node_id for n in nodes_dict.values()],
        textposition="bottom center",
        marker=dict(size=node_size, color=node_color, line=dict(width=2, color='white')),
        hovertext=node_text,
        hoverinfo="text"
    ))

    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode='markers',
        marker=dict(size=40, color='#0000FF', symbol='diamond', line=dict(width=2, color='white')),
        name="HUB",
        hoverinfo='skip'
    ))

    fig.add_shape(
        type="circle",
        xref="x", yref="y",
        x0=-max_range_limit, y0=-max_range_limit,
        x1=max_range_limit, y1=max_range_limit,
        line=dict(color="rgba(255, 0, 0, 0.3)", width=2, dash="dash"),
        fillcolor="rgba(0, 0, 0, 0)",
    )

    axis_limit = max(20, max_range_limit + 5)

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        xaxis=dict(
            showgrid=True, gridcolor='#333', zeroline=False, 
            showticklabels=False, range=[-axis_limit, axis_limit]
        ),
        yaxis=dict(
            showgrid=True, gridcolor='#333', zeroline=False, 
            showticklabels=False, range=[-axis_limit, axis_limit],
            scaleanchor="x", scaleratio=1
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        uirevision='constant' 
    )
    
    return fig

def style_log_dataframe(logs_list):
    if not logs_list:
        return None
        
    df = pd.DataFrame(logs_list)
    
    def _color_status(val):
        color = 'white'
        if val == 'VERIFIED': color = '#00FF00'
        elif val == 'BLOCKED': color = '#FF0000' 
        elif val == 'CRITICAL': color = '#FF4500' 
        elif val == 'REJECTED': color = 'yellow' 
        return f'color: {color}; font-weight: bold;'
    
    return df.style.map(_color_status, subset=['Status'])