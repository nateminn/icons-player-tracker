import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import json
import requests

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
        # Load from your GitHub repository - main-2.0 branch
        url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-2.0/ICONS_DASHBOARD_MASTER_20250911.csv"
        df = pd.read_csv(url)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Ensure numeric columns are properly typed
        df['july_2025_volume'] = pd.to_numeric(df['july_2025_volume'], errors='coerce').fillna(0)
        df['has_volume'] = pd.to_numeric(df['has_volume'], errors='coerce').fillna(0)
        
        return df
        
    except Exception as e:
        # Try main branch as fallback
        try:
            url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main/ICONS_DASHBOARD_MASTER_20250911.csv"
            df = pd.read_csv(url)
            df.columns = df.columns.str.strip()
            df['july_2025_volume'] = pd.to_numeric(df['july_2025_volume'], errors='coerce').fillna(0)
            df['has_volume'] = pd.to_numeric(df['has_volume'], errors='coerce').fillna(0)
            return df
        except:
            st.error(f"Unable to load data from GitHub. Error: {str(e)}")
            return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_player_details():
    """Load player details from GitHub"""
    try:
        # Load from main-2.0 branch
        url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-2.0/player_essential_data_json.json"
        response = requests.get(url)
        data = response.json()
        
        # Convert to DataFrame for easier manipulation
        player_df = pd.DataFrame(data['players'])
        
        # Create a dictionary for quick lookup
        player_dict = {player['name']: player for player in data['players']}
        
        return player_df, player_dict
        
    except Exception as e:
        st.warning(f"Player details not available yet. Upload player_essential_data_json.json to GitHub.")
        return pd.DataFrame(), {}

def enhance_with_player_details(df, player_dict):
    """Enhance the dashboard DataFrame with player details"""
    if not player_dict:
        return df
    
    # Add new columns
    df['team'] = ''
    df['position'] = ''
    df['age'] = 0
    df['nationality'] = ''
    df['player_league'] = ''
    df['previous_teams'] = ''
    
    # Match players and add their info
    for index, row in df.iterrows():
        player_name = row['actual_player']
        
        # Try different matching strategies
        player_info = None
        
        # Exact match
        if player_name in player_dict:
            player_info = player_dict[player_name]
        else:
            # Try partial match (last name)
            for full_name, info in player_dict.items():
                if player_name.lower() in full_name.lower() or full_name.lower() in player_name.lower():
                    player_info = info
                    break
        
        if player_info:
            df.at[index, 'team'] = player_info.get('team', '')
            df.at[index, 'position'] = player_info.get('position', '')
            df.at[index, 'age'] = player_info.get('age', 0)
            df.at[index, 'nationality'] = player_info.get('nationality', '')
            df.at[index, 'player_league'] = player_info.get('league', '')
            df.at[index, 'previous_teams'] = ', '.join(player_info.get('previous_teams', []))
    
    return df

# Header
st.markdown('<h1 class="main-header">Icons Player Demand Tracker</h1>', unsafe_allow_html=True)
st.markdown("### Global Search Demand Analysis for Football Players - July 2025")

# Load data
with st.spinner('Loading data from GitHub...'):
    df = load_csv_data()
    player_df, player_dict = load_player_details()

if df.empty:
    st.error("""
    ### Data Loading Error
    
    Could not load the data from GitHub. Please check:
    1. Your internet connection
    2. The GitHub repository is accessible
    3. The CSV file exists at the specified location
    """)
    st.stop()
else:
    # Enhance with player details if available
    if player_dict:
        df = enhance_with_player_details(df, player_dict)
        st.success(f"✓ Successfully loaded {len(df):,} rows with detailed player data")
    else:
        st.success(f"✓ Successfully loaded {len(df):,} rows of data")

# Sidebar filters
with st.sidebar:
    st.markdown("## Dashboard Controls")
    st.markdown("### Filters")

    # Country filter
    selected_countries = st.multiselect(
        "Select Countries:",
        options=sorted(df['country'].unique()),
        default=sorted(df['country'].unique())  
    )
    
    # Player filter
    available_players = sorted(df[df['country'].isin(selected_countries)]['actual_player'].unique())
    selected_players = st.multiselect(
        "Select Players:",
        options=available_players,
        default=available_players
    )
    
    # Position filter (if player data is loaded)
    if 'position' in df.columns:
        positions = sorted(df[df['position'] != '']['position'].unique())
        if positions:
            selected_positions = st.multiselect(
                "Select Positions:",
                options=positions,
                default=positions
            )
        else:
            selected_positions = []
    else:
        selected_positions = []
    
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

# Apply filters
filtered_df = df[
    (df['country'].isin(selected_countries)) &
    (df['actual_player'].isin(selected_players)) &
    (df['search_type'].isin(selected_search_types)) &
    (df['july_2025_volume'] >= volume_range[0]) &
    (df['july_2025_volume'] <= volume_range[1])
]

# Apply position filter if available
if selected_positions and 'position' in df.columns:
    filtered_df = filtered_df[filtered_df['position'].isin(selected_positions)]

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
        if 'age' in filtered_df.columns and filtered_df['age'].sum() > 0:
            avg_age = filtered_df[filtered_df['age'] > 0].groupby('actual_player')['age'].first().mean()
            st.metric(
                "Avg Player Age",
                f"{avg_age:.1f} years" if not pd.isna(avg_age) else "N/A",
                delta="Current squad"
            )
        else:
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
    
    # Tabs for different views - 6 TABS TOTAL
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Overview", 
        "🌍 Market Analysis", 
        "👤 Player Details",
        "📋 All Players",
        "📊 Comparisons", 
        "👕 Merchandise"
    ])
    
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
        
        # Position Analysis (if player data is loaded)
        if 'position' in filtered_df.columns and filtered_df['position'].str.len().sum() > 0:
            st.markdown("### Position Analysis")
            position_data = filtered_df[filtered_df['position'] != ''].groupby('position')['july_2025_volume'].sum().reset_index()
            position_data = position_data.sort_values('july_2025_volume', ascending=False)
            
            fig_position = px.bar(
                position_data,
                x='position',
                y='july_2025_volume',
                title='Search Volume by Player Position',
                color='july_2025_volume',
                color_continuous_scale='Viridis',
                labels={'july_2025_volume': 'Search Volume', 'position': 'Position'}
            )
            st.plotly_chart(fig_position, use_container_width=True)
        
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
            color_discrete_sequence=px.colors.qualitative.Set3
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
    
    # Replace the existing tab3 (Player Details) section with this cleaner version:

    with tab3:
        # Enhanced Player Details with cleaner layout
        st.markdown("### 👤 Individual Player Analysis")
        
        # Get unique players sorted by total volume
        player_volumes = filtered_df.groupby('actual_player')['july_2025_volume'].sum().sort_values(ascending=False)
        
        # Player selector at the top
        selected_player = st.selectbox(
            "Select a player to analyze:",
            options=player_volumes.index.tolist(),
            key="player_selector"
        )
        
        player_data = filtered_df[filtered_df['actual_player'] == selected_player]
        
        # Get additional player info if available
        player_info = player_dict.get(selected_player, {}) if player_dict else {}
        
        # SECTION 1: PLAYER PROFILE CARD
        st.markdown("---")
        st.markdown("#### 📋 Player Profile")
        
        if player_info:
            # Create a clean profile card with columns
            profile_col1, profile_col2, profile_col3, profile_col4 = st.columns(4)
            
            with profile_col1:
                st.markdown("**Current Team**")
                st.info(player_info.get('team', 'N/A'))
                
            with profile_col2:
                st.markdown("**Position**")
                st.info(player_info.get('position', 'N/A'))
                
            with profile_col3:
                st.markdown("**Age**")
                st.info(f"{player_info.get('age', 'N/A')} years")
                
            with profile_col4:
                st.markdown("**Nationality**")
                st.info(player_info.get('nationality', 'N/A'))
            
            # League and Previous Teams in a second row
            st.markdown("")  # Add some spacing
            league_col1, league_col2 = st.columns([1, 3])
            
            with league_col1:
                st.markdown("**Current League**")
                st.success(player_info.get('league', 'N/A'))
            
            with league_col2:
                st.markdown("**Career History**")
                previous_teams = player_info.get('previous_teams', [])
                if previous_teams:
                    # Create a nice flowing list of previous teams
                    teams_display = " → ".join(previous_teams[:8])
                    if len(previous_teams) > 8:
                        teams_display += f" (+{len(previous_teams) - 8} more)"
                    st.success(teams_display)
                else:
                    st.success("No previous clubs recorded")
        else:
            st.info("📊 Player profile data not available - showing search metrics only")
        
        # SECTION 2: KEY SEARCH METRICS
        st.markdown("---")
        st.markdown("#### 📊 Search Performance Metrics")
        
        # Calculate key metrics
        total_searches = player_data['july_2025_volume'].sum()
        countries_count = player_data['country'].nunique()
        name_variations = player_data['name_variation'].nunique()
        avg_per_country = total_searches / countries_count if countries_count > 0 else 0
        
        # Calculate search type breakdown
        search_type_breakdown = player_data.groupby('search_type')['july_2025_volume'].sum()
        merch_searches = search_type_breakdown.get('Merchandise', 0)
        name_searches = search_type_breakdown.get('Name Only', 0)
        merch_percentage = (merch_searches / total_searches * 100) if total_searches > 0 else 0
        
        # Display metrics in a clean grid
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric(
                label="Total Search Volume",
                value=f"{total_searches:,}",
                delta="All markets combined"
            )
        
        with metric_col2:
            st.metric(
                label="Market Reach",
                value=f"{countries_count} countries",
                delta=f"{avg_per_country:,.0f} avg/country"
            )
        
        with metric_col3:
            st.metric(
                label="Name Variations",
                value=f"{name_variations}",
                delta="Different search terms"
            )
        
        with metric_col4:
            st.metric(
                label="Merchandise Interest",
                value=f"{merch_percentage:.1f}%",
                delta=f"{merch_searches:,} searches"
            )
        
        # SECTION 3: VISUALIZATIONS
        st.markdown("---")
        st.markdown("#### 📈 Search Volume Analysis")
        
        # Tab selection for different views
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["🌍 By Country", "🔍 By Search Type", "📝 Name Variations"])
        
        with viz_tab1:
            # Country breakdown - horizontal bar chart for better readability
            player_country_data = player_data.groupby('country')['july_2025_volume'].sum().reset_index()
            player_country_data = player_country_data.sort_values('july_2025_volume', ascending=True)
            
            # Show top 15 countries if there are many
            if len(player_country_data) > 15:
                player_country_data = player_country_data.nlargest(15, 'july_2025_volume')
                chart_title = f'{selected_player} - Top 15 Countries by Search Volume'
            else:
                chart_title = f'{selected_player} - Search Volume by Country'
            
            fig_country = px.bar(
                player_country_data,
                x='july_2025_volume',
                y='country',
                orientation='h',
                title=chart_title,
                color='july_2025_volume',
                color_continuous_scale='Blues',
                labels={'july_2025_volume': 'Search Volume', 'country': 'Country'},
                text='july_2025_volume'
            )
            
            # Format the text on bars
            fig_country.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_country.update_layout(
                height=max(400, len(player_country_data) * 25),  # Dynamic height based on countries
                showlegend=False,
                xaxis_title="Search Volume",
                yaxis_title=""
            )
            st.plotly_chart(fig_country, use_container_width=True)
            
            # Top 3 markets summary
            if len(player_country_data) >= 3:
                st.markdown("**🏆 Top 3 Markets:**")
                top_3 = player_country_data.nlargest(3, 'july_2025_volume')
                col1, col2, col3 = st.columns(3)
                for idx, (col, row) in enumerate(zip([col1, col2, col3], top_3.itertuples())):
                    with col:
                        medal = ["🥇", "🥈", "🥉"][idx]
                        percentage = (row.july_2025_volume / total_searches * 100)
                        st.metric(
                            label=f"{medal} {row.country}",
                            value=f"{row.july_2025_volume:,}",
                            delta=f"{percentage:.1f}% of total"
                        )
        
        with viz_tab2:
            # Search type breakdown - donut chart
            player_search_type = player_data.groupby('search_type')['july_2025_volume'].sum().reset_index()
            
            fig_search = px.pie(
                player_search_type,
                values='july_2025_volume',
                names='search_type',
                title=f'{selected_player} - Search Type Distribution',
                hole=0.4,  # Make it a donut chart
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig_search.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Volume: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
            )
            
            fig_search.update_layout(height=450)
            st.plotly_chart(fig_search, use_container_width=True)
            
            # Search type summary cards
            st.markdown("**Search Type Breakdown:**")
            search_cols = st.columns(len(player_search_type))
            for col, (_, row) in zip(search_cols, player_search_type.iterrows()):
                with col:
                    percentage = (row['july_2025_volume'] / total_searches * 100)
                    st.metric(
                        label=row['search_type'],
                        value=f"{row['july_2025_volume']:,}",
                        delta=f"{percentage:.1f}%"
                    )
        
        with viz_tab3:
            # Name variations - cleaner presentation
            name_var_data = player_data.groupby('name_variation')['july_2025_volume'].sum().reset_index()
            name_var_data = name_var_data.sort_values('july_2025_volume', ascending=False)
            
            # Limit to top 15 for cleaner display
            display_limit = min(15, len(name_var_data))
            name_var_display = name_var_data.head(display_limit)
            
            if len(name_var_display) > 0:
                fig_names = px.bar(
                    name_var_display,
                    x='july_2025_volume',
                    y='name_variation',
                    orientation='h',
                    title=f'Top {display_limit} Name Variations for {selected_player}',
                    color='july_2025_volume',
                    color_continuous_scale='Greens',
                    labels={'july_2025_volume': 'Search Volume', 'name_variation': 'Search Term'},
                    text='july_2025_volume'
                )
                
                fig_names.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                fig_names.update_layout(
                    height=max(400, display_limit * 30),
                    showlegend=False,
                    xaxis_title="Search Volume",
                    yaxis_title=""
                )
                st.plotly_chart(fig_names, use_container_width=True)
                
                # Most popular variation
                if len(name_var_data) > 0:
                    top_variation = name_var_data.iloc[0]
                    st.info(f"**Most searched variation:** \"{top_variation['name_variation']}\" with {top_variation['july_2025_volume']:,} searches ({top_variation['july_2025_volume']/total_searches*100:.1f}% of total)")
            else:
                st.info("No name variation data available")
        
        # SECTION 4: MARKET INSIGHTS
        st.markdown("---")
        st.markdown("#### 💡 Market Insights")
        
        # Create insight cards
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            # Geographic concentration
            top_5_countries = player_country_data.nlargest(5, 'july_2025_volume')
            top_5_volume = top_5_countries['july_2025_volume'].sum()
            concentration = (top_5_volume / total_searches * 100) if total_searches > 0 else 0
            
            st.markdown("**📍 Geographic Concentration**")
            if concentration > 70:
                st.warning(f"High concentration: Top 5 markets account for {concentration:.1f}% of searches")
            elif concentration > 50:
                st.info(f"Moderate concentration: Top 5 markets account for {concentration:.1f}% of searches")
            else:
                st.success(f"Well distributed: Top 5 markets account for {concentration:.1f}% of searches")
        
        with insight_col2:
            # Commercial opportunity
            st.markdown("**💰 Commercial Opportunity**")
            if merch_percentage > 30:
                st.success(f"High merchandise interest ({merch_percentage:.1f}%) - Strong commercial potential")
            elif merch_percentage > 15:
                st.info(f"Moderate merchandise interest ({merch_percentage:.1f}%) - Good commercial potential")
            else:
                st.warning(f"Low merchandise interest ({merch_percentage:.1f}%) - Focus on brand building")
        
        # SECTION 5: DATA EXPORT
        st.markdown("---")
        
        # Prepare player data for export
        export_data = player_data[['actual_player', 'country', 'search_type', 'name_variation', 
                                   'july_2025_volume', 'merch_category', 'merch_term']].copy()
        
        # Add player info if available
        if player_info:
            export_data['team'] = player_info.get('team', '')
            export_data['position'] = player_info.get('position', '')
            export_data['age'] = player_info.get('age', '')
            export_data['nationality'] = player_info.get('nationality', '')
            export_data['league'] = player_info.get('league', '')
        
        csv_player = export_data.to_csv(index=False)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.download_button(
                label="📥 Download Player Data",
                data=csv_player,
                file_name=f"{selected_player.replace(' ', '_')}_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_player_detail"
            )
        
        with col2:
            # Summary report button
            if st.button("📊 Generate Report", key="generate_report"):
                st.info("Report generation feature coming soon!")
        
        with col3:
            st.caption(f"Data includes {len(player_data)} records across {countries_count} countries")

    
    with tab4:
        # Enhanced All Players tab with player details
        st.markdown("### Complete Players Database")
        
        # Create summary for all players
        player_summary = filtered_df.groupby('actual_player').agg({
            'july_2025_volume': 'sum',
            'country': 'nunique',
            'name_variation': 'nunique'
        }).reset_index()
        
        # Add player details if available
        if player_df is not None and not player_df.empty:
            player_summary = player_summary.merge(
                player_df[['name', 'team', 'position', 'age', 'nationality', 'league']],
                left_on='actual_player',
                right_on='name',
                how='left'
            )
            # Drop the duplicate name column
            if 'name' in player_summary.columns:
                player_summary = player_summary.drop('name', axis=1)
        
        # Add merchandise volume separately
        merch_volume = filtered_df[filtered_df['search_type'] == 'Merchandise'].groupby('actual_player')['july_2025_volume'].sum()
        name_volume = filtered_df[filtered_df['search_type'] == 'Name Only'].groupby('actual_player')['july_2025_volume'].sum()
        
        player_summary['name_searches'] = player_summary['actual_player'].map(name_volume).fillna(0).astype(int)
        player_summary['merch_searches'] = player_summary['actual_player'].map(merch_volume).fillna(0).astype(int)
        player_summary['merch_ratio'] = ((player_summary['merch_searches'] / player_summary['july_2025_volume'] * 100)
                                         .fillna(0).round(1))
        
        # Prepare display columns based on available data
        if 'team' in player_summary.columns:
            display_columns = [
                'actual_player', 'team', 'position', 'age', 'nationality', 'league',
                'july_2025_volume', 'country', 'name_searches', 'merch_searches', 'merch_ratio'
            ]
            column_names = [
                'Player', 'Team', 'Pos', 'Age', 'Nation', 'League',
                'Total Volume', 'Countries', 'Name Searches', 'Merch Searches', 'Merch %'
            ]
        else:
            display_columns = [
                'actual_player', 'july_2025_volume', 'country', 
                'name_searches', 'merch_searches', 'merch_ratio'
            ]
            column_names = [
                'Player', 'Total Volume', 'Countries',
                'Name Searches', 'Merch Searches', 'Merch %'
            ]
        
        player_summary = player_summary[display_columns]
        player_summary.columns = column_names
        
        # Sort by total volume by default
        player_summary = player_summary.sort_values('Total Volume', ascending=False)
        
        # Add ranking
        player_summary.insert(0, 'Rank', range(1, len(player_summary) + 1))
        
        # Filtering controls
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Filter by position if available
            if 'Pos' in player_summary.columns:
                positions = ['All'] + sorted(player_summary['Pos'].dropna().unique().tolist())
                selected_position = st.selectbox("Position", positions, key="all_players_position")
            else:
                selected_position = 'All'
        
        with col2:
            # Filter by league if available
            if 'League' in player_summary.columns:
                leagues = ['All'] + sorted(player_summary['League'].dropna().unique().tolist())
                selected_league = st.selectbox("League", leagues, key="all_players_league")
            else:
                selected_league = 'All'
        
        with col3:
            # Sort by
            sort_options = ['Total Volume', 'Name Searches', 'Merch Searches', 'Merch %', 'Player']
            if 'Age' in player_summary.columns:
                sort_options.insert(4, 'Age')
            sort_by = st.selectbox(
                "Sort by",
                options=sort_options,
                index=0,
                key="all_players_sort"
            )
        
        with col4:
            # Sort order
            sort_order = st.radio(
                "Order",
                options=['Descending', 'Ascending'],
                horizontal=True,
                key="all_players_order"
            )
        
        # Apply filters
        filtered_summary = player_summary.copy()
        
        if selected_position != 'All' and 'Pos' in filtered_summary.columns:
            filtered_summary = filtered_summary[filtered_summary['Pos'] == selected_position]
        
        if selected_league != 'All' and 'League' in filtered_summary.columns:
            filtered_summary = filtered_summary[filtered_summary['League'] == selected_league]
        
        # Apply sorting
        ascending = (sort_order == 'Ascending')
        sorted_summary = filtered_summary.sort_values(sort_by, ascending=ascending)
        
        # Reset ranking after filtering and sorting
        sorted_summary['Rank'] = range(1, len(sorted_summary) + 1)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Players Shown", len(sorted_summary))
        with col2:
            st.metric("Total Search Volume", f"{sorted_summary['Total Volume'].sum():,}")
        with col3:
            if 'Age' in sorted_summary.columns:
                avg_age = sorted_summary[sorted_summary['Age'] > 0]['Age'].mean()
                st.metric("Average Age", f"{avg_age:.1f}" if not pd.isna(avg_age) else "N/A")
            else:
                st.metric("Unique Players", len(sorted_summary))
        with col4:
            if 'League' in sorted_summary.columns:
                leagues_count = sorted_summary['League'].nunique()
                st.metric("Leagues", leagues_count)
            else:
                countries_count = sorted_summary['Countries'].sum()
                st.metric("Total Countries", countries_count)
        
        # Format the dataframe for display
        format_dict = {
            'Total Volume': '{:,.0f}',
            'Name Searches': '{:,.0f}',
            'Merch Searches': '{:,.0f}',
            'Merch %': '{:.1f}%'
        }
        if 'Age' in sorted_summary.columns:
            format_dict['Age'] = lambda x: f'{int(x)}' if pd.notna(x) and x > 0 else 'N/A'
        
        styled_df = sorted_summary.style.format(format_dict).background_gradient(subset=['Total Volume'], cmap='Blues')
        
        # Display the table
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=600
        )
        
        # Export button for this table
        st.markdown("---")
        csv_export = sorted_summary.to_csv(index=False)
        st.download_button(
            label="Download Players Summary (CSV)",
            data=csv_export,
            file_name=f"all_players_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_all_players_detailed"
        )
    
    with tab5:
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
            
            # Comparison metrics table with player details
            st.markdown("#### Detailed Comparison Metrics")
            comparison_metrics = comparison_df.groupby('actual_player').agg({
                'july_2025_volume': 'sum',
                'country': 'nunique',
                'name_variation': 'nunique'
            }).round(0).reset_index()
            
            # Add player details if available
            if player_dict:
                for idx, row in comparison_metrics.iterrows():
                    player_info = player_dict.get(row['actual_player'], {})
                    if player_info:
                        comparison_metrics.at[idx, 'Team'] = player_info.get('team', 'N/A')
                        comparison_metrics.at[idx, 'Position'] = player_info.get('position', 'N/A')
                        comparison_metrics.at[idx, 'Age'] = player_info.get('age', 'N/A')
            
            comparison_metrics.columns = ['Player', 'Total Volume', 'Countries', 'Name Variations'] + \
                                        (['Team', 'Position', 'Age'] if player_dict else [])
            comparison_metrics = comparison_metrics.sort_values('Total Volume', ascending=False)
            
            st.dataframe(
                comparison_metrics.style.background_gradient(subset=['Total Volume'], cmap='Blues'),
                use_container_width=True
            )
        elif len(players_to_compare) > 10:
            st.warning("Please select maximum 10 players for comparison")
    
    with tab6:
        # Merchandise Analysis
        st.markdown("### Merchandise Search Analysis")
        
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
            
            # Player merchandise performance
            st.markdown("#### Top Players by Merchandise Searches")
            player_merch = merch_df.groupby('actual_player')['july_2025_volume'].sum().nlargest(20).reset_index()
            
            fig_player_merch = px.bar(
                player_merch,
                x='actual_player',
                y='july_2025_volume',
                title='Top 20 Players - Merchandise Search Volume',
                color='july_2025_volume',
                color_continuous_scale='Viridis',
                labels={'july_2025_volume': 'Merchandise Searches', 'actual_player': 'Player'}
            )
            fig_player_merch.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_player_merch, use_container_width=True)
            
            # Merchandise by country
            st.markdown("#### Merchandise Searches by Country")
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
    
    # Export functionality
    st.markdown("---")
    st.markdown("### Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data (CSV)",
            data=csv,
            file_name=f"player_demand_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Summary statistics
        summary_data = filtered_df.groupby('actual_player').agg({
            'july_2025_volume': ['sum', 'mean'],
            'country': 'nunique',
            'name_variation': 'nunique'
        }).round(0)
        summary_data.columns = ['Total_Volume', 'Avg_Volume', 'Countries', 'Name_Variations']
        summary_csv = summary_data.to_csv()
        
        st.download_button(
            label="Download Player Summary (CSV)",
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
col1, col2, col3 = st.columns(3)
with col1:
    st.caption(f"Data: {len(df):,} total rows")
with col2:
    st.caption(f"Players: {df['actual_player'].nunique()} unique")
with col3:
    st.caption(f"Markets: {df['country'].nunique()} countries")

st.caption("Icons Player Demand Tracker v2.0 | September 2025 Data | Built with Streamlit")
