import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Page configuration
st.set_page_config(
    page_title="Icons Player Demand Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
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

# Initialize session state for data
if 'player_data' not in st.session_state:
    st.session_state.player_data = None

@st.cache_data
def generate_demo_data():
    """Generate realistic demo data for the POC"""
    
    # Top players list
    players = [
        "Lionel Messi", "Cristiano Ronaldo", "Kylian Mbappé", "Erling Haaland",
        "Jude Bellingham", "Bukayo Saka", "Vinicius Jr", "Mohamed Salah",
        "Kevin De Bruyne", "Robert Lewandowski", "Harry Kane", "Luka Modrić",
        "Neymar Jr", "Pedri", "Gavi", "Jamal Musiala", "Florian Wirtz",
        "Victor Osimhen", "Khvicha Kvaratskhelia", "Rafael Leão"
    ]
    
    markets = ["UK", "US", "Saudi Arabia", "Mexico", "Canada", "Germany", 
               "Thailand", "China", "Italy", "Spain", "South Korea", "Global"]
    
    # Generate data with realistic patterns
    data = []
    for player in players:
        # Base popularity score for each player
        base_popularity = np.random.randint(5000, 100000)
        
        for market in markets:
            # Market-specific multipliers
            market_multiplier = {
                "UK": 1.2 if player in ["Harry Kane", "Bukayo Saka", "Mohamed Salah"] else 0.8,
                "US": 0.6 if player not in ["Cristiano Ronaldo", "Lionel Messi"] else 1.1,
                "Saudi Arabia": 1.5 if player in ["Cristiano Ronaldo", "Neymar Jr"] else 0.7,
                "Mexico": 0.9,
                "Germany": 1.1 if player in ["Jamal Musiala", "Florian Wirtz"] else 0.7,
                "Spain": 1.3 if player in ["Pedri", "Gavi", "Vinicius Jr"] else 0.8,
                "Italy": 1.2 if player in ["Victor Osimhen", "Khvicha Kvaratskhelia"] else 0.7,
                "China": 0.8,
                "Thailand": 0.6,
                "Canada": 0.5,
                "South Korea": 0.7,
                "Global": 1.0
            }.get(market, 0.8)
            
            # Calculate search volumes
            player_search = int(base_popularity * market_multiplier * np.random.uniform(0.8, 1.2))
            merch_search = int(player_search * np.random.uniform(0.15, 0.35))  # Merch is 15-35% of player searches
            
            # Trend calculation (positive or negative)
            trend = np.random.uniform(-15, 25)
            
            # Status (for demo purposes)
            status = np.random.choice(["Signed", "Unsigned", "In Negotiation"], p=[0.3, 0.6, 0.1])
            
            data.append({
                "Player": player,
                "Market": market,
                "Player Search Volume": player_search,
                "Merch Search Volume": merch_search,
                "Total Search Volume": player_search + merch_search,
                "Trend %": trend,
                "Status": status,
                "Last Updated": datetime.now().strftime("%Y-%m-%d")
            })
    
    return pd.DataFrame(data)

def load_google_sheets_data(sheet_url=None):
    """
    Load data from Google Sheets (placeholder for actual implementation)
    For the POC, we'll use demo data
    """
    # In production, you would use:
    # credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    # client = gspread.authorize(credentials)
    # sheet = client.open_by_url(sheet_url)
    # data = pd.DataFrame(sheet.worksheet('Sheet1').get_all_records())
    
    return generate_demo_data()

# Header
st.markdown('<h1 class="main-header">⚽ Icons Player Demand Tracker</h1>', unsafe_allow_html=True)
st.markdown("### Global Search Demand Analysis for Football Players")

# Sidebar configuration
with st.sidebar:
    st.markdown("## 📊 Dashboard Controls")
    
    # Data source selection
    st.markdown("### Data Source")
    data_source = st.radio(
        "Select data source:",
        ["Demo Data (POC)", "Google Sheets (Production)"]
    )
    
    if data_source == "Google Sheets (Production)":
        sheet_url = st.text_input("Google Sheet URL:", placeholder="https://docs.google.com/spreadsheets/...")
        if st.button("Load Data"):
            with st.spinner("Loading data from Google Sheets..."):
                st.session_state.player_data = load_google_sheets_data(sheet_url)
                st.success("Data loaded successfully!")
    else:
        if st.button("Generate Demo Data"):
            with st.spinner("Generating demo data..."):
                st.session_state.player_data = generate_demo_data()
                st.success("Demo data generated!")
    
    st.markdown("---")
    
    # Filters
    if st.session_state.player_data is not None:
        df = st.session_state.player_data
        
        st.markdown("### 🔍 Filters")
        
        # Market filter
        selected_markets = st.multiselect(
            "Select Markets:",
            options=df['Market'].unique(),
            default=["UK", "US", "Germany", "Spain"]
        )
        
        # Status filter
        selected_status = st.multiselect(
            "Player Status:",
            options=df['Status'].unique(),
            default=df['Status'].unique()
        )
        
        # Search volume range
        min_volume, max_volume = st.slider(
            "Total Search Volume Range:",
            min_value=int(df['Total Search Volume'].min()),
            max_value=int(df['Total Search Volume'].max()),
            value=(int(df['Total Search Volume'].min()), int(df['Total Search Volume'].max())),
            step=1000
        )
        
        # Apply filters
        filtered_df = df[
            (df['Market'].isin(selected_markets)) &
            (df['Status'].isin(selected_status)) &
            (df['Total Search Volume'] >= min_volume) &
            (df['Total Search Volume'] <= max_volume)
        ]
    else:
        st.info("👆 Click 'Generate Demo Data' to start")
        filtered_df = pd.DataFrame()

# Main dashboard
if not filtered_df.empty:
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_volume = filtered_df['Total Search Volume'].sum()
        st.metric(
            "Total Search Volume",
            f"{total_volume:,}",
            delta=f"{filtered_df['Trend %'].mean():.1f}% avg trend"
        )
    
    with col2:
        avg_player_volume = filtered_df.groupby('Player')['Total Search Volume'].sum().mean()
        st.metric(
            "Avg Volume per Player",
            f"{avg_player_volume:,.0f}",
            delta="Across selected markets"
        )
    
    with col3:
        top_market = filtered_df.groupby('Market')['Total Search Volume'].sum().idxmax()
        top_market_volume = filtered_df.groupby('Market')['Total Search Volume'].sum().max()
        st.metric(
            "Top Market",
            top_market,
            delta=f"{top_market_volume:,} searches"
        )
    
    with col4:
        unsigned_count = filtered_df[filtered_df['Status'] == 'Unsigned']['Player'].nunique()
        st.metric(
            "Unsigned Players",
            unsigned_count,
            delta="Potential signings"
        )
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "🌍 Market Analysis", "👤 Player Details", "📊 Comparisons", "🎯 Opportunities"])
    
    with tab1:
        # Overview charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Top players bar chart
            top_players = filtered_df.groupby('Player')['Total Search Volume'].sum().nlargest(10).reset_index()
            fig_bar = px.bar(
                top_players,
                x='Total Search Volume',
                y='Player',
                orientation='h',
                title='Top 10 Players by Total Search Volume',
                color='Total Search Volume',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Market distribution pie chart
            market_dist = filtered_df.groupby('Market')['Total Search Volume'].sum().reset_index()
            fig_pie = px.pie(
                market_dist,
                values='Total Search Volume',
                names='Market',
                title='Search Volume Distribution by Market'
            )
            fig_pie.update_layout(height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Trend analysis
        st.markdown("### 📈 Trend Analysis")
        trend_data = filtered_df.groupby('Player').agg({
            'Total Search Volume': 'sum',
            'Trend %': 'mean',
            'Status': 'first'
        }).reset_index()
        
        fig_scatter = px.scatter(
            trend_data,
            x='Total Search Volume',
            y='Trend %',
            size='Total Search Volume',
            color='Status',
            hover_data=['Player'],
            title='Player Popularity vs Growth Trend',
            labels={'Trend %': 'Growth Trend (%)', 'Total Search Volume': 'Total Search Volume'}
        )
        fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_scatter.add_vline(x=trend_data['Total Search Volume'].median(), line_dash="dash", line_color="gray")
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with tab2:
        # Market Analysis
        st.markdown("### 🌍 Market Deep Dive")
        
        # Market heatmap
        pivot_data = filtered_df.pivot_table(
            values='Total Search Volume',
            index='Player',
            columns='Market',
            aggfunc='sum',
            fill_value=0
        )
        
        fig_heatmap = px.imshow(
            pivot_data,
            labels=dict(x="Market", y="Player", color="Search Volume"),
            title="Player Popularity Heatmap by Market",
            aspect="auto",
            color_continuous_scale="Viridis"
        )
        fig_heatmap.update_layout(height=600)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Market trends
        col1, col2 = st.columns(2)
        with col1:
            market_trends = filtered_df.groupby('Market')['Trend %'].mean().sort_values(ascending=False).reset_index()
            fig_market_trend = px.bar(
                market_trends,
                x='Market',
                y='Trend %',
                title='Average Growth Trend by Market',
                color='Trend %',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_market_trend, use_container_width=True)
        
        with col2:
            # Merch vs Player search ratio
            merch_ratio = filtered_df.groupby('Market').agg({
                'Player Search Volume': 'sum',
                'Merch Search Volume': 'sum'
            }).reset_index()
            merch_ratio['Merch Ratio %'] = (merch_ratio['Merch Search Volume'] / merch_ratio['Player Search Volume'] * 100)
            
            fig_merch = px.bar(
                merch_ratio,
                x='Market',
                y='Merch Ratio %',
                title='Merchandise Search Ratio by Market',
                color='Merch Ratio %',
                color_continuous_scale='Purples'
            )
            st.plotly_chart(fig_merch, use_container_width=True)
    
    with tab3:
        # Player Details
        st.markdown("### 👤 Individual Player Analysis")
        
        selected_player = st.selectbox(
            "Select a player to analyze:",
            options=sorted(filtered_df['Player'].unique())
        )
        
        player_data = filtered_df[filtered_df['Player'] == selected_player]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Searches", f"{player_data['Total Search Volume'].sum():,}")
        with col2:
            st.metric("Status", player_data['Status'].iloc[0])
        with col3:
            st.metric("Avg Trend", f"{player_data['Trend %'].mean():.1f}%")
        
        # Player market breakdown
        fig_player = px.bar(
            player_data,
            x='Market',
            y='Total Search Volume',
            title=f'{selected_player} - Search Volume by Market',
            color='Total Search Volume',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_player, use_container_width=True)
        
        # Player vs Merch searches
        col1, col2 = st.columns(2)
        with col1:
            search_breakdown = player_data[['Market', 'Player Search Volume', 'Merch Search Volume']].melt(
                id_vars='Market',
                var_name='Search Type',
                value_name='Volume'
            )
            fig_breakdown = px.bar(
                search_breakdown,
                x='Market',
                y='Volume',
                color='Search Type',
                title='Player vs Merchandise Searches',
                barmode='group'
            )
            st.plotly_chart(fig_breakdown, use_container_width=True)
        
        with col2:
            # Trend by market
            fig_trend = px.bar(
                player_data,
                x='Market',
                y='Trend %',
                title='Growth Trend by Market',
                color='Trend %',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    
    with tab4:
        # Comparisons
        st.markdown("### 📊 Player Comparisons")
        
        players_to_compare = st.multiselect(
            "Select players to compare:",
            options=sorted(filtered_df['Player'].unique()),
            default=sorted(filtered_df['Player'].unique())[:3]
        )
        
        if players_to_compare:
            comparison_df = filtered_df[filtered_df['Player'].isin(players_to_compare)]
            
            # Grouped bar chart
            comparison_summary = comparison_df.groupby(['Player', 'Market'])['Total Search Volume'].sum().reset_index()
            fig_comparison = px.bar(
                comparison_summary,
                x='Market',
                y='Total Search Volume',
                color='Player',
                title='Player Comparison Across Markets',
                barmode='group'
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Radar chart for top markets
            top_markets = ['UK', 'US', 'Germany', 'Spain', 'Italy']
            radar_data = comparison_df[comparison_df['Market'].isin(top_markets)]
            radar_pivot = radar_data.pivot_table(
                values='Total Search Volume',
                index='Player',
                columns='Market',
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
                title="Market Presence Comparison (Top 5 Markets)"
            )
            st.plotly_chart(fig_radar, use_container_width=True)
    
    with tab5:
        # Opportunities
        st.markdown("### 🎯 Signing Opportunities")
        
        # Find high-potential unsigned players
        unsigned_df = filtered_df[filtered_df['Status'] == 'Unsigned']
        opportunities = unsigned_df.groupby('Player').agg({
            'Total Search Volume': 'sum',
            'Trend %': 'mean',
            'Market': 'count'
        }).reset_index()
        opportunities.columns = ['Player', 'Total Volume', 'Avg Trend %', 'Market Coverage']
        
        # Score calculation (simple weighted score)
        opportunities['Opportunity Score'] = (
            (opportunities['Total Volume'] / opportunities['Total Volume'].max() * 0.5) +
            (opportunities['Avg Trend %'] / 100 * 0.3) +
            (opportunities['Market Coverage'] / 12 * 0.2)
        ) * 100
        
        opportunities = opportunities.sort_values('Opportunity Score', ascending=False)
        
        # Display top opportunities
        st.markdown("#### 🏆 Top Unsigned Players by Opportunity Score")
        
        top_opportunities = opportunities.head(10)
        
        fig_opp = px.bar(
            top_opportunities,
            x='Opportunity Score',
            y='Player',
            orientation='h',
            title='Top 10 Signing Opportunities',
            color='Opportunity Score',
            color_continuous_scale='Greens',
            hover_data=['Total Volume', 'Avg Trend %', 'Market Coverage']
        )
        fig_opp.update_layout(height=400)
        st.plotly_chart(fig_opp, use_container_width=True)
        
        # Detailed opportunity table
        st.markdown("#### 📋 Detailed Opportunity Analysis")
        st.dataframe(
            opportunities.style.background_gradient(subset=['Opportunity Score'], cmap='Greens'),
            use_container_width=True
        )
        
        # High growth players
        st.markdown("#### 📈 High Growth Players (>15% trend)")
        high_growth = filtered_df[filtered_df['Trend %'] > 15].groupby('Player').agg({
            'Total Search Volume': 'sum',
            'Trend %': 'mean',
            'Status': 'first'
        }).reset_index().sort_values('Trend %', ascending=False)
        
        fig_growth = px.scatter(
            high_growth,
            x='Total Search Volume',
            y='Trend %',
            size='Total Search Volume',
            color='Status',
            hover_data=['Player'],
            title='High Growth Players',
            labels={'Trend %': 'Growth Rate (%)', 'Total Search Volume': 'Current Volume'}
        )
        st.plotly_chart(fig_growth, use_container_width=True)
    
    # Export functionality
    st.markdown("---")
    st.markdown("### 💾 Export Data")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name=f"player_demand_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("📊 Export to Google Sheets"):
            st.info("In production, this would export directly to Google Sheets")
    
    with col3:
        if st.button("📧 Email Report"):
            st.info("In production, this would send an automated email report")

else:
    # Empty state
    st.info("👈 Please generate demo data or connect to Google Sheets to begin")
    
    # Instructions
    with st.expander("📖 How to Use This Dashboard"):
        st.markdown("""
        ### Getting Started
        1. Click **'Generate Demo Data'** in the sidebar to see the dashboard with sample data
        2. Use filters to explore different markets and player statuses
        3. Navigate through tabs to see different analyses
        
        ### For Production Use
        1. Set up Google Sheets with your Keyword Planner data
        2. Configure Google Sheets API credentials
        3. Connect the dashboard to your sheet
        4. Set up automated data refresh
        
        ### Data Requirements
        Your Google Sheet should have these columns:
        - Player (name)
        - Market (country/region)
        - Player Search Volume
        - Merch Search Volume
        - Status (Signed/Unsigned/In Negotiation)
        - Trend % (month-over-month change)
        """)

# Footer
st.markdown("---")
st.caption("Icons Player Demand Tracker v1.0 | Data updates monthly | Built with Streamlit")
