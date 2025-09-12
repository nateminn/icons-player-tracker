import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np  # Fixed the typo here

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
    .insight-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
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
    https://raw.githubusercontent.com/nateminn/icons-player-tracker/refs/heads/main/ICONS_DASHBOARD_MASTER_20250911.csv
    """)
    st.stop()
else:
    st.success(f"✅ Successfully loaded {len(df):,} rows of data")

# Sidebar filters
with st.sidebar:
    st.markdown("## 📊 Dashboard Controls")
    st.markdown("### 🔍 Filters")
    
    # Add refresh button
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Show data status
    st.info(f"📊 Dataset: {len(df):,} rows")
    st.caption("Data source: GitHub Repository")
    
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
    
    # Tabs for different views - ADDED NEW INSIGHTS TAB
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Overview", 
        "🌍 Market Analysis", 
        "👤 Player Details", 
        "📊 Comparisons", 
        "👕 Merchandise",
        "🎯 Market Insights"  # NEW TAB
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
        
        selected_player = st.selectbox(
            "Select a player to analyze:",
            options=sorted(filtered_df['actual_player'].unique())
        )
        
        player_data = filtered_df[filtered_df['actual_player'] == selected_player]
        
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
            
            # Comparison metrics table
            st.markdown("#### 📋 Detailed Comparison Metrics")
            comparison_metrics = comparison_df.groupby('actual_player').agg({
                'july_2025_volume': 'sum',
                'country': 'nunique',
                'name_variation': 'nunique'
            }).round(0).reset_index()
            comparison_metrics.columns = ['Player', 'Total Volume', 'Countries', 'Name Variations']
            comparison_metrics = comparison_metrics.sort_values('Total Volume', ascending=False)
            
            st.dataframe(
                comparison_metrics.style.background_gradient(subset=['Total Volume'], cmap='Blues'),
                use_container_width=True
            )
        elif len(players_to_compare) > 10:
            st.warning("Please select maximum 10 players for comparison")
    
    with tab5:
        # Comparisons (moved from tab4)
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
            
            # Player merchandise performance
            st.markdown("#### 🏆 Top Players by Merchandise Searches")
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
    
    # NEW TAB 7: MARKET INSIGHTS
    with tab7:
        st.markdown("### 🎯 Smart Market Insights & Opportunities")
        
        # Calculate opportunity scores
        st.markdown("#### 💡 Market Opportunity Analysis")
        
        # 1. Calculate market penetration for each player
        player_stats = filtered_df.groupby('actual_player').agg({
            'july_2025_volume': 'sum',
            'country': 'nunique',
            'search_type': 'nunique',
            'name_variation': 'nunique'
        }).reset_index()
        
        # Add merchandise ratio
        merch_volume = filtered_df[filtered_df['search_type'] == 'Merchandise'].groupby('actual_player')['july_2025_volume'].sum()
        total_volume = filtered_df.groupby('actual_player')['july_2025_volume'].sum()
        merch_ratio = (merch_volume / total_volume * 100).fillna(0)
        player_stats['merch_ratio'] = player_stats['actual_player'].map(merch_ratio).fillna(0)
        
        # Calculate opportunity score
        player_stats['market_coverage'] = player_stats['country'] / df['country'].nunique() * 100
        player_stats['search_diversity'] = player_stats['search_type'] / df['search_type'].nunique() * 100
        player_stats['opportunity_score'] = (
            (100 - player_stats['market_coverage']) * 0.4 +  # Higher score for untapped markets
            (100 - player_stats['merch_ratio']) * 0.3 +      # Higher score for low merch conversion
            player_stats['july_2025_volume'] / player_stats['july_2025_volume'].max() * 30  # Volume potential
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top opportunity players
            top_opportunities = player_stats.nlargest(10, 'opportunity_score')[
                ['actual_player', 'opportunity_score', 'market_coverage', 'merch_ratio']
            ].round(1)
            
            fig_opp = px.bar(
                top_opportunities,
                x='opportunity_score',
                y='actual_player',
                orientation='h',
                title='🚀 Top 10 Players with Market Opportunity',
                color='opportunity_score',
                color_continuous_scale='RdYlGn',
                labels={'opportunity_score': 'Opportunity Score', 'actual_player': 'Player'}
            )
            st.plotly_chart(fig_opp, use_container_width=True)
        
        with col2:
            # Underserved markets
            country_coverage = filtered_df.groupby('country').agg({
                'actual_player': 'nunique',
                'july_2025_volume': 'sum'
            }).reset_index()
            country_coverage['players_per_million_searches'] = (
                country_coverage['actual_player'] / (country_coverage['july_2025_volume'] / 1000000)
            ).round(1)
            
            underserved = country_coverage.nsmallest(10, 'players_per_million_searches')
            
            fig_underserved = px.bar(
                underserved,
                x='players_per_million_searches',
                y='country',
                orientation='h',
                title='🎯 Underserved Markets (Few Players, High Demand)',
                color='july_2025_volume',
                color_continuous_scale='Oranges',
                labels={'players_per_million_searches': 'Players per Million Searches'}
            )
            st.plotly_chart(fig_underserved, use_container_width=True)
        
        # Key insights section
        st.markdown("#### 📊 Automated Key Insights")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("**🔥 Hottest Player**")
            hottest = player_stats.nlargest(1, 'july_2025_volume')['actual_player'].values[0]
            st.markdown(f"{hottest}")
            st.markdown(f"Volume: {player_stats[player_stats['actual_player']==hottest]['july_2025_volume'].values[0]:,.0f}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("**💎 Hidden Gem**")
            # Players with high search diversity but low total volume
            hidden_gems = player_stats[
                (player_stats['july_2025_volume'] < player_stats['july_2025_volume'].median()) &
                (player_stats['search_diversity'] > 50)
            ].nlargest(1, 'opportunity_score')
            if not hidden_gems.empty:
                gem = hidden_gems['actual_player'].values[0]
                st.markdown(f"{gem}")
                st.markdown(f"Opportunity Score: {hidden_gems['opportunity_score'].values[0]:.1f}")
            else:
                st.markdown("No hidden gems found")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("**🌍 Best Global Reach**")
            global_player = player_stats.nlargest(1, 'country')
            gp_name = global_player['actual_player'].values[0]
            st.markdown(f"{gp_name}")
            st.markdown(f"Present in {global_player['country'].values[0]} markets")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Market gaps analysis
        st.markdown("#### 🔍 Market Gap Analysis")
        
        # Find players missing from key markets
        key_markets = ['United States', 'United Kingdom', 'Germany', 'Brazil', 'Spain']
        available_key_markets = [m for m in key_markets if m in filtered_df['country'].unique()]
        
        if available_key_markets:
            market_presence = {}
            for player in player_stats.nlargest(20, 'july_2025_volume')['actual_player']:
                player_countries = filtered_df[filtered_df['actual_player'] == player]['country'].unique()
                missing_markets = [m for m in available_key_markets if m not in player_countries]
                if missing_markets:
                    market_presence[player] = missing_markets
            
            if market_presence:
                st.markdown("**Players Missing from Key Markets:**")
                gap_data = []
                for player, markets in list(market_presence.items())[:5]:
                    gap_data.append({
                        'Player': player,
                        'Missing Markets': ', '.join(markets),
                        'Number of Gaps': len(markets)
                    })
                gap_df = pd.DataFrame(gap_data)
                st.dataframe(gap_df, use_container_width=True)
        
        # Merchandise conversion opportunities
        st.markdown("#### 🛍️ Merchandise Conversion Opportunities")
        
        # Find players with high general search but low merchandise search
        low_merch = player_stats[
            (player_stats['july_2025_volume'] > player_stats['july_2025_volume'].median()) &
            (player_stats['merch_ratio'] < 20)
        ].nlargest(10, 'july_2025_volume')[['actual_player', 'july_2025_volume', 'merch_ratio']]
        
        if not low_merch.empty:
            low_merch.columns = ['Player', 'Total Searches', 'Merch %']
            low_merch['Potential'] = '⭐' * (5 - (low_merch['Merch %'] / 5).astype(int).clip(0, 4))
            
            st.markdown("**High-volume players with low merchandise conversion:**")
            st.dataframe(
                low_merch.style.background_gradient(subset=['Total Searches'], cmap='Greens'),
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
        # Summary statistics
        summary_data = filtered_df.groupby('actual_player').agg({
            'july_2025_volume': ['sum', 'mean'],
            'country': 'nunique',
            'name_variation': 'nunique'
        }).round(0)
        summary_data.columns = ['Total_Volume', 'Avg_Volume', 'Countries', 'Name_Variations']
        summary_csv = summary_data.to_csv()
        
        st.download_button(
            label="📊 Download Player Summary (CSV)",
            data=summary_csv,
            file_name=f"player_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col3:
        # Info about the current filter
        st.info(f"📊 Showing {len(filtered_df):,} rows from {len(df):,} total")

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

st.caption("Icons Player Demand Tracker v2.1 | July 2025 Data | Built with Streamlit")
