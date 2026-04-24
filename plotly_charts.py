import plotly.graph_objects as go


def plot_gex_curve(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["strike"],
        y=df["gex"],
        mode="lines",
        name="GEX",
        hovertemplate="Strike: %{x}<br>GEX: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title="Gamma Exposure (GEX)",
        xaxis_title="Strike",
        yaxis_title="GEX",
        hovermode="x unified"
    )

    return fig


def plot_iv_skew(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["strike"],
        y=df["iv"],
        mode="lines+markers",
        name="IV Skew",
        hovertemplate="Strike: %{x}<br>IV: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title="IV Skew",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility",
        hovermode="x unified"
    )

    return fig


def plot_dex_curve(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["strike"],
        y=df["dex"],
        mode="lines",
        name="DEX",
        hovertemplate="Strike: %{x}<br>DEX: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title="Delta Exposure (DEX)",
        xaxis_title="Strike",
        yaxis_title="DEX",
        hovermode="x unified"
    )

    return fig


def plot_volume_sentiment(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["time"],
        y=df["volume_sentiment"],
        mode="lines",
        name="Volume Sentiment",
        hovertemplate="Time: %{x}<br>Sentiment: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title="Volume Sentiment",
        xaxis_title="Time",
        yaxis_title="Sentiment",
        hovermode="x unified"
    )

    return fig


def plot_expected_move_term_structure(df):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["expiry"],
        y=df["expected_move"],
        mode="lines+markers",
        name="Expected Move",
        hovertemplate="Expiry: %{x}<br>Move: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title="Expected Move Term Structure",
        xaxis_title="Expiry",
        yaxis_title="Expected Move",
        hovermode="x unified"
    )

    return fig
