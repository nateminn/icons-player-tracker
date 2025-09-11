import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Icons Player Demand Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: black;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_csv_data():
    """Load the CSV data from GitHub"""
    try:
        # Load from your GitHub repository
        url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main/ICONS_DASHBOARD_MASTER_20250911.csv"
        df = pd.read_csv(url)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Ensure numeric columns are properly typed
        df['july_2025_volume'] = pd.to_numeric(df['july_2025_volume'], errors='coerce').fillna(0)
        df['has_volume'] = pd.to_numeric(df['has_volume'], errors='coerce').fillna(0)
        
        return df
        
    except Exception as e:
        st.error(f"Unable to load data from GitHub. Error: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_monthly_data():
    """Load data for all three months for trend analysis"""
    monthly_data = {}
    
    # URLs for each month's data - UPDATE THESE WITH YOUR ACTUAL URLS
    urls = {
        'June 2025': "https://raw.githubusercontent.com/nateminn/icons-player-tracker/experimental/ICONS_JUNE_2025.csv",
        'July 2025': "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main/ICONS_DASHBOARD_MASTER_20250911.csv",
        'August 2025': "https://raw.githubusercontent.com/nateminn/icons-player-tracker/experimental/ICONS_AUGUST_2025.csv"
    }
    
    for month, url in urls.items():
        try:
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            
            # Rename the volume column to a standard name
            if 'june_2025_volume' in df.columns:
                df['search_volume'] = pd.to_numeric(df['june_2025_volume'], errors='coerce').fillna(0)
            elif 'july_2025_volume' in df.columns:
                df['search_volume'] = pd.to_numeric(df['july_2025_volume'], errors='coerce').fillna(0)
            elif 'august_2025_volume' in df.columns:
                df['search_volume'] = pd.to_numeric(df['august_2025_volume'], errors='coerce').fillna(0)
            
            df['month'] = month
            monthly_data[month] = df
        except:
            st.warning(f"Could not load data for {month}")
            
    return monthly_data

# Header
st.markdown('<h1 class="main-header">Icons Player Demand Tracker</h1>', unsafe_allow_html=True)
st.markdown("### Global Search Demand Analysis for Football Players - July 2025")

# Load data
with st.spinner('Loading data from GitHub...'):
    df = load_csv_data()
    monthly_data = load_monthly_data()  # Load monthly data for trends

if df.empty:
    st.error("""
    ### ⚠️ Data Loading Error
    
    Could not load the data from GitHub. Please check:
    1. Your internet connection
    2. The GitHub repository is accessible
    3. The CSV file exists at the specified location
    
    **Expected file location:**
    https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main/ICONS_DASHBOARD_MASTER_20250911.csv
    """)
    st.stop()
else:
    st.success(f"✅ Successfully loaded {len(df):,} rows of data")

# Sidebar filters
with st.sidebar:
    st.markdown("## 📊 Dashboard Controls")
    st.markdown("### 🔍 Filters")
    
    # Show data status
    st.info(f"📊 Dataset: {len(df):,} rows")
    st.caption("Data source: GitHub Repository")
    
    # Country filter
    selected_countries = st.multiselect(
        "Select Countries:",
        options=sorted(df['country'].unique()),
        default=sorted(df['country'].unique())  # Select all countries by default
    )
    
    # Player filter
    available_players = sorted(df[df['country'].isin(selected_countries)]['actual_player'].unique())
    selected_players = st.multiselect(
        "Select Players:",
        options=available_players,
        default=available_players  # Show all players by default
    )
    
    # Search type filter
    search_types = sorted(df['search_type'].unique())
    selected_search_types = st.multiselect(
        "Search Types:",
        options=search_types,
        default=search_types
    )
    
    # Merchandise category filter
    merch_categories = sorted(df[df['merch_category'].notna()]['merch_category'].unique())
    selected_merch_categories = st.multiselect(
        "Merchandise Categories:",
        options=merch_categories,
        default=merch_categories
    )
    
    # Volume filter
    if len(df) > 0:
        min_vol = int(df['july_2025_volume'].min())
        max_vol = int(df['july_2025_volume'].max())
        volume_range = st.slider(
            "Search Volume Range:",
            min_value=min_vol,
            max_value=max_vol,
            value=(min_vol, max_vol),  # Full range by default
            step=10
        )
    else:
        volume_range = (0, 1000)
    
    # Only show data with volume
    only_with_volume = st.checkbox("Show only items with search volume", value=True)

# Apply filters
filtered_df = df[
    (df['country'].isin(selected_countries)) &
    (df['actual_player'].isin(selected_players)) &
    (df['search_type'].isin(selected_search_types)) &
    (df['july_2025_volume'] >= volume_range[0]) &
    (df['july_2025_volume'] <= volume_range[1])
]

# Additional filter for merchandise categories
if 'Merchandise' in selected_search_types:
    merch_filter = filtered_df['merch_category'].isin(selected_merch_categories) | filtered_df['search_type'] != 'Merchandise'
    filtered_df = filtered_df[merch_filter]

if only_with_volume:
    filtered_df = filtered_df[filtered_df['has_volume'] == 1]

# Main dashboard
if not filtered_df.empty:
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_volume = filtered_df['july_2025_volume'].sum()
        st.metric(
            "Total Search Volume",
            f"{total_volume:,}",
            delta="July 2025"
        )
    
    with col2:
        unique_players = filtered_df['actual_player'].nunique()
        st.metric(
            "Players Analyzed",
            f"{unique_players}",
            delta=f"of {df['actual_player'].nunique()} total"
        )
    
    with col3:
        avg_volume_per_player = filtered_df.groupby('actual_player')['july_2025_volume'].sum().mean()
        st.metric(
            "Avg Volume per Player",
            f"{avg_volume_per_player:,.0f}",
            delta="Across selected markets"
        )
    
    with col4:
        top_country = filtered_df.groupby('country')['july_2025_volume'].sum().idxmax()
        st.metric(
            "Top Market",
            top_country,
            delta=f"{filtered_df[filtered_df['country'] == top_country]['july_2025_volume'].sum():,} searches"
        )
    
    st.markdown("---")
    
    # Tabs for different views - ADDED TRENDS TAB
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📈 Overview", "🌍 Market Analysis", "👤 Player Details", "📊 Comparisons", "🛍️ Merchandise", "📉 Monthly Trends"])
    
    # [KEEPING ALL EXISTING TABS EXACTLY THE SAME - tab1 through tab5]
    with tab1:
        # Overview charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Top players by total volume
            player_volumes = filtered_df.groupby('actual_player')['july_2025_volume'].sum().nlargest(15).reset_index()
            fig_bar = px.bar(
                player_volumes,
                x='july_2025_volume',
                y='actual_player',
                orientation='h',
                title='Top 15 Players by Total Search Volume',
                color='july_2025_volume',
                color_continuous_scale='Blues',
                labels={'july_2025_volume': 'Search Volume', 'actual_player': 'Player'}
            )
            fig_bar.update_layout(height=500)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Country distribution
            country_dist = filtered_df.groupby('country')['july_2025_volume'].sum().reset_index()
            fig_pie = px.pie(
                country_dist,
                values='july_2025_volume',
                names='country',
                title='Search Volume Distribution by Country'
            )
            fig_pie.update_layout(height=500)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Search Type Breakdown
        st.markdown("### 🔍 Search Type Analysis")
        search_type_data = filtered_df.groupby(['search_type', 'actual_player'])['july_2025_volume'].sum().reset_index()
        search_type_pivot = search_type_data.pivot(index='actual_player', columns='search_type', values='july_2025_volume').fillna(0)
        
        # Get top 20 players by total volume for cleaner visualization
        top_players_list = search_type_pivot.sum(axis=1).nlargest(20).index
        search_type_pivot_top = search_type_pivot.loc[top_players_list]
        
        fig_stacked = px.bar(
            search_type_pivot_top.reset_index(),
            x='actual_player',
            y=search_type_pivot_top.columns.tolist(),
            title='Search Volume by Type (Top 20 Players)',
            labels={'value': 'Search Volume', 'actual_player': 'Player'},
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_stacked.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_stacked, use_container_width=True)
    
    # [CONTINUING WITH OTHER EXISTING TABS - NO CHANGES]
    # ... [tab2, tab3, tab4, tab5 remain exactly the same]
    
    # NEW TAB 6: MONTHLY TRENDS
    with tab6:
        st.markdown("### 📉 Monthly Trend Analysis")
        
        if len(monthly_data) > 0:
            # Combine all monthly data
            all_months_df = []
            for month, data in monthly_data.items():
                if not data.empty:
                    # Apply the same filters to monthly data
                    month_filtered = data[
                        (data['country'].isin(selected_countries)) &
                        (data['actual_player'].isin(selected_players)) &
                        (data['search_type'].isin(selected_search_types))
                    ]
                    all_months_df.append(month_filtered)
            
            if all_months_df:
                combined_df = pd.concat(all_months_df, ignore_index=True)
                
                # Calculate top 20 players by total volume across all months
                top_20_players = combined_df.groupby('actual_player')['search_volume'].sum().nlargest(20).index
                
                # Filter to just top 20 players
                trend_df = combined_df[combined_df['actual_player'].isin(top_20_players)]
                
                # Aggregate by player and month
                trend_summary = trend_df.groupby(['actual_player', 'month'])['search_volume'].sum().reset_index()
                
                # Line chart for trends
                fig_trend = px.line(
                    trend_summary,
                    x='month',
                    y='search_volume',
                    color='actual_player',
                    title='Top 20 Players - Search Volume Trends (June-August 2025)',
                    labels={'search_volume': 'Total Search Volume', 'month': 'Month'},
                    markers=True,
                    height=600
                )
                
                # Update x-axis to show months in order
                fig_trend.update_xaxes(categoryorder='array', categoryarray=['June 2025', 'July 2025', 'August 2025'])
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Month-over-month growth analysis
                col1, col2 = st.columns(2)
                
                with col1:
                    # Calculate growth rates
                    growth_data = []
                    for player in top_20_players:
                        player_data = trend_summary[trend_summary['actual_player'] == player].sort_values('month')
                        if len(player_data) >= 2:
                            june_vol = player_data[player_data['month'] == 'June 2025']['search_volume'].values
                            july_vol = player_data[player_data['month'] == 'July 2025']['search_volume'].values
                            august_vol = player_data[player_data['month'] == 'August 2025']['search_volume'].values
                            
                            if len(july_vol) > 0 and len(june_vol) > 0 and june_vol[0] > 0:
                                june_july_growth = ((july_vol[0] - june_vol[0]) / june_vol[0]) * 100
                            else:
                                june_july_growth = 0
                                
                            if len(august_vol) > 0 and len(july_vol) > 0 and july_vol[0] > 0:
                                july_august_growth = ((august_vol[0] - july_vol[0]) / july_vol[0]) * 100
                            else:
                                july_august_growth = 0
                            
                            growth_data.append({
                                'Player': player,
                                'Jun-Jul Growth %': june_july_growth,
                                'Jul-Aug Growth %': july_august_growth,
                                'Avg Growth %': (june_july_growth + july_august_growth) / 2
                            })
                    
                    if growth_data:
                        growth_df = pd.DataFrame(growth_data).sort_values('Avg Growth %', ascending=False).head(10)
                        
                        fig_growth = px.bar(
                            growth_df,
                            x='Player',
                            y=['Jun-Jul Growth %', 'Jul-Aug Growth %'],
                            title='Top 10 Players by Growth Rate',
                            labels={'value': 'Growth %', 'variable': 'Period'},
                            barmode='group',
                            color_discrete_map={'Jun-Jul Growth %': '#3498db', 'Jul-Aug Growth %': '#2ecc71'}
                        )
                        fig_growth.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig_growth, use_container_width=True)
                
                with col2:
                    # Top movers (biggest gainers and losers)
                    if growth_data:
                        growth_df_full = pd.DataFrame(growth_data).sort_values('Avg Growth %', ascending=False)
                        
                        # Create a diverging bar chart for top gainers and losers
                        top_movers = pd.concat([growth_df_full.head(5), growth_df_full.tail(5)])
                        
                        fig_movers = px.bar(
                            top_movers,
                            x='Avg Growth %',
                            y='Player',
                            orientation='h',
                            title='Top Gainers & Losers (Avg % Change)',
                            color='Avg Growth %',
                            color_continuous_scale='RdYlGn',
                            color_continuous_midpoint=0
                        )
                        st.plotly_chart(fig_movers, use_container_width=True)
                
                # Monthly comparison table
                st.markdown("#### 📊 Monthly Volume Comparison")
                
                # Pivot table for better display
                comparison_pivot = trend_summary.pivot(index='actual_player', columns='month', values='search_volume').fillna(0)
                comparison_pivot = comparison_pivot[['June 2025', 'July 2025', 'August 2025']]  # Ensure correct order
                comparison_pivot['Total'] = comparison_pivot.sum(axis=1)
                comparison_pivot = comparison_pivot.sort_values('Total', ascending=False).head(20)
                
                # Format the numbers
                formatted_pivot = comparison_pivot.style.format("{:,.0f}").background_gradient(cmap='Blues')
                st.dataframe(formatted_pivot, use_container_width=True)
                
            else:
                st.warning("No data available for trend analysis with current filters")
        else:
            st.info("Monthly trend data is being loaded. Please ensure June and August data files are uploaded to GitHub.")
    
    # [REST OF THE CODE REMAINS THE SAME - Export functionality, footer, etc.]

else:
    # Empty state when filters return no data
    st.warning("No data matches the current filter criteria. Please adjust your filters.")
    st.info(f"Total dataset contains {len(df):,} rows with {df['actual_player'].nunique()} unique players across {df['country'].nunique()} countries.")

# Footer with data info
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"💾 Data: {len(df):,} total rows")
with col2:
    st.caption(f"👥 Players: {df['actual_player'].nunique()} unique")
with col3:
    st.caption(f"🌍 Markets: {df['country'].nunique()} countries")

st.caption("Icons Player Demand Tracker v2.0 | July 2025 Data | Built with Streamlit")
