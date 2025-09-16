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
        # Load the MERGED CSV with both signed and unsigned players
        url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-2/ICONS_DASHBOARD_MERGED_20250916_103417.csv"
        df = pd.read_csv(url)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Ensure numeric columns are properly typed
        df['july_2025_volume'] = pd.to_numeric(df['july_2025_volume'], errors='coerce').fillna(0)
        df['has_volume'] = pd.to_numeric(df['has_volume'], errors='coerce').fillna(0)
        
        # Ensure status column exists and is properly formatted
        if 'status' not in df.columns:
            # If status column doesn't exist, create it with default value
            df['status'] = 'unsigned'
        else:
            # Clean up status column values
            df['status'] = df['status'].str.strip().str.lower()
            # Standardize values
            df['status'] = df['status'].replace({
                'sign': 'signed',
                'unsign': 'unsigned',
                'signed': 'signed',
                'unsigned': 'unsigned'
            })
            # Fill any NaN values with 'unsigned'
            df['status'] = df['status'].fillna('unsigned')
        
        return df
        
    except Exception as e:
        st.error(f"Unable to load data from GitHub. Error: {str(e)}")
        return pd.DataFrame()

# Header
st.markdown('<h1 class="main-header">Icons Player Demand Tracker</h1>', unsafe_allow_html=True)
st.markdown("### Global Search Demand Analysis for Football Players - July 2025")

# Load data
with st.spinner('Loading data from GitHub...'):
    df = load_csv_data()

if df.empty:
    st.error("""
    ### ⚠️ Data Loading Error
    
    Could not load the data from GitHub. Please check:
    1. Your internet connection
    2. The GitHub repository is accessible
    3. The CSV file exists at the specified location
    
    **Expected file location:**
    https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-2/ICONS_DASHBOARD_MERGED_20250916_103417.csv
    """)
    st.stop()
else:
    # Count unique players and their status
    unique_players_count = df['actual_player'].nunique()
    signed_players = df[df['status'] == 'signed']['actual_player'].nunique()
    unsigned_players = df[df['status'] == 'unsigned']['actual_player'].nunique()
    
    st.success(f"✓ Successfully loaded {len(df):,} rows | {unique_players_count} total players ({signed_players} signed, {unsigned_players} unsigned)")

# Sidebar filters
with st.sidebar:
    st.markdown("## Dashboard Controls")
    st.markdown("### Filters")
    
    # Show data status
    st.info(f"📊 Dataset: {len(df):,} rows")
    st.info(f"👥 Total Players: {unique_players_count}")
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"✅ Signed: {signed_players}")
    with col2:
        st.warning(f"⏳ Unsigned: {unsigned_players}")
    
    st.caption("Data source: GitHub Repository")
    st.markdown("---")
    
    # STATUS FILTER - NEW!
    st.markdown("#### Player Status")
    status_options = ['All', 'Signed', 'Unsigned']
    selected_status = st.selectbox(
        "Filter by Status:",
        options=status_options,
        index=0,  # Default to 'All'
        help="Filter players by their signing status"
    )
    
    # Apply status filter to get relevant players
    if selected_status == 'Signed':
        status_filtered_df = df[df['status'] == 'signed']
    elif selected_status == 'Unsigned':
        status_filtered_df = df[df['status'] == 'unsigned']
    else:
        status_filtered_df = df
    
    st.markdown("---")
    
    # Country filter
    selected_countries = st.multiselect(
        "Select Countries:",
        options=sorted(df['country'].unique()),
        default=sorted(df['country'].unique())  
    )
    
    # Player filter - Updated to default to ALL players and respect status filter
    available_players = sorted(status_filtered_df[status_filtered_df['country'].isin(selected_countries)]['actual_player'].unique())
    
    # DEFAULT TO ALL AVAILABLE PLAYERS
    selected_players = st.multiselect(
        "Select Players:",
        options=available_players,
        default=available_players,  # This now defaults to ALL players (respecting status filter)
        help=f"Showing {len(available_players)} players based on status and country filters"
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
            value=(min_vol, max_vol),
            step=10
        )
    else:
        volume_range = (0, 1000)
    
    # Only show data with volume
    only_with_volume = st.checkbox("Show only items with search volume", value=True)

# Apply filters including the new status filter
filtered_df = df[
    (df['country'].isin(selected_countries)) &
    (df['actual_player'].isin(selected_players)) &
    (df['search_type'].isin(selected_search_types)) &
    (df['july_2025_volume'] >= volume_range[0]) &
    (df['july_2025_volume'] <= volume_range[1])
]

# Apply status filter
if selected_status == 'Signed':
    filtered_df = filtered_df[filtered_df['status'] == 'signed']
elif selected_status == 'Unsigned':
    filtered_df = filtered_df[filtered_df['status'] == 'unsigned']

# Additional filter for merchandise categories
if 'Merchandise' in selected_search_types:
    merch_filter = filtered_df['merch_category'].isin(selected_merch_categories) | filtered_df['search_type'] != 'Merchandise'
    filtered_df = filtered_df[merch_filter]

if only_with_volume:
    filtered_df = filtered_df[filtered_df['has_volume'] == 1]

# Main dashboard
if not filtered_df.empty:
    
    # Key Metrics Row - Updated to show status breakdown
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
        total_available = df['actual_player'].nunique()
        st.metric(
            "Players Analyzed",
            f"{unique_players}",
            delta=f"of {total_available} total"
        )
    
    with col3:
        # Show signed vs unsigned in filtered data
        signed_in_filter = filtered_df[filtered_df['status'] == 'signed']['actual_player'].nunique()
        unsigned_in_filter = filtered_df[filtered_df['status'] == 'unsigned']['actual_player'].nunique()
        st.metric(
            "Player Status",
            f"{signed_in_filter} Signed",
            delta=f"{unsigned_in_filter} Unsigned"
        )
    
    with col4:
        top_country = filtered_df.groupby('country')['july_2025_volume'].sum().idxmax()
        st.metric(
            "Top Market",
            top_country,
            delta=f"{filtered_df[filtered_df['country'] == top_country]['july_2025_volume'].sum():,} searches"
        )
    
    st.markdown("---")
    
    # Tabs for different views - Added Status Analysis tab
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Overview", 
        "🌍 Market Analysis", 
        "👤 Player Details", 
        "📊 Comparisons", 
        "👕 Merchandise",
        "📋 Status Analysis"  # NEW TAB
    ])
    
    with tab1:
        # Overview charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Top players by total volume - color by status
            player_volumes = filtered_df.groupby(['actual_player', 'status'])['july_2025_volume'].sum().reset_index()
            player_volumes = player_volumes.nlargest(15, 'july_2025_volume')
            
            fig_bar = px.bar(
                player_volumes,
                x='july_2025_volume',
                y='actual_player',
                orientation='h',
                title='Top 15 Players by Total Search Volume',
                color='status',
                color_discrete_map={'signed': '#2ecc71', 'unsigned': '#3498db'},
                labels={'july_2025_volume': 'Search Volume', 'actual_player': 'Player', 'status': 'Status'}
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
    
    with tab2:
        # Market Analysis
        st.markdown("### 🌍 Market Deep Dive")
        
        # Create pivot table for heatmap
        pivot_data = filtered_df.groupby(['actual_player', 'country'])['july_2025_volume'].sum().reset_index()
        pivot_table = pivot_data.pivot(index='actual_player', columns='country', values='july_2025_volume').fillna(0)
        
        # Select top players for better visualization
        top_players_for_heatmap = pivot_table.sum(axis=1).nlargest(25).index
        pivot_table_top = pivot_table.loc[top_players_for_heatmap]
        
        fig_heatmap = px.imshow(
            pivot_table_top,
            labels=dict(x="Country", y="Player", color="Search Volume"),
            title="Player Popularity Heatmap by Country (Top 25 Players)",
            aspect="auto",
            color_continuous_scale="Viridis"
        )
        fig_heatmap.update_layout(height=700)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Country comparison
        col1, col2 = st.columns(2)
        
        with col1:
            # Top countries by volume
            country_totals = filtered_df.groupby('country')['july_2025_volume'].sum().nlargest(10).reset_index()
            fig_country = px.bar(
                country_totals,
                x='country',
                y='july_2025_volume',
                title='Top 10 Countries by Total Search Volume',
                color='july_2025_volume',
                color_continuous_scale='Teal',
                labels={'july_2025_volume': 'Total Volume'}
            )
            st.plotly_chart(fig_country, use_container_width=True)
        
        with col2:
            # Average volume per player by country
            country_avg = filtered_df.groupby('country').agg({
                'july_2025_volume': 'sum',
                'actual_player': 'nunique'
            }).reset_index()
            country_avg['avg_per_player'] = country_avg['july_2025_volume'] / country_avg['actual_player']
            country_avg_top = country_avg.nlargest(10, 'avg_per_player')
            
            fig_avg = px.bar(
                country_avg_top,
                x='country',
                y='avg_per_player',
                title='Top 10 Countries by Avg Volume per Player',
                color='avg_per_player',
                color_continuous_scale='Purples',
                labels={'avg_per_player': 'Avg Volume per Player'}
            )
            st.plotly_chart(fig_avg, use_container_width=True)
    
    with tab3:
        # Player Details
        st.markdown("### 👤 Individual Player Analysis")
        
        # Add player status to selection
        player_options = sorted(filtered_df['actual_player'].unique())
        player_status_map = dict(filtered_df[['actual_player', 'status']].drop_duplicates().values)
        
        # Format player names with status indicator
        player_display = [f"{player} ({'✅ Signed' if player_status_map.get(player) == 'signed' else '⏳ Unsigned'})" 
                         for player in player_options]
        
        selected_display = st.selectbox(
            "Select a player to analyze:",
            options=player_display
        )
        
        # Extract actual player name from display
        selected_player = selected_display.split(' (')[0]
        
        player_data = filtered_df[filtered_df['actual_player'] == selected_player]
        player_status = player_status_map.get(selected_player, 'unknown')
        
        # Show player status
        if player_status == 'signed':
            st.success(f"✅ {selected_player} - SIGNED PLAYER")
        else:
            st.info(f"⏳ {selected_player} - UNSIGNED PLAYER")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Searches", f"{player_data['july_2025_volume'].sum():,}")
        with col2:
            st.metric("Countries", f"{player_data['country'].nunique()}")
        with col3:
            st.metric("Name Variations", f"{player_data['name_variation'].nunique()}")
        
        # Player market breakdown
        player_country_data = player_data.groupby('country')['july_2025_volume'].sum().reset_index()
        fig_player = px.bar(
            player_country_data,
            x='country',
            y='july_2025_volume',
            title=f'{selected_player} - Search Volume by Country',
            color='july_2025_volume',
            color_continuous_scale='Blues',
            labels={'july_2025_volume': 'Search Volume'}
        )
        st.plotly_chart(fig_player, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Search type breakdown for player
            player_search_type = player_data.groupby('search_type')['july_2025_volume'].sum().reset_index()
            fig_search = px.pie(
                player_search_type,
                values='july_2025_volume',
                names='search_type',
                title=f'{selected_player} - Search Type Distribution'
            )
            st.plotly_chart(fig_search, use_container_width=True)
        
        with col2:
            # Name variations performance
            name_var_data = player_data.groupby('name_variation')['july_2025_volume'].sum().nlargest(10).reset_index()
            if len(name_var_data) > 0:
                fig_names = px.bar(
                    name_var_data,
                    x='july_2025_volume',
                    y='name_variation',
                    orientation='h',
                    title=f'Top Name Variations - {selected_player}',
                    color='july_2025_volume',
                    color_continuous_scale='Greens'
                )
                st.plotly_chart(fig_names, use_container_width=True)
    
    with tab4:
        # Comparisons
        st.markdown("### 📊 Player Comparisons")
        
        players_to_compare = st.multiselect(
            "Select players to compare (max 10):",
            options=sorted(filtered_df['actual_player'].unique()),
            default=sorted(filtered_df.groupby('actual_player')['july_2025_volume'].sum().nlargest(3).index)
        )
        
        if players_to_compare and len(players_to_compare) <= 10:
            comparison_df = filtered_df[filtered_df['actual_player'].isin(players_to_compare)]
            
            # Grouped bar chart by country
            comparison_summary = comparison_df.groupby(['actual_player', 'country'])['july_2025_volume'].sum().reset_index()
            
            # Select top countries for cleaner visualization
            top_countries_for_comparison = comparison_summary.groupby('country')['july_2025_volume'].sum().nlargest(8).index
            comparison_summary_filtered = comparison_summary[comparison_summary['country'].isin(top_countries_for_comparison)]
            
            fig_comparison = px.bar(
                comparison_summary_filtered,
                x='country',
                y='july_2025_volume',
                color='actual_player',
                title='Player Comparison Across Top Markets',
                barmode='group',
                labels={'july_2025_volume': 'Search Volume'}
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Radar chart comparison
            radar_countries = ['United States', 'United Kingdom', 'Germany', 'France', 'Spain', 'Italy', 'Brazil', 'Mexico']
            available_radar_countries = [c for c in radar_countries if c in comparison_df['country'].unique()]
            
            if len(available_radar_countries) >= 3:
                radar_data = comparison_df[comparison_df['country'].isin(available_radar_countries)]
                radar_pivot = radar_data.pivot_table(
                    values='july_2025_volume',
                    index='actual_player',
                    columns='country',
                    aggfunc='sum',
                    fill_value=0
                )
                
                fig_radar = go.Figure()
                for player in radar_pivot.index:
                    fig_radar.add_trace(go.Scatterpolar(
                        r=radar_pivot.loc[player].values,
                        theta=radar_pivot.columns,
                        fill='toself',
                        name=player
                    ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, radar_pivot.max().max()]
                        )),
                    showlegend=True,
                    title="Market Presence Comparison"
                )
                st.plotly_chart(fig_radar, use_container_width=True)
            
            # Comparison metrics table with status
            st.markdown("#### 📋 Detailed Comparison Metrics")
            comparison_metrics = comparison_df.groupby('actual_player').agg({
                'july_2025_volume': 'sum',
                'country': 'nunique',
                'name_variation': 'nunique',
                'status': 'first'  # Get status for each player
            }).round(0).reset_index()
            comparison_metrics.columns = ['Player', 'Total Volume', 'Countries', 'Name Variations', 'Status']
            comparison_metrics = comparison_metrics.sort_values('Total Volume', ascending=False)
            
            # Format status column
            comparison_metrics['Status'] = comparison_metrics['Status'].apply(
                lambda x: '✅ Signed' if x == 'signed' else '⏳ Unsigned'
            )
            
            st.dataframe(
                comparison_metrics.style.background_gradient(subset=['Total Volume'], cmap='Blues'),
                use_container_width=True
            )
        elif len(players_to_compare) > 10:
            st.warning("Please select maximum 10 players for comparison")
    
    with tab5:
        # Merchandise Analysis
        st.markdown("### 👕 Merchandise Search Analysis")
        
        merch_df = filtered_df[filtered_df['search_type'] == 'Merchandise']
        
        if not merch_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Top merchandise categories
                merch_cat_totals = merch_df.groupby('merch_category')['july_2025_volume'].sum().reset_index()
                fig_merch_cat = px.pie(
                    merch_cat_totals,
                    values='july_2025_volume',
                    names='merch_category',
                    title='Merchandise Search Volume by Category'
                )
                st.plotly_chart(fig_merch_cat, use_container_width=True)
            
            with col2:
                # Top merchandise terms
                merch_terms = merch_df.groupby('merch_term')['july_2025_volume'].sum().nlargest(15).reset_index()
                fig_terms = px.bar(
                    merch_terms,
                    x='july_2025_volume',
                    y='merch_term',
                    orientation='h',
                    title='Top 15 Merchandise Search Terms',
                    color='july_2025_volume',
                    color_continuous_scale='Reds',
                    labels={'july_2025_volume': 'Search Volume', 'merch_term': 'Merchandise Term'}
                )
                st.plotly_chart(fig_terms, use_container_width=True)
            
            # Player merchandise performance - highlight signed vs unsigned
            st.markdown("#### 🏆 Top Players by Merchandise Searches")
            player_merch = merch_df.groupby(['actual_player', 'status'])['july_2025_volume'].sum().reset_index()
            player_merch = player_merch.nlargest(20, 'july_2025_volume')
            
            fig_player_merch = px.bar(
                player_merch,
                x='actual_player',
                y='july_2025_volume',
                title='Top 20 Players - Merchandise Search Volume',
                color='status',
                color_discrete_map={'signed': '#2ecc71', 'unsigned': '#3498db'},
                labels={'july_2025_volume': 'Merchandise Searches', 'actual_player': 'Player', 'status': 'Status'}
            )
            fig_player_merch.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_player_merch, use_container_width=True)
            
            # Merchandise by country
            st.markdown("#### 🌍 Merchandise Searches by Country")
            country_merch = merch_df.groupby(['country', 'merch_category']).agg({
                'july_2025_volume': 'sum'
            }).reset_index()
            
            # Top countries for merchandise
            top_merch_countries = country_merch.groupby('country')['july_2025_volume'].sum().nlargest(10).index
            country_merch_filtered = country_merch[country_merch['country'].isin(top_merch_countries)]
            
            fig_country_merch = px.bar(
                country_merch_filtered,
                x='country',
                y='july_2025_volume',
                color='merch_category',
                title='Merchandise Categories by Country (Top 10 Markets)',
                labels={'july_2025_volume': 'Search Volume'},
                barmode='stack'
            )
            st.plotly_chart(fig_country_merch, use_container_width=True)
            
        else:
            st.info("No merchandise data available for the selected filters")
    
    with tab6:
        # NEW TAB - Status Analysis
        st.markdown("### 📋 Status Analysis - Signed vs Unsigned Players")
        
        # Overall status comparison
        status_summary = filtered_df.groupby('status').agg({
            'actual_player': 'nunique',
            'july_2025_volume': 'sum'
        }).reset_index()
        status_summary.columns = ['Status', 'Player Count', 'Total Volume']
        status_summary['Status'] = status_summary['Status'].apply(
            lambda x: '✅ Signed' if x == 'signed' else '⏳ Unsigned'
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_status_players = px.pie(
                status_summary,
                values='Player Count',
                names='Status',
                title='Player Distribution by Status',
                color_discrete_map={'✅ Signed': '#2ecc71', '⏳ Unsigned': '#3498db'}
            )
            st.plotly_chart(fig_status_players, use_container_width=True)
        
        with col2:
            fig_status_volume = px.pie(
                status_summary,
                values='Total Volume',
                names='Status',
                title='Search Volume by Status',
                color_discrete_map={'✅ Signed': '#2ecc71', '⏳ Unsigned': '#3498db'}
            )
            st.plotly_chart(fig_status_volume, use_container_width=True)
        
        # Top performers by status
        st.markdown("#### Top Performing Players by Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### ✅ Top Signed Players")
            signed_top = filtered_df[filtered_df['status'] == 'signed'].groupby('actual_player')['july_2025_volume'].sum().nlargest(10).reset_index()
            fig_signed = px.bar(
                signed_top,
                x='july_2025_volume',
                y='actual_player',
                orientation='h',
                title='Top 10 Signed Players',
                color_discrete_sequence=['#2ecc71']
            )
            st.plotly_chart(fig_signed, use_container_width=True)
        
        with col2:
            st.markdown("##### ⏳ Top Unsigned Players")
            unsigned_top = filtered_df[filtered_df['status'] == 'unsigned'].groupby('actual_player')['july_2025_volume'].sum().nlargest(10).reset_index()
            fig_unsigned = px.bar(
                unsigned_top,
                x='july_2025_volume',
                y='actual_player',
                orientation='h',
                title='Top 10 Unsigned Players',
                color_discrete_sequence=['#3498db']
            )
            st.plotly_chart(fig_unsigned, use_container_width=True)
        
        # Average metrics comparison
        st.markdown("#### Performance Metrics Comparison")
        
        metrics_comparison = filtered_df.groupby('status').agg({
            'july_2025_volume': 'mean',
            'country': lambda x: filtered_df[filtered_df['status'] == x.iloc[0]]['country'].nunique(),
            'name_variation': lambda x: filtered_df[filtered_df['status'] == x.iloc[0]]['name_variation'].nunique()
        }).round(0).reset_index()
        
        metrics_comparison.columns = ['Status', 'Avg Volume per Entry', 'Countries Covered', 'Name Variations']
        metrics_comparison['Status'] = metrics_comparison['Status'].apply(
            lambda x: '✅ Signed' if x == 'signed' else '⏳ Unsigned'
        )
        
        st.dataframe(
            metrics_comparison.style.background_gradient(subset=['Avg Volume per Entry'], cmap='Greens'),
            use_container_width=True
        )
    
    # Export functionality
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name=f"player_demand_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Summary statistics with status
        summary_data = filtered_df.groupby('actual_player').agg({
            'july_2025_volume': ['sum', 'mean'],
            'country': 'nunique',
            'name_variation': 'nunique',
            'status': 'first'
        }).round(0)
        summary_data.columns = ['Total_Volume', 'Avg_Volume', 'Countries', 'Name_Variations', 'Status']
        summary_csv = summary_data.to_csv()
        
        st.download_button(
            label="📊 Download Player Summary (CSV)",
            data=summary_csv,
            file_name=f"player_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Info about the current filter
        st.info(f"Showing {len(filtered_df):,} rows from {len(df):,} total")

else:
    # Empty state when filters return no data
    st.warning("No data matches the current filter criteria. Please adjust your filters.")
    st.info(f"Total dataset contains {len(df):,} rows with {df['actual_player'].nunique()} unique players across {df['country'].nunique()} countries.")

# Footer with data info
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.caption(f"📊 Data: {len(df):,} total rows")
with col2:
    st.caption(f"👥 Players: {df['actual_player'].nunique()} total")
with col3:
    signed_count = df[df['status'] == 'signed']['actual_player'].nunique()
    st.caption(f"✅ Signed: {signed_count}")
with col4:
    unsigned_count = df[df['status'] == 'unsigned']['actual_player'].nunique()
    st.caption(f"⏳ Unsigned: {unsigned_count}")

st.caption("Icons Player Demand Tracker v2.0 | July 2025 Data | Enhanced with Player Status")
