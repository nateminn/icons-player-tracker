import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import requests
import json

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
            padding: 1rem -3;
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
        # CORRECTED URL - using main-2.0 branch
        url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-3/ICONS_DASHBOARD_MERGED_20250916_103417.csv"
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_player_details():
    """Load player details from GitHub"""
    try:
        # CORRECTED URL - using main-2.0 instead of main-2
        url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-3/player_essential_data_json.json"
        response = requests.get(url)
        data = response.json()
        
        # Create a dictionary for quick lookup
        player_dict = {player['name']: player for player in data['players']}
        
        return player_dict
        
    except Exception as e:
        st.warning(f"Could not load player details: {str(e)}")
        return {}

# Header
st.markdown('<h1 class="main-header">Icons Player Demand Tracker</h1>', unsafe_allow_html=True)
st.markdown("### Global Search Demand Analysis for Football Players - July 2025")

# Load data
with st.spinner('Loading data from GitHub...'):
    df = load_csv_data()
    player_dict = load_player_details()

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
    
    # In the sidebar section (replace lines 161-168)
    
    # Search type filter
    search_types = sorted(df['search_type'].unique())
    selected_search_types = st.multiselect(
        "Search Types:",
        options=search_types,
        default=search_types
    )
    
    # Merchandise category filter - ONLY show when Merchandise is selected
    if 'Merchandise' in selected_search_types:
        merch_categories = sorted(df[df['merch_category'].notna()]['merch_category'].unique())
        selected_merch_categories = st.multiselect(
            "Merchandise Categories:",
            options=merch_categories,
            default=merch_categories,
            help="Filter merchandise searches by category"
        )
    else:
        # If Merchandise not selected, default to all categories (for when it gets re-selected)
        merch_categories = sorted(df[df['merch_category'].notna()]['merch_category'].unique())
        selected_merch_categories = merch_categories  # Set to all by default
        
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


# Apply merchandise category filter
if 'Merchandise' in selected_search_types and selected_merch_categories:
    # For merchandise rows, only keep those with selected categories
    # For non-merchandise rows, keep them all
    merch_filter = (
        (filtered_df['search_type'] != 'Merchandise') |  # Keep all non-merchandise
        (filtered_df['merch_category'].isin(selected_merch_categories))  # Keep only selected merch categories
    )
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
    
          # Add this to the tab creation section (replace the 6 tabs with 6, removing Status Analysis)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Overview", 
        "🌍 Market Analysis", 
        "👤 Player Details", 
        "📊 Comparisons", 
        "👕 Merchandise",
        "🎯 Opportunity Scores"  # NEW TAB
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
        st.markdown("### Search Type Analysis")
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
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_stacked.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_stacked, use_container_width=True)
    
    with tab2:
        # Market Analysis
        st.markdown("### Market Deep Dive")
        
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
        # Player Details - ENHANCED WITH ALL AVAILABLE DATA
        st.markdown("### **Individual Player Analysis**")
        
        # Get unique players sorted by total volume
        player_volumes_for_select = filtered_df.groupby('actual_player')['july_2025_volume'].sum().sort_values(ascending=False)
        player_options = player_volumes_for_select.index.tolist()
        
        # Simple player selection without status in dropdown
        selected_player = st.selectbox(
            "Select a player to analyze:",
            options=player_options
        )
        
        player_data = filtered_df[filtered_df['actual_player'] == selected_player]
        player_status_map = dict(filtered_df[['actual_player', 'status']].drop_duplicates().values)
        player_status = player_status_map.get(selected_player, 'unknown')
        
        # Get additional player info if available
        player_info = player_dict.get(selected_player, {}) if player_dict else {}
        
        st.markdown("---")
        
        # PLAYER PROFILE SECTION - ENHANCED
        st.markdown("#### **Player Profile**")
        
        # First row - Basic info
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**Sport**")
            st.info(player_info.get('sport', 'N/A'))
        
        with col2:
            st.markdown("**Current Team**")
            st.info(player_info.get('team', 'N/A'))
        
        with col3:
            st.markdown("**Position**")
            st.info(player_info.get('position', 'N/A'))
        
        with col4:
            st.markdown("**Age**")
            age = player_info.get('age', 'N/A')
            if isinstance(age, (int, float)):
                st.info(f"{age} years")
            else:
                st.info(str(age))
        
        # Second row - Additional details
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**Nationality**")
            st.success(player_info.get('nationality', 'N/A'))
        
        with col2:
            st.markdown("**Current League**")
            st.success(player_info.get('league', 'N/A'))
        
        with col3:
            st.markdown("**Status**")
            # Determine status from team info
            team = player_info.get('team', '')
            if 'Retired' in team or 'Deceased' in team:
                st.warning(team)
            elif team == 'Active':
                st.success("Active")
            elif team == 'Free Agent':
                st.warning("Free Agent")
            else:
                st.success("Active Player")
        
        with col4:
            st.markdown("**Instagram Followers**")
            followers = player_info.get('instagram_followers', 'N/A')
            if followers != 'N/A':
                st.info(followers)
            else:
                st.info("Not Available")
        
        # Career Journey Section
        st.markdown("---")
        st.markdown("#### **Career Journey**")
        
        st.markdown("**Full Career Path**")
        if player_info and player_info.get('previous_teams'):
            previous_teams = player_info.get('previous_teams', [])
            current_team = player_info.get('team', '')
            
            # Build career path
            if previous_teams:
                career_path = " → ".join(previous_teams)
                if current_team and current_team not in ['Retired', 'N/A'] and 'Deceased' not in current_team:
                    career_path = career_path + " → " + current_team
            else:
                career_path = current_team if current_team else "No career history available"
            
            st.success(career_path)
        else:
            st.success("Career history not available")
        
        # Achievements Section - Simplified
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("**Achievements & Honours**")
        
        with col2:
            if player_info and player_info.get('major_trophies'):
                trophies = player_info.get('major_trophies', [])
                
                if trophies and trophies != ['N/A']:
                    # Display as bullet points in a single info box
                    trophy_list = " • ".join(trophies)
                    st.info(trophy_list)
                else:
                    st.info("No major trophies recorded")
            else:
                st.info("Trophy information not available")
        
        st.markdown("---")
        
        # SEARCH PERFORMANCE METRICS - Original section continues
        st.markdown("#### **Search Performance Metrics**")
        
        # Calculate metrics
        total_searches = player_data['july_2025_volume'].sum()
        countries = player_data['country'].nunique()
        name_variations = player_data['name_variation'].nunique()
        merch_searches = player_data[player_data['search_type'] == 'Merchandise']['july_2025_volume'].sum()
        merch_pct = (merch_searches/total_searches*100) if total_searches > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Searches",
                value=f"{total_searches:,}"
            )
        
        with col2:
            st.metric(
                label="Countries",
                value=f"{countries}"
            )
        
        with col3:
            st.metric(
                label="Name Variations",
                value=f"{name_variations}"
            )
        
        with col4:
            st.metric(
                label="Merch Interest",
                value=f"{merch_pct:.1f}%"
            )
        
        st.markdown("---")
        
        # ADDITIONAL METRICS
        st.markdown("#### **Market Distribution**")
        
        # Top markets info
        player_country_data = player_data.groupby('country')['july_2025_volume'].sum().sort_values(ascending=False).reset_index()
        
        if not player_country_data.empty:
            # Show top 3 markets
            col1, col2, col3 = st.columns(3)
            
            for i, col in enumerate([col1, col2, col3]):
                if i < len(player_country_data):
                    with col:
                        country = player_country_data.iloc[i]['country']
                        volume = player_country_data.iloc[i]['july_2025_volume']
                        percentage = (volume / total_searches * 100) if total_searches > 0 else 0
                        st.metric(
                            f"#{i+1} {country}",
                            f"{volume:,}",
                            f"{percentage:.1f}% of total"
                        )
        
        st.markdown("---")
        
        # VISUALIZATIONS
        st.markdown("#### **Search Analysis**")
        
        # Market breakdown bar chart
        fig_player = px.bar(
            player_country_data,
            x='country',
            y='july_2025_volume',
            title=f'Search Volume by Country - {selected_player}',
            color='july_2025_volume',
            color_continuous_scale='Blues',
            labels={'july_2025_volume': 'Search Volume'},
            height=400
        )
        st.plotly_chart(fig_player, use_container_width=True)
        
        # Two column layout for pie charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Search type breakdown
            player_search_type = player_data.groupby('search_type')['july_2025_volume'].sum().reset_index()
            fig_search = px.pie(
                player_search_type,
                values='july_2025_volume',
                names='search_type',
                title='Search Type Distribution',
                height=350
            )
            st.plotly_chart(fig_search, use_container_width=True)
        
        with col2:
            # Name variations breakdown
            name_var_data = player_data.groupby('name_variation')['july_2025_volume'].sum().reset_index()
            if len(name_var_data) > 0:
                fig_names = px.pie(
                    name_var_data,
                    values='july_2025_volume',
                    names='name_variation',
                    title='Search by Name Variation',
                    height=350
                )
                st.plotly_chart(fig_names, use_container_width=True)
            else:
                st.info("No name variation data available")
        
        # DETAILED DATA TABLE
        st.markdown("---")
        st.markdown("#### **Detailed Search Data**")
        
        # Create summary table
        detailed_data = player_data.groupby(['country', 'search_type']).agg({
            'july_2025_volume': 'sum'
        }).reset_index()
        
        # Pivot for better display
        if not detailed_data.empty:
            pivot_table = detailed_data.pivot(
                index='country',
                columns='search_type',
                values='july_2025_volume'
            ).fillna(0).astype(int)
            
            # Add total column
            pivot_table['Total'] = pivot_table.sum(axis=1)
            
            # Sort by total
            pivot_table = pivot_table.sort_values('Total', ascending=False)
            
            # Format the table
            st.dataframe(
                pivot_table.style.format("{:,.0f}").background_gradient(subset=['Total'], cmap='Blues'),
                use_container_width=True
            )
    with tab4:
        # Comparisons
        st.markdown("### Player Comparisons")
        
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
            st.markdown("#### Detailed Comparison Metrics")
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
                lambda x: ' Signed' if x == 'signed' else ' Unsigned'
            )
            
            st.dataframe(
                comparison_metrics.style.background_gradient(subset=['Total Volume'], cmap='Blues'),
                use_container_width=True
            )
        elif len(players_to_compare) > 10:
            st.warning("Please select maximum 10 players for comparison")
        
     with tab5:
            # Merchandise Analysis
            st.markdown("###  Merchandise Search Analysis")
            
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
        st.markdown("### 🎯 Player Opportunity Score Analysis")
        
        # Scoring key information
        with st.expander("📊 Scoring Methodology", expanded=False):
            st.markdown("""
            **SCORING WEIGHTS:**
            - Google Search Demand: 25%
            - Instagram Followers: 15%
            - Current Team: 10%
            - Previous Teams: 10%
            - Nationality: 8%
            - Major Trophies: 15%
            - Sport: 5%
            - Position: 5%
            - Age/Status: 7%
            
            **POINT SCALES:**
            - **Instagram:** >300M=10pts | 100-300M=8pts | 50-100M=6pts | 10-50M=4pts | 1-10M=2pts | N/A=0pts
            - **Teams:** Elite (Real Madrid, Barcelona, Man United, etc.)=10pts | Top=7pts | Good=5pts | Retired=3pts
            - **Trophies:** World Cup=10pts | Champions League=9pts | Ballon d'Or=10pts | Continental=6pts
            - **Nationality:** Top (Brazil, Argentina, France, Germany, Spain)=10pts | Good=8pts | Other=5pts
            """)
        
        # Function to calculate opportunity score
        def calculate_opportunity_score(row, google_search_vol=None):
            score = 0
            
            # 1. Google Search (25%) - if available
            if google_search_vol and google_search_vol > 0:
                # Normalize search volume (assuming max ~10M searches)
                search_points = min(10, google_search_vol / 1000000)
                score += search_points * 0.25
            
            # 2. Instagram Followers (15%)
            instagram = row.get('instagram_followers', 'N/A')
            instagram_points = 0
            if instagram != 'N/A' and instagram:
                try:
                    num = float(instagram.replace('M', ''))
                    if num > 300: instagram_points = 10
                    elif num > 100: instagram_points = 8
                    elif num > 50: instagram_points = 6
                    elif num > 10: instagram_points = 4
                    elif num > 1: instagram_points = 2
                    else: instagram_points = 1
                except:
                    instagram_points = 0
            score += instagram_points * 0.15
            
            # 3. Current Team (10%)
            elite_clubs = ["Real Madrid", "Barcelona", "Manchester United", "Manchester City",
                          "Liverpool", "Bayern Munich", "PSG", "Chelsea", "Arsenal", "Inter Miami"]
            top_clubs = ["Tottenham", "Inter Milan", "AC Milan", "Juventus", "Atletico Madrid",
                        "Borussia Dortmund", "Roma", "Napoli", "Al Nassr", "Al Hilal"]
            
            team = row.get('team', '')
            team_points = 0
            if any(club in str(team) for club in elite_clubs):
                team_points = 10
            elif any(club in str(team) for club in top_clubs):
                team_points = 7
            elif "Retired" in str(team):
                team_points = 3
            else:
                team_points = 5
            score += team_points * 0.10
            
            # 4. Previous Teams (10%)
            previous_teams = row.get('previous_teams', [])
            prev_team_points = 0
            if previous_teams:
                for team in previous_teams:
                    if any(club in str(team) for club in elite_clubs):
                        prev_team_points += 2
                    elif any(club in str(team) for club in top_clubs):
                        prev_team_points += 1
                prev_team_points = min(10, prev_team_points)
            score += prev_team_points * 0.10
            
            # 5. Nationality (8%)
            top_nations = ["Brazil", "Argentina", "France", "Germany", "Spain"]
            good_nations = ["England", "Italy", "Portugal", "Netherlands", "Belgium", "Croatia"]
            
            nationality = row.get('nationality', '')
            nation_points = 0
            if nationality in top_nations:
                nation_points = 10
            elif nationality in good_nations:
                nation_points = 8
            else:
                nation_points = 5
            score += nation_points * 0.08
            
            # 6. Major Trophies (15%)
            trophies = row.get('major_trophies', [])
            trophy_points = 0
            if trophies and trophies != ['N/A']:
                for trophy in trophies:
                    if "World Cup" in str(trophy):
                        trophy_points += 10
                    if "Champions League" in str(trophy):
                        trophy_points += 9
                    if "Ballon d'Or" in str(trophy):
                        trophy_points += 10
                    if any(x in str(trophy) for x in ["Euros", "Copa America"]):
                        trophy_points += 6
                    if "NBA Championship" in str(trophy):
                        trophy_points += 8
                trophy_points = min(10, trophy_points / 2)  # Normalize
            score += trophy_points * 0.15
            
            # 7. Sport (5%)
            sport = row.get('sport', '')
            sport_points = 0
            if sport == "Football":
                sport_points = 10
            elif sport == "Basketball":
                sport_points = 7
            elif sport == "Tennis":
                sport_points = 5
            elif sport == "Boxing":
                sport_points = 4
            else:
                sport_points = 3
            score += sport_points * 0.05
            
            # 8. Position (5%)
            position = row.get('position', '')
            position_points = 5
            if row.get('sport') == "Football":
                if any(pos in str(position) for pos in ["ST", "CF", "RW", "LW"]):
                    position_points = 10
                elif any(pos in str(position) for pos in ["AM", "CAM"]):
                    position_points = 8
                elif "CM" in str(position):
                    position_points = 6
                elif any(pos in str(position) for pos in ["CB", "RB", "LB"]):
                    position_points = 4
                elif "GK" in str(position):
                    position_points = 3
            score += position_points * 0.05
            
            # 9. Age/Status (7%)
            age = row.get('age', 0)
            age_points = 0
            if isinstance(age, (int, float)):
                if 24 <= age <= 32:
                    age_points = 10
                elif 18 <= age <= 23:
                    age_points = 8
                elif 33 <= age <= 38:
                    age_points = 6
                else:
                    age_points = 3
            elif "Deceased" in str(age):
                age_points = 4
            score += age_points * 0.07
            
            return round(score, 2)
        
        # Load ALL players from the JSON file directly
        try:
            # Load all players from the complete dataset
            all_players_df = pd.DataFrame(player_dict.values()) if player_dict else pd.DataFrame()
            
            if not all_players_df.empty:
                # PROPERLY MAP GOOGLE SEARCH VOLUME DATA
                google_volumes_map = {}
                
                if google_search_df is not None:
                    # Create a comprehensive name mapping
                    for _, row in google_search_df.iterrows():
                        csv_player_name = row['Player Name'].strip()
                        volume = row['Google Search Volume']
                        
                        if volume != 'N/A' and pd.notna(volume):
                            try:
                                # Convert volume to number
                                volume_num = float(str(volume).replace(',', ''))
                                google_volumes_map[csv_player_name] = volume_num
                            except:
                                pass
                
                # Function to find Google volume for a player
                def find_google_volume(player_name, player_info):
                    # Try direct match first
                    if player_name in google_volumes_map:
                        return google_volumes_map[player_name]
                    
                    # Try all name variants from total_names
                    total_names = player_info.get('total_names', [player_name])
                    for variant in total_names:
                        if variant in google_volumes_map:
                            return google_volumes_map[variant]
                    
                    # No match found
                    return 0
                
                # Apply Google volumes to all players
                all_players_df['google_search_volume'] = all_players_df.apply(
                    lambda row: find_google_volume(row['name'], row.to_dict()),
                    axis=1
                )
                
                # Calculate opportunity scores for ALL players
                all_players_df['opportunity_score'] = all_players_df.apply(
                    lambda row: calculate_opportunity_score(row.to_dict(), row['google_search_volume']),
                    axis=1
                )
                
                # Sort by opportunity score
                all_players_df = all_players_df.sort_values('opportunity_score', ascending=False)
                
                # Add rank
                all_players_df['rank'] = range(1, len(all_players_df) + 1)
                
                # Display summary statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Players", len(all_players_df))
                with col2:
                    avg_score = all_players_df['opportunity_score'].mean()
                    st.metric("Avg Opportunity Score", f"{avg_score:.2f}")
                with col3:
                    complete_data = all_players_df[all_players_df['instagram_followers'] != 'N/A'].shape[0]
                    st.metric("Players with Instagram Data", f"{complete_data}/{len(all_players_df)}")
                with col4:
                    with_search = all_players_df[all_players_df['google_search_volume'] > 0].shape[0]
                    st.metric("Players with Google Search Data", f"{with_search}/{len(all_players_df)}")
                
                st.markdown("---")
                
                # Filters for the table
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sport_filter = st.multiselect(
                        "Filter by Sport:",
                        options=['All'] + sorted(all_players_df['sport'].unique()),
                        default=['All']
                    )
                
                with col2:
                    min_score, max_score = st.slider(
                        "Opportunity Score Range:",
                        min_value=0.0,
                        max_value=10.0,
                        value=(0.0, 10.0),
                        step=0.1
                    )
                
                with col3:
                    search_data_filter = st.selectbox(
                        "Search Data Filter:",
                        options=["All Players", "With Google Search Data Only", "Without Google Search Data Only"]
                    )
                
                # Apply filters
                filtered_players = all_players_df.copy()
                
                if 'All' not in sport_filter:
                    filtered_players = filtered_players[filtered_players['sport'].isin(sport_filter)]
                
                filtered_players = filtered_players[
                    (filtered_players['opportunity_score'] >= min_score) &
                    (filtered_players['opportunity_score'] <= max_score)
                ]
                
                if search_data_filter == "With Google Search Data Only":
                    filtered_players = filtered_players[filtered_players['google_search_volume'] > 0]
                elif search_data_filter == "Without Google Search Data Only":
                    filtered_players = filtered_players[filtered_players['google_search_volume'] == 0]
                
                # Prepare display dataframe
                display_cols = [
                    'rank', 'name', 'opportunity_score', 'google_search_volume',
                    'instagram_followers', 'team', 'nationality', 'position',
                    'age', 'sport', 'major_trophies'
                ]
                
                display_df = filtered_players[display_cols].copy()
                
                # Format columns for display
                display_df.columns = [
                    'Rank', 'Player Name', 'Opportunity Score', 'Google Search Volume',
                    'Instagram Followers', 'Current Team', 'Nationality', 'Position',
                    'Age', 'Sport', 'Major Trophies'
                ]
                
                # Format Google search volume - show "N/A" for 0 values
                display_df['Google Search Volume'] = display_df['Google Search Volume'].apply(
                    lambda x: f"{int(x):,}" if x > 0 else "N/A"
                )
                
                # Format trophies (show count instead of full list)
                display_df['Major Trophies'] = display_df['Major Trophies'].apply(
                    lambda x: f"{len(x)} trophies" if isinstance(x, list) and x != ['N/A'] else "None"
                )
                
                # Display the table
                st.markdown(f"### Player Opportunity Scores Table ({len(display_df)} players)")
                
                # Use st.dataframe for better formatting
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Opportunity Score": st.column_config.NumberColumn(
                            "Opportunity Score",
                            help="Combined score from all metrics (0-10)",
                            format="%.2f",
                        ),
                        "Rank": st.column_config.NumberColumn(
                            "Rank",
                            help="Ranking based on opportunity score",
                            format="%d",
                        ),
                    }
                )
                
                # Top 10 Players Highlight
                st.markdown("---")
                st.markdown("### 🏆 Top 10 Players by Opportunity Score")
                
                top_10 = display_df.head(10)[['Rank', 'Player Name', 'Opportunity Score', 'Google Search Volume', 'Instagram Followers', 'Current Team']]
                st.table(top_10)
                
                # Export functionality
                st.markdown("---")
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Opportunity Scores (CSV)",
                    data=csv,
                    file_name=f"player_opportunity_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
            else:
                st.error("No player data found. Please check that the JSON file is loaded correctly.")
        
        except Exception as e:
            st.error(f"Error loading player data: {str(e)}")
            st.info("Please make sure the player JSON file is available and properly formatted.")
        
    # Export functionality
    st.markdown("---")
    st.markdown("###  Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label=" Download Filtered Data (CSV)",
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
            label=" Download Player Summary (CSV)",
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
    st.caption(f" Data: {len(df):,} total rows")
with col2:
    st.caption(f" Players: {df['actual_player'].nunique()} total")
with col3:
    signed_count = df[df['status'] == 'signed']['actual_player'].nunique()
    st.caption(f" Signed: {signed_count}")
with col4:
    unsigned_count = df[df['status'] == 'unsigned']['actual_player'].nunique()
    st.caption(f" Unsigned: {unsigned_count}")

st.caption("Icons Player Demand Tracker v2.0")
