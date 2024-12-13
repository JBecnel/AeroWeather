import streamlit as st
import plotly.express as px
from utils.data_processor import load_sample_data, process_delay_data

def delay_patterns_page():
    st.title("Flight Delay Patterns")
    
    # Load and process data
    df = load_sample_data()
    df = process_delay_data(df)
    

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        selected_airlines = st.multiselect(
            "Select Airlines",
            options=df['airline'].unique(),
            default=df['airline'].unique()
        )
    
    categories = [x for x in df['delay_category'].unique() if str(x) != 'nan' ]
    #print(categories)
    with col2:
        delay_categories = st.multiselect(
            "Delay Categories",
            options=categories,
            default=categories
        )
    
    # Filter data
    filtered_df = df[
        (df['airline'].isin(selected_airlines)) &
        (df['delay_category'].isin(delay_categories))
    ]
    
    # Visualizations
    st.subheader("Delay Distribution by Airline")
    fig = px.violin(
        filtered_df,
        x='airline',
        y='delay_minutes',
        color='airline',
        box=True,
        template='plotly_dark'
    )
    fig.update_layout(
        xaxis_title = "Airline",
        yaxis_title = "Delay Minutes",        
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Delay categories breakdown
    st.subheader("Delay Distribution by Airline and Category")
    
    # Aggregate data for chart
    agg_df = filtered_df.groupby(['airline', 'delay_category'], observed=True)['delay_minutes'].count().reset_index()
    
    agg_df.rename(columns={'delay_minutes' : 'freq'}, inplace=True)
    agg_df['percent'] = 100*agg_df['freq'] / agg_df.groupby(['airline'])['freq'].transform('sum')
    
    # Create grouped bar 
    fig = px.bar(
        agg_df,
        x='airline',
        y='percent',
        color='delay_category',
        barmode='group',
        template='plotly_dark',        
    )
    fig.update_layout(
        xaxis_title='Airline',
        yaxis_title='Percent of Each Delay Type',
        legend_title='Delay Category',
        margin=dict(t=50, l=25, r=25, b=25)
    )
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    delay_patterns_page()
