import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import io
from src.data_loader import BigQueryCONN
from src.image_loader import image_reader
from src.prompt_classifier import classify_prompt
from src.llm import LMMConnectors
from src.updates import Update
from src.predictor import Prediction

st.set_page_config(
    page_title="EcoChain AI Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2e8b57 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #2e8b57;
        margin-bottom: 1rem;
    }
    .insight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    .supplier-detail {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }

    /* New Supplier Form Styles */
    .new-supplier-form {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: white;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    .form-section {
        background: rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }

    /* AI Assistant Styles */
    .ai-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }

    .ai-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .ai-subtitle {
        text-align: center;
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 2rem;
    }

    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 15px;
        max-width: 80%;
        word-wrap: break-word;
    }

    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        text-align: right;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
    }

    .example-queries {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
    }
    .success-message {
        background: linear-gradient(135deg, #28a745, #20c997);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        text-align: center;
        font-weight: bold;
    }

</style>
""", unsafe_allow_html=True)


@st.cache_data()
def load_supplier_data():
    try:
        conn = BigQueryCONN()
        suppliers = conn.bigquery_loader()
        df = pd.DataFrame(suppliers)
        df = df.dropna()
        return df
    except Exception as e:
        st.error(f"Error connecting to database: {str(e)}")
        return pd.DataFrame()

# Initialize supplier database in session state
if "suppliers_db" not in st.session_state:
    st.session_state.suppliers_db = pd.DataFrame(columns=[
        'supplier_name', 'country', 'region', 'product_category',
        'sub_category', 'certification', 'partnership_status',
        'annual_volume', 'cost_premium', 'risk_level', 'last_audit',
        'audit_summary', 'recommendation', 'uploaded_images'
    ])

def run_ai_query(user_query: str):
    try:
        classifier = classify_prompt(user_query)
        AI = LMMConnectors(user_query)
        if classifier == "VECTOR_SEARCH":
            response = AI.Vector_Search()
            return response
        else:
            response = AI.AI_Generate()
            return response
    except Exception as e:
        return f"Sorry, I couldn't process your query. Error: {str(e)}"

def update_supplier(supplier):
    try:
        update = Update(supplier)
        bqsupplier_id = update.supplier_update()
        update.embed_supplier(bqsupplier_id)
        scores = Prediction()
        update.update_ecoscores(scores)
        update.update_recommendations(bqsupplier_id)
        return True
    except Exception as e:
        st.error(f"Error updating supplier: {str(e)}")
        return False

# Load data
try:
    df = load_supplier_data()
    if df.empty:
        st.error("No data loaded. Please check your Internet Connection.")
        st.stop()
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

mode = st.sidebar.radio("Choose Mode", ["Dashboard", "AI Assistant", "Add New Supplier"])

if mode == "Dashboard":

    st.markdown("""
    <div class="main-header">
        <h1>🌍 EcoChain AI Supplier Sustainability Dashboard</h1>
        <p>Advanced Decision Support for Sustainable Sourcing & Supply Chain Management</p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Filters
    st.sidebar.markdown("## 🔍 Filters & Controls")

    # Check if required columns exist
    required_columns = ['country', 'region', 'product_category', 'recommendation', 'total_eco_score', 'risk_level']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing required columns: {missing_columns}")
        st.stop()

    # Multi-select filters
    countries = st.sidebar.multiselect("🌏 Countries",
                                    options=sorted(df["country"].unique()),
                                    default=[])

    regions = st.sidebar.multiselect("🗺️ Regions",
                                    options=sorted(df["region"].unique()),
                                    default=[])

    categories = st.sidebar.multiselect("📦 Product Categories",
                                    options=sorted(df["product_category"].unique()),
                                    default=[])

    recommendations = st.sidebar.multiselect("⭐ Recommendations",
                                            options=sorted(df["recommendation"].unique()),
                                            default=[])

    # Score threshold slider
    min_score = st.sidebar.slider("🎯 Minimum Eco Score",
                                min_value=float(df["total_eco_score"].min()),
                                max_value=float(df["total_eco_score"].max()),
                                value=float(df["total_eco_score"].min()))

    # Risk level filter
    risk_levels = st.sidebar.multiselect("⚠️ Risk Levels",
                                        options=sorted(df["risk_level"].unique()),
                                        default=[])

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 View Options")
    show_detailed_scores = st.sidebar.checkbox("Show Detailed Scores", value=False)
    show_financial_metrics = st.sidebar.checkbox("Show Financial Metrics", value=True)

    # Apply filters
    filtered_df = df.copy()

    if countries:
        filtered_df = filtered_df[filtered_df["country"].isin(countries)]
    if regions:
        filtered_df = filtered_df[filtered_df["region"].isin(regions)]
    if categories:
        filtered_df = filtered_df[filtered_df["product_category"].isin(categories)]
    if recommendations:
        filtered_df = filtered_df[filtered_df["recommendation"].isin(recommendations)]
    if risk_levels:
        filtered_df = filtered_df[filtered_df["risk_level"].isin(risk_levels)]

    filtered_df = filtered_df[filtered_df["total_eco_score"] >= min_score]

    # KPI Dashboard
    st.markdown("## 📈 Key Performance Indicators")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🏢 Total Suppliers",
                len(filtered_df),
                delta=f"{len(filtered_df) - len(df)} from total")

    with col2:
        preferred_pct = (filtered_df['recommendation'].eq('Preferred').mean() * 100) if len(filtered_df) > 0 else 0
        st.metric("⭐ Preferred (%)",
                f"{preferred_pct:.1f}%")

    with col3:
        avg_score = filtered_df['total_eco_score'].mean() if len(filtered_df) > 0 else 0
        st.metric("🎯 Avg Eco Score",
                f"{avg_score:.1f}",
                delta=f"{avg_score - df['total_eco_score'].mean():.1f}")

    with col4:
        total_volume = filtered_df['annual_volume'].sum() if len(filtered_df) > 0 else 0
        st.metric("📦 Annual Volume",
                f"${total_volume/1000000:.1f}M")

    with col5:
        avg_premium = filtered_df['cost_premium'].mean() if len(filtered_df) > 0 else 0
        st.metric("💰 Avg Premium",
                f"{avg_premium:.1f}%")

    st.markdown("---")

    # Main Content Area
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Supplier Overview", "📊 Analytics", "🔍 Deep Dive", "🤖 Data Insights", "🔮 Simulation"])

    with tab1:
        st.markdown("### 📋 Supplier Recommendations Table")

        if len(filtered_df) > 0:
            # Color mapping for recommendations
            def highlight_recommendation(val):
                color_map = {
                    'Preferred': 'background-color: #d4edda; color: #155724',
                    'Neutral': 'background-color: #fff3cd; color: #856404',
                    'Under Review': 'background-color: #cce5f0; color: #004085',
                    'Caution': 'background-color: #f8d7da; color: #721c24',
                    'Avoid': 'background-color: #f5c6cb; color: #721c24'
                }
                return color_map.get(val, '')

            # Display columns based on user preference
            display_cols = ["supplier_name", "country", "product_category", "sub_category", "total_eco_score",
                        "certification", "partnership_status", "recommendation"]

            # Check for detailed score columns
            detailed_score_cols = ["carbon_score", "water_score", "waste_score", "social_score"]
            if show_detailed_scores and all(col in df.columns for col in detailed_score_cols):
                display_cols.extend(detailed_score_cols)

            # Check for financial metric columns
            financial_cols = ["annual_volume", "cost_premium", "risk_level"]
            if show_financial_metrics and all(col in df.columns for col in financial_cols):
                display_cols.extend(financial_cols)

            # Filter display columns to only include those that exist in the dataframe
            display_cols = [col for col in display_cols if col in filtered_df.columns]

            # Format dataframe for display
            display_df = filtered_df[display_cols].copy()

            # Apply styling if recommendation column exists
            if 'recommendation' in display_df.columns:
                styled_df = display_df.style.map(
                    highlight_recommendation, subset=['recommendation']
                )

                # Format numeric columns
                format_dict = {'total_eco_score': '{:.1f}'}
                if 'carbon_score' in display_df.columns:
                    format_dict.update({
                        'carbon_score': '{:.1f}',
                        'water_score': '{:.1f}',
                        'waste_score': '{:.1f}',
                        'social_score': '{:.1f}'
                    })
                if 'annual_volume' in display_df.columns:
                    format_dict.update({
                        'annual_volume': '${:,.0f}',
                        'cost_premium': '{:.1f}%'
                    })

                styled_df = styled_df.format(format_dict)
                st.dataframe(styled_df, use_container_width=True, height=400)
            else:
                st.dataframe(display_df, use_container_width=True, height=400)

            # Download button
            csv = filtered_df.to_csv(index=False)
            st.download_button("📥 Download Data", csv, "supplier_data.csv", "text/csv")
        else:
            st.warning("No suppliers match the current filter criteria.")

    with tab2:
        if len(filtered_df) > 0:
            col1, col2 = st.columns(2)

            with col1:
                # Eco Score Distribution
                st.markdown("#### 📈 Eco Score Distribution")
                fig_hist = px.histogram(filtered_df, x="total_eco_score", nbins=15,
                                    color="recommendation",
                                    title="Distribution of Sustainability Scores",
                                    color_discrete_map={
                                        'Preferred': '#28a745',
                                        'Neutral': '#ffc107',
                                        'Under Review': '#17a2b8',
                                        'Caution': '#fd7e14',
                                        'Avoid': '#dc3545'
                                    })
                fig_hist.update_layout(height=400)
                st.plotly_chart(fig_hist, use_container_width=True)

                # Geographic Distribution
                st.markdown("#### 🗺️ Suppliers by Region")
                region_data = filtered_df['region'].value_counts().reset_index()
                region_data.columns = ['Region', 'Count']
                fig_pie = px.pie(region_data, values='Count', names='Region',
                            title="Supplier Distribution by Region")
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                # Category Performance
                st.markdown("#### 📊 Performance by Category")
                category_avg = filtered_df.groupby('product_category')['total_eco_score'].mean().reset_index()
                fig_bar = px.bar(category_avg, x='product_category', y='total_eco_score',
                            title="Average Eco Score by Product Category",
                            color='total_eco_score',
                            color_continuous_scale='RdYlGn')
                fig_bar.update_layout(height=400, xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, use_container_width=True)

                # Risk vs Score Analysis (only if columns exist)
                if 'cost_premium' in filtered_df.columns and 'annual_volume' in filtered_df.columns:
                    st.markdown("#### ⚖️ Risk vs Sustainability Score")
                    fig_scatter = px.scatter(filtered_df, x='total_eco_score', y='cost_premium',
                                        color='risk_level', size='annual_volume',
                                        hover_data=['supplier_name', 'country'],
                                        title="Cost Premium vs Eco Score",
                                        color_discrete_map={
                                            'Low': '#28a745',
                                            'Medium': '#ffc107',
                                            'High': '#dc3545'
                                        })
                    st.plotly_chart(fig_scatter, use_container_width=True)

            # Sub-category Analysis
            if 'sub_category' in filtered_df.columns:
                st.markdown("#### 📊 Sub-Category Performance")
                subcategory_performance = filtered_df.groupby('sub_category').agg({
                    'total_eco_score': 'mean',
                    'supplier_name': 'count'
                }).round(2).reset_index()
                subcategory_performance.columns = ['Sub Category', 'Avg Score', 'Count']
                subcategory_performance = subcategory_performance.sort_values('Avg Score', ascending=False)

                fig_sub = px.bar(subcategory_performance, x='Sub Category', y='Avg Score',
                                title="Average Eco Score by Sub-Category",
                                color='Avg Score',
                                color_continuous_scale='RdYlGn')
                fig_sub.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_sub, use_container_width=True)

            # Detailed Score Breakdown
            detailed_score_cols = ["carbon_score", "water_score", "waste_score", "social_score"]
            if show_detailed_scores and all(col in filtered_df.columns for col in detailed_score_cols):
                st.markdown("#### 📊 Detailed Score Breakdown")

                # Create radar chart for top 5 suppliers
                top_suppliers = filtered_df.nlargest(5, 'total_eco_score')

                fig_radar = go.Figure()

                for idx, (_, supplier) in enumerate(top_suppliers.iterrows()):
                    fig_radar.add_trace(go.Scatterpolar(
                        r=[supplier[col] for col in detailed_score_cols],
                        theta=['Carbon', 'Water', 'Waste', 'Social'],
                        fill='toself',
                        name=supplier['supplier_name'][:20]
                    ))

                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=True,
                    title="Top 5 Suppliers - Detailed Score Comparison",
                    height=500
                )
                st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.warning("No data available for analytics with current filters.")

    with tab3:
        st.markdown("### 🔍 Detailed Supplier Analysis")

        if len(filtered_df) > 0:
            # Supplier selection
            supplier_names = filtered_df['supplier_name'].tolist()
            selected_supplier = st.selectbox("Select a supplier for detailed analysis:", supplier_names)

            if selected_supplier:
                supplier_data = filtered_df[filtered_df['supplier_name'] == selected_supplier].iloc[0]

                # Create detailed view
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"#### {supplier_data['supplier_name']}")

                    # Score visualization (only if detailed scores exist)
                    detailed_score_cols = ["carbon_score", "water_score", "waste_score", "social_score"]
                    if all(col in supplier_data.index for col in detailed_score_cols):
                        scores = {
                            'Carbon Footprint': supplier_data['carbon_score'],
                            'Water Management': supplier_data['water_score'],
                            'Waste Reduction': supplier_data['waste_score'],
                            'Social Impact': supplier_data['social_score']
                        }

                        fig_gauge = make_subplots(
                            rows=2, cols=2,
                            specs=[[{'type': 'indicator'}, {'type': 'indicator'}],
                                [{'type': 'indicator'}, {'type': 'indicator'}]],
                            subplot_titles=list(scores.keys()),
                            vertical_spacing=0.3
                        )

                        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
                        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']

                        for i, (metric, score) in enumerate(scores.items()):
                            row, col = positions[i]
                            fig_gauge.add_trace(
                                go.Indicator(
                                    mode="gauge+number",
                                    value=score,
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    gauge={
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': colors[i]},
                                        'steps': [
                                            {'range': [0, 40], 'color': "lightgray"},
                                            {'range': [40, 70], 'color': "yellow"},
                                            {'range': [70, 100], 'color': "green"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': 90
                                        }
                                    }
                                ),
                                row=row, col=col
                            )

                        fig_gauge.update_layout(height=900, title="Sustainability Metrics Dashboard")
                        st.plotly_chart(fig_gauge, use_container_width=True)
                    else:
                        st.info("Detailed scores not available for this supplier.")

                with col2:

                    # Show product image if available
                    if 'image_url' in supplier_data and pd.notna(supplier_data['image_url']):
                        st.markdown("#### 📸 Product Image")
                        try:
                            with st.spinner("🔄 Retrieving Product Image..."):
                                image = image_reader(supplier_data['image_url'])
                                st.image(image,width=200)
                        except Exception as e:
                            st.info("Product image not available. Please check your Internet Connection")

                    st.markdown("#### Key Information")

                    info_items = [
                        ("🏢", "Supplier ID", supplier_data.get('supplier_id', 'N/A')),
                        ("🌍", "Country", supplier_data['country']),
                        ("🗺️", "Region", supplier_data['region']),
                        ("🏭", "Category", supplier_data['product_category']),
                        ("🏭", "Sub-Category", supplier_data.get('sub_category', 'N/A')),
                        ("🎯", "Overall Score", f"{supplier_data['total_eco_score']:.1f}/100"),
                        ("📜", "Certifications", supplier_data.get('certification', 'N/A')),
                        ("🤝", "Status", supplier_data.get('partnership_status', 'N/A')),
                        ("💰", "Annual Volume", f"${supplier_data.get('annual_volume', 0):,}"),
                        ("📈", "Cost Premium", f"{supplier_data.get('cost_premium', 0):.1f}%"),
                        ("⚠️", "Risk Level", supplier_data.get('risk_level', 'N/A')),
                        ("📅", "Last Audit", supplier_data.get('last_audit', 'N/A'))
                    ]

                    for icon, label, value in info_items:
                        st.markdown(f"**{icon} {label}:** {value}")

                    # Recommendation badge
                    rec = supplier_data['recommendation']
                    color_map = {
                        'Preferred': '🟢',
                        'Neutral': '🟡',
                        'Under Review': '🔵',
                        'Caution': '🟠',
                        'Avoid': '🔴'
                    }
                    st.markdown(f"### {color_map.get(rec, '⚪')} Recommendation: **{rec}**")

                    # Show audit summary if available
                    if 'audit_summary' in supplier_data and pd.notna(supplier_data['audit_summary']):
                        st.markdown("#### 📋 Latest Audit Summary")
                        st.text_area("", value=supplier_data['audit_summary'], height=100, disabled=True)

        else:
            st.warning("No suppliers available for detailed analysis.")

    with tab4:
        st.markdown("### 🤖 AI-Powered Insights & Recommendations")

        if len(filtered_df) > 0:
            # Top recommendations
            preferred_suppliers = filtered_df[filtered_df['recommendation'] == 'Preferred'].nlargest(3, 'total_eco_score')
            avoid_suppliers = filtered_df[filtered_df['recommendation'] == 'Avoid']
            review_suppliers = filtered_df[filtered_df['recommendation'].isin(['Under Review', 'Caution'])]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### ✅ Top Recommendations")
                if not preferred_suppliers.empty:
                    for _, supplier in preferred_suppliers.iterrows():
                        st.success(f"**{supplier['supplier_name']}** ({supplier['country']})\n"
                                f"Score: {supplier['total_eco_score']:.1f} | "
                                f"Category: {supplier['product_category']}")
                else:
                    st.info("No preferred suppliers in current selection.")

                st.markdown("#### 🔍 Needs Review")
                if not review_suppliers.empty:
                    for _, supplier in review_suppliers.head(3).iterrows():
                        st.warning(f"**{supplier['supplier_name']}** ({supplier['country']})\n"
                                f"Score: {supplier['total_eco_score']:.1f} | "
                                f"Risk: {supplier['risk_level']}")
                else:
                    st.info("No suppliers need review in current selection.")

            with col2:
                st.markdown("#### ❌ Avoid Recommendations")
                if not avoid_suppliers.empty:
                    for _, supplier in avoid_suppliers.head(3).iterrows():
                        st.error(f"**{supplier['supplier_name']}** ({supplier['country']})\n"
                            f"Score: {supplier['total_eco_score']:.1f} | "
                            f"Risk: {supplier['risk_level']}")
                else:
                    st.info("No suppliers to avoid in current selection.")

                # Market insights
                st.markdown("#### 📊 Market Intelligence")

                # Generate dynamic insights based on actual data
                total_suppliers = len(filtered_df)
                avg_score = filtered_df['total_eco_score'].mean()
                top_country = filtered_df['country'].mode().iloc[0] if not filtered_df.empty else "N/A"
                preferred_count = len(preferred_suppliers)

                insights = [
                    f"🌍 **Geographic Diversity**: Your supplier base includes {filtered_df['country'].nunique()} countries, with {top_country} having the most suppliers.",
                    f"📈 **Average Performance**: Current average sustainability score is {avg_score:.1f} across {total_suppliers} suppliers.",
                    f"💚 **Preferred Partners**: {preferred_count} suppliers ({preferred_count/total_suppliers*100:.1f}%) are classified as preferred partners.",
                    f"🏭 **Category Focus**: {filtered_df['product_category'].nunique()} product categories represented.",
                ]

                # Add subcategory insight if available
                if 'sub_category' in filtered_df.columns:
                    insights.append(f"🏷️ **Sub-categories**: {filtered_df['sub_category'].nunique()} sub-categories represented.")

                # Add risk insight if available
                if 'risk_level' in filtered_df.columns:
                    high_risk_count = len(filtered_df[filtered_df['risk_level'] == 'High'])
                    insights.append(f"⚠️ **Risk Assessment**: {high_risk_count} high-risk suppliers require immediate attention.")

                for insight in insights:
                    st.markdown(insight)

        else:
            st.info("Apply filters to view AI insights for your supplier selection.")

    with tab5:
        st.markdown("### 🔮 Supplier Performance Simulation")

        if len(filtered_df) > 0:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Scenario Planning")

                # Supplier selection for simulation
                supplier_choice = st.selectbox("Select Supplier for Simulation",
                                            filtered_df['supplier_name'].unique())

                if supplier_choice:
                    base_data = filtered_df[filtered_df['supplier_name'] == supplier_choice].iloc[0]

                    st.markdown("##### Improvement Scenarios")
                    carbon_improvement = st.slider("Carbon Footprint Improvement (%)", 0, 50, 10)
                    water_improvement = st.slider("Water Management Improvement (%)", 0, 50, 10)
                    waste_improvement = st.slider("Waste Reduction Improvement (%)", 0, 50, 10)
                    social_improvement = st.slider("Social Impact Improvement (%)", 0, 50, 10)

                    # Calculate new scores (only if detailed scores exist)
                    detailed_score_cols = ["carbon_score", "water_score", "waste_score", "social_score"]
                    if all(col in base_data.index for col in detailed_score_cols):
                        new_carbon = min(100, base_data['carbon_score'] * (1 + carbon_improvement/100))
                        new_water = min(100, base_data['water_score'] * (1 + water_improvement/100))
                        new_waste = min(100, base_data['waste_score'] * (1 + waste_improvement/100))
                        new_social = min(100, base_data['social_score'] * (1 + social_improvement/100))

                        new_total_score = (new_carbon + new_water + new_waste + new_social) / 4
                    else:
                        # Use base score with average improvement if detailed scores not available
                        avg_improvement = (carbon_improvement + water_improvement + waste_improvement + social_improvement) / 4
                        new_total_score = min(100, base_data['total_eco_score'] * (1 + avg_improvement/100))
                        new_carbon = new_water = new_waste = new_social = new_total_score

                    st.markdown("##### Investment Required")
                    investment_needed = (carbon_improvement + water_improvement +
                                    waste_improvement + social_improvement) * 10000
                    st.info(f"Estimated Investment: ${investment_needed:,}")

            with col2:
                if supplier_choice:
                    st.markdown("#### Simulation Results")

                    # Before vs After comparison
                    if all(col in base_data.index for col in detailed_score_cols):
                        comparison_data = pd.DataFrame({
                            'Metric': ['Carbon', 'Water', 'Waste', 'Social', 'Overall'],
                            'Current': [base_data['carbon_score'], base_data['water_score'],
                                    base_data['waste_score'], base_data['social_score'],
                                    base_data['total_eco_score']],
                            'Projected': [new_carbon, new_water, new_waste, new_social, new_total_score]
                        })
                    else:
                        comparison_data = pd.DataFrame({
                            'Metric': ['Overall'],
                            'Current': [base_data['total_eco_score']],
                            'Projected': [new_total_score]
                        })

                    fig_comparison = px.bar(comparison_data, x='Metric', y=['Current', 'Projected'],
                                        title="Current vs Projected Performance",
                                        barmode='group',
                                        color_discrete_map={'Current': '#ff7f0e', 'Projected': '#2ca02c'})
                    fig_comparison.update_layout(height=400)
                    st.plotly_chart(fig_comparison, use_container_width=True)

                    # Impact summary
                    score_improvement = new_total_score - base_data['total_eco_score']
                    st.markdown("##### 📊 Impact Summary")

                    if score_improvement > 0:
                        st.success(f"🎯 **Total Score Improvement**: +{score_improvement:.1f} points")
                        st.success(f"📈 **New Overall Score**: {new_total_score:.1f}/100")

                        if new_total_score >= 90:
                            st.success("🌟 **Achievement**: Top-tier sustainability rating!")
                        elif new_total_score >= 80:
                            st.info("✨ **Achievement**: High sustainability performance!")

                        # ROI calculation (only if annual volume exists)
                        if 'annual_volume' in base_data.index and investment_needed > 0:
                            roi_value = (score_improvement * base_data['annual_volume']) / investment_needed
                            st.metric("💰 Estimated ROI", f"{roi_value:.1f}x")
                    else:
                        st.warning("No improvement projected with current settings.")
        else:
            st.info("Select suppliers using the filters to run simulations.")

elif mode == "AI Assistant":
    # Beautiful AI Assistant Interface
    st.markdown("""
    <div class="ai-container">
        <div class="ai-title">🤖 EcoChain AI Assistant</div>
        <div class="ai-subtitle">Your intelligent companion for sustainability insights, data analysis, and visual reporting</div>
    </div>
    """, unsafe_allow_html=True)

    if "show_history" not in st.session_state:
        st.session_state.show_history = False

    # Layout: empty space + chat toggle button on the right
    col1, col2 = st.columns([9, 1])
    with col2:
        show_history = st.checkbox("💬 Chat History", key="history_toggle")

    # Text input
    user_query = st.text_area(
        "",
        placeholder="Ask me anything about suppliers, sustainability metrics, or request visualizations...",
        height=100,
        key="query_input"
    )

    # Keep chat history in session state
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Initialize response state
    if "last_response" not in st.session_state:
        st.session_state["last_response"] = ""

    # Show Previous Messages (only if toggled on)
    if show_history and st.session_state.messages:
        st.markdown("---")
        st.markdown("### 💬 Conversation History")

        for i, msg in enumerate(reversed(st.session_state.messages[-10:])):  # Show last 10 messages
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)

    # Example canned queries
    st.markdown("""
    <div class="example-queries">
        <h4>💡 Example Queries:</h4>
        <ul>
            <li><strong>Data Analysis:</strong> Show me top 5 suppliers with best carbon scores</li>
            <li><strong>Geographic Analysis:</strong> Compare suppliers by country performance</li>
            <li><strong>Certifications:</strong> Show suppliers with Fair Trade certification</li>
            <li><strong>Risk Analysis:</strong> Show me all high-risk suppliers</li>
            <li><strong>Preferred Partners:</strong> List all preferred suppliers</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    run_query_clicked = st.button("Run Query")

    if run_query_clicked:
        if user_query.strip() == "":
            st.warning("⚠️ Please enter a query before running.")
        else:
            with st.spinner("🔄 AI is Thinking..."):
                st.session_state["messages"].append({"role": "user", "content": user_query})
                response = run_ai_query(user_query)
                if response is None:
                    response = "Oops Assistant Can't Answer At The Moment, Check Internet Connection and Retry"

                # Store the response and enable copy button
                st.session_state.last_response = response

            # Display AI response
            st.markdown("""
            <div>
                <h3>🤖 AI Response</h3>
            </div>
            """, unsafe_allow_html=True)
            st.write(response)
            st.session_state["messages"].append({"role": "assistant", "content": response})

elif mode == "Add New Supplier":
    st.markdown("""
    <div class="new-supplier-form">
        <h1 style="text-align: center; margin-bottom: 2rem;">➕ Add New Supplier</h1>
        <p style="text-align: center; margin-bottom: 2rem; opacity: 0.9;">
            Expand your supplier database with comprehensive sustainability metrics
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("new_supplier_form", clear_on_submit=True):
        col1, col2, col3, col4  = st.columns(4)

        with col1:
            st.markdown("### 🏢 Basic Information")
            supplier_name = st.text_input("Supplier Name *", placeholder="Enter supplier name")
            country = st.text_input("Country *", placeholder="e.g., Nigeria, Ghana, Kenya")
            region = st.selectbox("Region *", ["Africa", "Asia", "Europe", "North America", "South America", "Oceania"])

            st.markdown("### 📦 Product Information")
            product_category = st.selectbox(
                "Product Category *",
                ["Electronics", "Textiles", "Agriculture", "Manufacturing", "Energy", "Healthcare", "Automotive", "Food & Beverage"]
            )
            sub_category = st.text_input("Sub Category *", placeholder="e.g., Organic Cotton, Solar Panels")

        with col2:
            st.markdown("### 📜 Certifications & Status")
            certification = st.multiselect(
                "Certifications *",
                ["ISO 14001", "Fair Trade", "Organic", "B-Corp", "LEED", "Carbon Neutral", "GRI", "SA8000", "Forest Stewardship Council"]
            )
            partnership_status = st.selectbox("Partnership Status *", ["Active", "Under Review", "Pending", "Inactive"])

        with col3:
            st.markdown("### 💰 Financial & Risk")
            annual_volume = st.number_input("Annual Volume (USD) *", min_value=0, value=100000, step=10000)
            cost_premium = st.slider("Cost Premium (%) *", -20, 50, 0)
            risk_level = st.selectbox("Risk Level *", ["Low", "Medium", "High"])

        # Full width sections
        st.markdown("### 📅 Audit Information")
        with col4:
            last_audit = st.date_input("Last Audit Date", value=datetime.now().date())

        audit_summary = st.text_area("Audit Summary *", placeholder="Enter detailed audit findings and observations...", height=100)

        st.markdown("### 📸 Product Images")
        uploaded_images = st.file_uploader(
            "Upload Product Images (Optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Upload multiple images to showcase products or facilities"
        )

        # Form submission
        col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
        with col_submit2:
            submitted = st.form_submit_button("🚀 Add Supplier", use_container_width=True)

        if submitted:
            # Validation
            required_fields = [supplier_name, country, region, product_category, sub_category, certification, partnership_status, audit_summary]
            if not all(required_fields) or annual_volume is None or cost_premium is None or risk_level is None:
                st.error("❌ Please fill in all required fields marked with *")
            else:
                # Create new supplier record
                new_supplier = {
                    'supplier_name': supplier_name,
                    'country': country,
                    'region': region,
                    'product_category': product_category,
                    'sub_category': sub_category if sub_category else "General",
                    'certification': certification if certification else [],
                    'partnership_status': partnership_status,
                    'annual_volume': annual_volume,
                    'cost_premium': cost_premium,
                    'risk_level': risk_level,
                    'last_audit': last_audit.strftime('%Y-%m-%d'),
                    'audit_summary': audit_summary,
                    'uploaded_images': uploaded_images if uploaded_images else []
                }

                with st.spinner("🔄 Adding Supplier, This may take a while..."):
                    condition = update_supplier(new_supplier)
                    if condition is False:
                        st.error("Oops You Currently Don't Have Access To Database, Contact Developer")
                    else:
                        # Clear cache to reload data
                        load_supplier_data.clear()

                        # Success message
                        st.markdown(f'''
                        <div class="success-message">
                            ✅ Supplier "{supplier_name}" added successfully!<br>
                        </div>
                        ''', unsafe_allow_html=True)

                        st.balloons()

                        # Show summary
                        st.markdown("### 📊 Supplier Summary")
                        summary_data = pd.DataFrame([{
                            'Field': k.replace('_', ' ').title(),
                            'Value': str(v) if not isinstance(v, list) else ', '.join(v) if v else 'None'
                        } for k, v in new_supplier.items() if k not in ['uploaded_images']])

                        st.dataframe(summary_data, use_container_width=True, hide_index=True)


# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p>🌍 <strong>EcoChain AI Dashboard</strong> | Powered by Big Query AI | Last Updated: {}</p>
    <p>For support or feedback, contact: nwabekepraisejah@gmail.com</p>
    <p>All Data Used Was Synthetic</p>
</div>
""".format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)
