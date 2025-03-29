import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class DashboardComponents:
    def __init__(self, colors):
        self.colors = colors

    def render_metric_card(self, title, value, subtitle=None, trend=None, trend_value=None):
        """Render a well-styled metric card with optional trend indicator."""
        trend_html = ""
        if trend and trend_value is not None:
            trend_color = self.colors['success'] if trend == 'up' else self.colors['danger']
            trend_arrow = '▲' if trend == 'up' else '▼'
            trend_html = f'<div style="color: {trend_color}; font-size: 0.9rem;">{trend_arrow} {trend_value}%</div>'
        
        card_html = f'''
            <div style="padding: 15px; background: {self.colors['card']}; border-radius: 8px; text-align: center;">
                <div style="color: {self.colors['subtext']}; font-size: 0.9rem;">{title}</div>
                <div style="color: {self.colors['text']}; font-size: 2rem; font-weight: bold;">{value}</div>
                {f'<div style="color: {self.colors["subtext"]}; font-size: 0.8rem;">{subtitle}</div>' if subtitle else ''}
                {trend_html}
            </div>
        '''
        st.markdown(card_html, unsafe_allow_html=True)

    def create_gauge_chart(self, value, title):
        """Creates a gauge chart for percentage-based metrics."""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': title, 'font': {'size': 20, 'color': self.colors['text']}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': self.colors['primary']},
                'steps': [
                    {'range': [0, 40], 'color': self.colors['danger']},
                    {'range': [40, 70], 'color': self.colors['warning']},
                    {'range': [70, 100], 'color': self.colors['success']}
                ]
            }
        ))
        fig.update_layout(paper_bgcolor=self.colors['card'], height=300, margin=dict(l=20, r=20, t=40, b=20))
        return fig

    def create_trend_chart(self, dates, values, title):
        """Creates a trend line chart."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=values, mode='lines+markers', line=dict(width=3, color=self.colors['info'])))
        fig.update_layout(title=title, paper_bgcolor=self.colors['card'], height=300, margin=dict(l=20, r=20, t=50, b=20))
        return fig

    def create_bar_chart(self, categories, values, title):
        """Creates a bar chart."""
        fig = go.Figure(go.Bar(x=categories, y=values, marker_color=self.colors['primary'], text=values, textposition='auto'))
        fig.update_layout(title=title, paper_bgcolor=self.colors['card'], height=300, margin=dict(l=20, r=20, t=50, b=20))
        return fig

    def create_dual_axis_chart(self, categories, values1, values2, title):
        """Creates a chart with dual y-axes."""
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=categories, y=values1, name="Count", marker_color=self.colors['secondary']), secondary_y=False)
        fig.add_trace(go.Scatter(x=categories, y=values2, name="Score", mode='lines+markers', line=dict(width=3, color=self.colors['warning'])), secondary_y=True)
        fig.update_layout(title=title, paper_bgcolor=self.colors['card'], height=300, margin=dict(l=20, r=20, t=50, b=20))
        return fig
