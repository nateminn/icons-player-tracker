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
def load_monthly_data():
    """Load monthly CSV data from GitHub"""
    monthly_data = {}
    
    # Define the URLs for each month's data
    month_urls = {
        'July': 'https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-3/Master_July_225.csv',
        'August': 'https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-3/Master_August_225.csv',
    }
    
    for month, url in month_urls.items():
        try:
            df = pd.read_csv(url)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Add month column
            df['month'] = month
            
            # Ensure numeric columns are properly typed
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0)
            df['has_volume'] = pd.to_numeric(df['has_volume'], errors='coerce').fillna(0)
            
            # Ensure status column exists and is properly formatted
            if 'status' not in df.columns:
                df['status'] = 'unsigned'
            else:
                df['status'] = df['status'].str.strip().str.lower()
                df['status'] = df['status'].replace({
                    'sign': 'signed',
                    'unsign': 'unsigned',
                    'signed': 'signed',
                    'unsigned': 'unsigned'
                })
                df['status'] = df['status'].fillna('unsigned')
            
            monthly_data[month] = df
            
        except Exception as e:
            st.warning(f"Unable to load {month} data: {str(e)}")
            continue
    
    return monthly_data

@st.cache_data(ttl=3600)
def combine_monthly_data(monthly_data, selected_months):
    """Combine selected months into a single dataframe"""
    if not monthly_data or not selected_months:
        return pd.DataFrame()
    
    combined_dfs = []
    
    for month in selected_months:
        if month in monthly_data:
            combined_dfs.append(monthly_data[month])
    
    if not combined_dfs:
        return pd.DataFrame()
    
    # Concatenate all selected months
    combined_df = pd.concat(combined_dfs, ignore_index=True)
    
    # If "All" is selected with multiple months, aggregate the data properly
    if len(selected_months) > 1:
        # For aggregated view, we need to be careful about how we combine
        # Some columns should be aggregated (volumes), others should be preserved
        
        # Define grouping columns - these identify unique search terms
        grouping_columns = ['actual_player', 'name_variation', 'country', 'country_code', 
                           'search_type', 'status']
        
        # Add merch columns only if they exist
        if 'merch_category' in combined_df.columns:
            grouping_columns.append('merch_category')
        if 'merch_term' in combined_df.columns:
            grouping_columns.append('merch_term')
        
        # Remove any columns that don't exist in the dataframe
        grouping_columns = [col for col in grouping_columns if col in combined_df.columns]
        
        # Group by all relevant columns and sum the volumes
        combined_df = combined_df.groupby(grouping_columns, dropna=False).agg({
            'volume': 'sum',
            'has_volume': 'max'  # Use max to indicate if any month had volume
        }).reset_index()
        
        # Add a combined month indicator
        combined_df['month'] = 'Combined (' + ', '.join(selected_months) + ')'
    
    return combined_df

@st.cache_data(ttl=3600)
def load_player_details():
    """Load player details from GitHub"""
    try:
        url = "https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main-3/player_essential_data_json.json"
        response = requests.get(url)
        response.raise_for_status()  # Check for HTTP errors
        
        # Try to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            st.warning(f"JSON parsing error: {e}")
            # Try to clean the JSON if there's an issue
            text = response.text.strip()
            # Remove any BOM or extra characters at the beginning
            if text.startswith('\ufeff'):
                text = text[1:]
            data = json.loads(text)
        
        # Create a dictionary for quick lookup
        if 'players' in data:
            player_dict = {player['name']: player for player in data['players']}
        else:
            # If structure is different, try direct parsing
            player_dict = {item['name']: item for item in data if 'name' in item}
        
        return player_dict
        
    except Exception as e:
        st.warning(f"Could not load player details: {str(e)}")
        return {}

# Header
st.markdown('<h1 class="main-header">Icons Player Demand Tracker</h1>', unsafe_allow_html=True)
st.markdown("### Global Search Demand Analysis for Football Players")

# Load data
with st.spinner('Loading data from GitHub...'):
    monthly_data = load_monthly_data()
    player_dict = load_player_details()

if not monthly_data:
    st.error("""
    ### ⚠️ Data Loading Error
    
    Could not load the monthly data from GitHub. Please check:
    1. Your internet connection
    2. The GitHub repository is accessible
    3. The CSV files exist at the specified locations
    """)
    st.stop()

# Sidebar filters
with st.sidebar:
    st.markdown("## Dashboard Controls")
    st.markdown("### Filters")
    
    # MONTH FILTER - NEW PRIMARY FILTER
    st.markdown("#### Month Selection")
    available_months = list(monthly_data.keys())
    month_options = ['All'] + available_months
    
    selected_month_option = st.selectbox(
        "Select Time Period:",
        options=month_options,
        index=0,  # Default to 'All'
    )
    
    # Determine which months to use
    if selected_month_option == 'All':
        selected_months = available_months
        st.info(f"Viewing combined data for: {', '.join(selected_months)}")
    else:
        selected_months = [selected_month_option]
        st.info(f"Viewing data for: {selected_month_option} 2025")
    
    # Combine the data based on selection
    df = combine_monthly_data(monthly_data, selected_months)
    
    if df.empty:
        st.error("No data available for the selected period")
        st.stop()
    
    
    # STATUS FILTER
    st.markdown("#### Player Status")
    status_options = ['All', 'Signed', 'Unsigned']
    selected_status = st.selectbox(
        "Filter by Status:",
        options=status_options,
        index=0,
    )
    
    # Apply status filter
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
    
    # Player filter
    available_players = sorted(status_filtered_df[status_filtered_df['country'].isin(selected_countries)]['actual_player'].unique())
    
    selected_players = st.multiselect(
        "Select Players:",
        options=available_players,
        default=available_players,
        help=f"Showing {len(available_players)} players based on filters"
    )
    
    # Search type filter
    search_types = sorted(df['search_type'].unique())
    selected_search_types = st.multiselect(
        "Search Types:",
        options=search_types,
        default=search_types
    )
    
    # Merchandise category filter
    if 'Merchandise' in selected_search_types:
        merch_categories = sorted(df[df['merch_category'].notna()]['merch_category'].unique())
        selected_merch_categories = st.multiselect(
            "Merchandise Categories:",
            options=merch_categories,
            default=merch_categories,
            help="Filter merchandise searches by category"
        )
    else:
        merch_categories = sorted(df[df['merch_category'].notna()]['merch_category'].unique())
        selected_merch_categories = merch_categories
    
    # Volume filter
    if len(df) > 0:
        min_vol = int(df['volume'].min())
        max_vol = int(df['volume'].max())
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
    (df['volume'] >= volume_range[0]) &
    (df['volume'] <= volume_range[1])
]

# Apply status filter
if selected_status == 'Signed':
    filtered_df = filtered_df[filtered_df['status'] == 'signed']
elif selected_status == 'Unsigned':
    filtered_df = filtered_df[filtered_df['status'] == 'unsigned']

# Apply merchandise category filter
if 'Merchandise' in selected_search_types and selected_merch_categories:
    merch_filter = (
        (filtered_df['search_type'] != 'Merchandise') |
        (filtered_df['merch_category'].isin(selected_merch_categories))
    )
    filtered_df = filtered_df[merch_filter]

if only_with_volume:
    filtered_df = filtered_df[filtered_df['has_volume'] == 1]

# Main dashboard
if not filtered_df.empty:
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_volume = filtered_df['volume'].sum()
        st.metric(
            "Total Search Volume",
            f"{total_volume:,}",
            delta=f"{', '.join(selected_months)} 2025"
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
        signed_in_filter = filtered_df[filtered_df['status'] == 'signed']['actual_player'].nunique()
        unsigned_in_filter = filtered_df[filtered_df['status'] == 'unsigned']['actual_player'].nunique()
        st.metric(
            "Player Status",
            f"{signed_in_filter} Signed",
            delta=f"{unsigned_in_filter} Unsigned"
        )
    
    with col4:
        top_country = filtered_df.groupby('country')['volume'].sum().idxmax()
        st.metric(
            "Top Market",
            top_country,
            delta=f"{filtered_df[filtered_df['country'] == top_country]['volume'].sum():,} searches"
        )
    
    st.markdown("---")
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Overview", 
        "🌍 Market Analysis", 
        "👤 Player Details", 
        "📊 Comparisons", 
        "👕 Merchandise",
        "📋 Player Database"
    ])
    
    with tab1:
        # Overview charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Top players by total volume
            player_volumes = filtered_df.groupby(['actual_player', 'status'])['volume'].sum().reset_index()
            player_volumes = player_volumes.nlargest(15, 'volume')
            
            fig_bar = px.bar(
                player_volumes,
                x='volume',
                y='actual_player',
                orientation='h',
                title=f'Top 15 Players by Search Volume ({", ".join(selected_months)})',
                color='status',
                color_discrete_map={'signed': '#2ecc71', 'unsigned': '#3498db'},
                labels={'volume': 'Search Volume', 'actual_player': 'Player', 'status': 'Status'}
            )
            fig_bar.update_layout(height=500)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Country distribution
            country_dist = filtered_df.groupby('country')['volume'].sum().reset_index()
            fig_pie = px.pie(
                country_dist,
                values='volume',
                names='country',
                title='Search Volume Distribution by Country'
            )
            fig_pie.update_layout(height=500)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Search Type Breakdown
        st.markdown("### Search Type Analysis")
        search_type_data = filtered_df.groupby(['search_type', 'actual_player'])['volume'].sum().reset_index()
        search_type_pivot = search_type_data.pivot(index='actual_player', columns='search_type', values='volume').fillna(0)
        
        # Get top 20 players by total volume
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
        pivot_data = filtered_df.groupby(['actual_player', 'country'])['volume'].sum().reset_index()
        pivot_table = pivot_data.pivot(index='actual_player', columns='country', values='volume').fillna(0)
        
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
            country_totals = filtered_df.groupby('country')['volume'].sum().nlargest(10).reset_index()
            fig_country = px.bar(
                country_totals,
                x='country',
                y='volume',
                title='Top 10 Countries by Total Search Volume',
                color='volume',
                color_continuous_scale='Teal',
                labels={'volume': 'Total Volume'}
            )
            st.plotly_chart(fig_country, use_container_width=True)
        
        with col2:
            # Average volume per player by country
            country_avg = filtered_df.groupby('country').agg({
                'volume': 'sum',
                'actual_player': 'nunique'
            }).reset_index()
            country_avg['avg_per_player'] = country_avg['volume'] / country_avg['actual_player']
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
        # Player Details - ENHANCED VERSION
        st.markdown("### **Individual Player Analysis**")
        
        # Get unique players sorted by total volume
        player_volumes_for_select = filtered_df.groupby('actual_player')['volume'].sum().sort_values(ascending=False)
        player_options = player_volumes_for_select.index.tolist()
        
        # Simple player selection
        selected_player = st.selectbox(
            "Select a player to analyze:",
            options=player_options
        )
        
        player_data = filtered_df[filtered_df['actual_player'] == selected_player]
        player_status = player_data['status'].iloc[0] if len(player_data) > 0 else 'unknown'
        
        # Get additional player info if available
        player_info = player_dict.get(selected_player, {}) if player_dict else {}
        
        st.markdown("---")
        
        # PLAYER PROFILE SECTION - ENHANCED
        st.markdown("#### **Player Profile**")
        
        # First row - Basic info with 5 columns (added signing status)
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("**Current Team**")
            st.info(player_info.get('team', 'N/A'))
        
        with col2:
            st.markdown("**Position**")
            st.info(player_info.get('position', 'N/A'))
        
        with col3:
            st.markdown("**Age**")
            age = player_info.get('age', 'N/A')
            if isinstance(age, (int, float)):
                st.info(f"{age} years")
            else:
                st.info(str(age))
        
        with col4:
            st.markdown("**Nationality**")
            st.info(player_info.get('nationality', 'N/A'))
        
        with col5:
            st.markdown("**Signing Status**")
            if player_status == 'signed':
                st.success(" Signed")
            elif player_status == 'unsigned':
                st.warning(" Unsigned")
            else:
                st.info("Unknown")
        
        # Second row - League and Career History
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("**Current League**")
            st.success(player_info.get('league', 'N/A'))
        
        with col2:
            st.markdown("**Career History**")
            if player_info and player_info.get('previous_teams'):
                previous_teams = player_info.get('previous_teams', [])
                career_path = " → ".join(previous_teams)
                current_team = player_info.get('team', '')
                if current_team and current_team != 'Retired' and 'Deceased' not in current_team:
                    career_path = career_path + " → " + current_team if career_path else current_team
                st.success(career_path if career_path else "No previous clubs recorded")
            else:
                st.success("No career history available")
        
        st.markdown("---")
        
        # SEARCH PERFORMANCE METRICS
        st.markdown("#### **Search Performance Metrics**")
        
        # Calculate metrics
        total_searches = player_data['volume'].sum()
        countries = player_data['country'].nunique()
        name_variations = player_data['name_variation'].nunique()
        merch_searches = player_data[player_data['search_type'] == 'Merchandise']['volume'].sum()
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
        
        # MARKET DISTRIBUTION
        st.markdown("#### **Market Distribution**")
        
        # Top markets info
        player_country_data = player_data.groupby('country')['volume'].sum().sort_values(ascending=False).reset_index()
        
        if not player_country_data.empty:
            # Show top 3 markets
            col1, col2, col3 = st.columns(3)
            
            for i, col in enumerate([col1, col2, col3]):
                if i < len(player_country_data):
                    with col:
                        country = player_country_data.iloc[i]['country']
                        volume = player_country_data.iloc[i]['volume']
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
            y='volume',
            title=f'Search Volume by Country - {selected_player}',
            color='volume',
            color_continuous_scale='Blues',
            labels={'volume': 'Search Volume'},
            height=400
        )
        st.plotly_chart(fig_player, use_container_width=True)
        
        # Two column layout for pie charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Search type breakdown
            player_search_type = player_data.groupby('search_type')['volume'].sum().reset_index()
            fig_search = px.pie(
                player_search_type,
                values='volume',
                names='search_type',
                title='Search Type Distribution',
                height=350
            )
            st.plotly_chart(fig_search, use_container_width=True)
        
        with col2:
            # Name variations breakdown
            name_var_data = player_data.groupby('name_variation')['volume'].sum().reset_index()
            if len(name_var_data) > 0:
                fig_names = px.pie(
                    name_var_data,
                    values='volume',
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
            'volume': 'sum'
        }).reset_index()
        
        # Pivot for better display
        if not detailed_data.empty:
            pivot_table = detailed_data.pivot(
                index='country',
                columns='search_type',
                values='volume'
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
        # Comparisons (similar structure, using 'volume' column)
        st.markdown("### Player Comparisons")
        
        players_to_compare = st.multiselect(
            "Select players to compare (max 10):",
            options=sorted(filtered_df['actual_player'].unique()),
            default=sorted(filtered_df.groupby('actual_player')['volume'].sum().nlargest(3).index)
        )
        
        if players_to_compare and len(players_to_compare) <= 10:
            comparison_df = filtered_df[filtered_df['actual_player'].isin(players_to_compare)]
            
            comparison_summary = comparison_df.groupby(['actual_player', 'country'])['volume'].sum().reset_index()
            
            top_countries_for_comparison = comparison_summary.groupby('country')['volume'].sum().nlargest(8).index
            comparison_summary_filtered = comparison_summary[comparison_summary['country'].isin(top_countries_for_comparison)]
            
            fig_comparison = px.bar(
                comparison_summary_filtered,
                x='country',
                y='volume',
                color='actual_player',
                title='Player Comparison Across Top Markets',
                barmode='group',
                labels={'volume': 'Search Volume'}
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
    
    with tab5:
        # Merchandise Analysis
        st.markdown("### Merchandise Search Analysis")
        
        merch_df = filtered_df[filtered_df['search_type'] == 'Merchandise']
        
        if not merch_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                merch_cat_totals = merch_df.groupby('merch_category')['volume'].sum().reset_index()
                fig_merch_cat = px.pie(
                    merch_cat_totals,
                    values='volume',
                    names='merch_category',
                    title='Merchandise Search Volume by Category'
                )
                st.plotly_chart(fig_merch_cat, use_container_width=True)
            
            with col2:
                merch_terms = merch_df.groupby('merch_term')['volume'].sum().nlargest(15).reset_index()
                fig_terms = px.bar(
                    merch_terms,
                    x='volume',
                    y='merch_term',
                    orientation='h',
                    title='Top 15 Merchandise Search Terms',
                    color='volume',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_terms, use_container_width=True)


    with tab6:
            # Player Database - Comprehensive table view
            st.markdown("### 📋 Complete Player Database")
            st.markdown("*All data respects current dashboard filters*")
            
            # Aggregate player data from filtered dataframe
            player_summary = filtered_df.groupby('actual_player').agg({
                'volume': 'sum',
                'country': lambda x: len(x.unique()),
                'name_variation': lambda x: len(x.unique()),
                'search_type': lambda x: len(x.unique()),
                'status': 'first'
            }).reset_index()
            
            player_summary.columns = ['Player', 'Total Volume', 'Countries', 'Name Variations', 'Search Types', 'Status']
            
            # Calculate merchandise volume for each player
            merch_volumes = filtered_df[filtered_df['search_type'] == 'Merchandise'].groupby('actual_player')['volume'].sum()
            player_summary['Merchandise Volume'] = player_summary['Player'].map(merch_volumes).fillna(0).astype(int)
            
            # Calculate top country for each player
            top_countries = filtered_df.groupby('actual_player').apply(
                lambda x: x.groupby('country')['volume'].sum().idxmax()
            )
            player_summary['Top Market'] = player_summary['Player'].map(top_countries)
            
            # Add player info from JSON if available
            if player_dict:
                player_summary['Team'] = player_summary['Player'].apply(lambda x: player_dict.get(x, {}).get('team', 'N/A'))
                player_summary['Position'] = player_summary['Player'].apply(lambda x: player_dict.get(x, {}).get('position', 'N/A'))
                player_summary['Age'] = player_summary['Player'].apply(lambda x: player_dict.get(x, {}).get('age', 'N/A'))
                player_summary['Nationality'] = player_summary['Player'].apply(lambda x: player_dict.get(x, {}).get('nationality', 'N/A'))
                player_summary['League'] = player_summary['Player'].apply(lambda x: player_dict.get(x, {}).get('league', 'N/A'))
            
            # Calculate merchandise percentage
            player_summary['Merch %'] = ((player_summary['Merchandise Volume'] / player_summary['Total Volume']) * 100).round(1)
            player_summary['Merch %'] = player_summary['Merch %'].fillna(0)
            
            # Format status column for display
            player_summary['Status'] = player_summary['Status'].apply(
                lambda x: ' Signed' if x == 'signed' else ' Unsigned'
            )
            
            # Reorder columns for better display
            if player_dict:
                column_order = [
                    'Player', 'Status', 'Total Volume', 'Top Market', 'Countries', 
                    'Team', 'Position', 'Age', 'Nationality', 'League',
                    'Name Variations', 'Search Types', 'Merchandise Volume', 'Merch %'
                ]
            else:
                column_order = [
                    'Player', 'Status', 'Total Volume', 'Top Market', 'Countries',
                    'Name Variations', 'Search Types', 'Merchandise Volume', 'Merch %'
                ]
            
            player_summary = player_summary[column_order]
            
            # Sort by total volume by default
            player_summary = player_summary.sort_values('Total Volume', ascending=False)
            
            # Display summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Players", len(player_summary))
            with col2:
                signed_count = len(player_summary[player_summary['Status'] == ' Signed'])
                st.metric("Signed Players", signed_count)
            with col3:
                unsigned_count = len(player_summary[player_summary['Status'] == ' Unsigned'])
                st.metric("Unsigned Players", unsigned_count)
            
            st.markdown("---")
            
            # Display options
            col1, col2 = st.columns(2)
            
            with col1:
                sort_by = st.selectbox(
                    "Sort by:",
                    options=['Total Volume', 'Player', 'Countries', 'Merchandise Volume', 'Merch %', 'Age'],
                    index=0
                )
            
            with col2:
                sort_order = st.radio(
                    "Order:",
                    options=['Descending', 'Ascending'],
                    horizontal=True
                )
            
            # Apply sorting
            ascending = sort_order == 'Ascending'
            if sort_by in player_summary.columns:
                player_summary = player_summary.sort_values(sort_by, ascending=ascending)
            
            # Reset index for clean display
            player_summary = player_summary.reset_index(drop=True)
            player_summary.index = player_summary.index + 1  # Start index at 1
            
            # Display the table with formatting
            st.dataframe(
                player_summary.style.format({
                    'Total Volume': '{:,.0f}',
                    'Merchandise Volume': '{:,.0f}',
                    'Merch %': '{:.1f}%',
                    'Countries': '{:.0f}',
                    'Name Variations': '{:.0f}',
                    'Search Types': '{:.0f}'
                }).background_gradient(subset=['Total Volume'], cmap='Blues'),
                use_container_width=True,
                height=600
            )
            
            # Export option for the table
            st.markdown("---")
            csv = player_summary.to_csv(index=False)
            st.download_button(
                label="📥 Download Player Database (CSV)",
                data=csv,
                file_name=f"player_database_{selected_month_option}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
    # Export functionality
    st.markdown("---")
    st.markdown("###  Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label=" Download Filtered Data (CSV)",
            data=csv,
            file_name=f"player_demand_data_{selected_month_option}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        summary_data = filtered_df.groupby('actual_player').agg({
            'volume': ['sum', 'mean'],
            'country': 'nunique',
            'name_variation': 'nunique',
            'status': 'first'
        }).round(0)
        summary_data.columns = ['Total_Volume', 'Avg_Volume', 'Countries', 'Name_Variations', 'Status']
        summary_csv = summary_data.to_csv()
        
        st.download_button(
            label=" Download Player Summary (CSV)",
            data=summary_csv,
            file_name=f"player_summary_{selected_month_option}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col3:
        st.info(f"Showing {len(filtered_df):,} rows | Period: {', '.join(selected_months)}")

else:
    st.warning("No data matches the current filter criteria. Please adjust your filters.")
    st.info(f"Total dataset contains {len(df):,} rows with {df['actual_player'].nunique()} unique players across {df['country'].nunique()} countries.")

# Footer
st.markdown("---")
st.caption(f"Icons Player Demand Tracker v3.0 | Data Period: {', '.join(selected_months)} 2025")
