import plotly.graph_objects as go

# Create the bar chart
fig = go.Figure()

# Add Call open interest as a bar trace
fig.add_trace(go.Bar(
    x=open_interest_df['strike_price'], 
    y=open_interest_df['Call_open_interest'], 
    name='Call Open Interest',
    marker_color='green'
))

# Add Put open interest as a bar trace
fig.add_trace(go.Bar(
    x=open_interest_df['strike_price'], 
    y=open_interest_df['Put_open_interest'], 
    name='Put Open Interest',
    marker_color='red'
))

# Update layout to limit strike price range and improve readability
fig.update_layout(
    title='Open Interest by Strike Price',
    xaxis_title='Strike Price',
    yaxis_title='Open Interest',
    barmode='group',
    xaxis_tickformat=',',
    legend_title='Option Type',
    xaxis=dict(range=[0, 120000])  # Set x-axis range from 0 to 120k
)

# Show the plot
fig.update_layout(template='plotly_dark', font_color="lightgrey")
fig.show()
