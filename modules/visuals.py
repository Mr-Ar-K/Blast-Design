import plotly.graph_objects as go


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
