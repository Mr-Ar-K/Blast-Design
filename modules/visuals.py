import plotly.graph_objects as go
import plotly.express as px


def plot_blast_layout(points, title="Blast Hole Layout"):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=points[:, 0],
            y=points[:, 1],
            mode="markers+text",
            marker=dict(size=12, color="firebrick"),
            text=[str(i) for i in range(len(points))],
            textposition="top center",
            name="Holes",
        )
    )
    fig.update_layout(title=title, xaxis_title="X", yaxis_title="Y", template="plotly_white")
    return fig


def plot_3d_layout(points, title="3D Blast Layout"):
    fig = go.Figure()
    z = [0] * len(points)
    fig.add_trace(
        go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=z,
            mode="markers+text",
            marker=dict(size=5, color="royalblue"),
            text=[str(i) for i in range(len(points))],
            textposition="top center",
            name="Holes",
        )
    )
    fig.update_layout(title=title, scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Z"))
    return fig


def plot_fragmentation_curve(sizes_cm, passing_percent, title="Rosin-Rammler Fragmentation Curve"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sizes_cm, y=passing_percent, mode="lines", name="Passing"))
    fig.update_layout(
        title=title,
        xaxis_title="Fragment size (cm)",
        yaxis_title="Percent passing (%)",
        template="plotly_white",
    )
    return fig


def plot_delay_layout(points, delays_ms, title="Delay Timing Map"):
    fig = px.scatter(
        x=points[:, 0],
        y=points[:, 1],
        color=delays_ms,
        color_continuous_scale="Turbo",
        labels={"x": "X", "y": "Y", "color": "Delay (ms)"},
        title=title,
    )
    fig.update_traces(marker=dict(size=14))
    fig.update_layout(template="plotly_white")
    return fig
