"""
Transaction Anomaly Detector Dashboard
========================================
Detects suspicious patterns in carrier transactions using ML and rule-based methods.
Run with: python -m streamlit run app/detector.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Transaction Anomaly Detector | Relay Product Excellence",
    page_icon="🔍",
    layout="wide"
)

# ============================================================
# LOAD DATA
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv("data/transactions.csv")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("Data not found! Run `python data/generate_transactions.py` first.")
    st.stop()

# ============================================================
# ML ANOMALY DETECTION MODEL
# ============================================================
@st.cache_data
def run_anomaly_detection(data):
    """Run Isolation Forest anomaly detection"""
    # Features for ML model
    features = ['hour_of_day', 'session_duration_seconds', 'pages_visited',
                'failed_attempts', 'amount', 'risk_score']

    X = data[features].fillna(0)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Isolation Forest
    model = IsolationForest(
        contamination=0.1,  # Expect ~10% anomalies
        random_state=42,
        n_estimators=100
    )
    predictions = model.fit_predict(X_scaled)

    # -1 = anomaly, 1 = normal
    data = data.copy()
    data['ml_prediction'] = predictions
    data['ml_anomaly'] = predictions == -1
    data['anomaly_score'] = -model.score_samples(X_scaled)  # Higher = more anomalous

    return data, model

df_with_ml, model = run_anomaly_detection(df)

# ============================================================
# HEADER
# ============================================================
st.title("🔍 Transaction Anomaly Detector")
st.markdown("**Relay Product Excellence | Transaction Integrity Monitoring**")
st.markdown("---")

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Settings")

    # Detection method
    detection_method = st.radio(
        "Detection Method",
        ["Both (ML + Rules)", "ML Only (Isolation Forest)", "Rules Only"],
        index=0
    )

    # Risk threshold
    risk_threshold = st.slider(
        "Risk Score Threshold",
        min_value=30,
        max_value=90,
        value=60,
        help="Transactions above this score are flagged"
    )

    # Date range
    st.markdown("---")
    st.header("📅 Date Range")
    min_date = df['timestamp'].min().date()
    max_date = df['timestamp'].max().date()

    date_range = st.date_input(
        "Select range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Region filter
    st.markdown("---")
    st.header("🌍 Region")
    selected_regions = st.multiselect(
        "Filter by region",
        options=df['region'].unique(),
        default=df['region'].unique()
    )

    # Anomaly type filter
    st.markdown("---")
    st.header("🚨 Anomaly Type")
    anomaly_types = df[df['is_anomaly'] == True]['anomaly_type'].unique()
    selected_anomalies = st.multiselect(
        "Filter by type",
        options=anomaly_types,
        default=anomaly_types
    )

# ============================================================
# APPLY FILTERS
# ============================================================
filtered_df = df_with_ml.copy()

# Date filter
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['timestamp'].dt.date >= date_range[0]) &
        (filtered_df['timestamp'].dt.date <= date_range[1])
    ]

# Region filter
filtered_df = filtered_df[filtered_df['region'].isin(selected_regions)]

# ============================================================
# DETECTION RESULTS
# ============================================================
# Determine which transactions are flagged based on method
if detection_method == "ML Only (Isolation Forest)":
    filtered_df['flagged'] = filtered_df['ml_anomaly']
elif detection_method == "Rules Only":
    filtered_df['flagged'] = filtered_df['risk_score'] >= risk_threshold
else:  # Both
    filtered_df['flagged'] = (filtered_df['ml_anomaly']) | (filtered_df['risk_score'] >= risk_threshold)

flagged_df = filtered_df[filtered_df['flagged'] == True]
normal_df = filtered_df[filtered_df['flagged'] == False]

# ============================================================
# KPI METRICS
# ============================================================
st.subheader("📊 Detection Summary")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Total Transactions", len(filtered_df))

with col2:
    st.metric("Flagged", len(flagged_df), delta_color="inverse")

with col3:
    flag_rate = len(flagged_df) / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
    st.metric("Flag Rate", f"{flag_rate:.1f}%", delta_color="inverse")

with col4:
    # True positives (flagged AND actually anomalous)
    true_positives = len(flagged_df[flagged_df['is_anomaly'] == True])
    st.metric("True Positives", true_positives)

with col5:
    # Precision
    precision = true_positives / len(flagged_df) * 100 if len(flagged_df) > 0 else 0
    st.metric("Precision", f"{precision:.1f}%")

with col6:
    # Recall
    total_actual_anomalies = len(filtered_df[filtered_df['is_anomaly'] == True])
    recall = true_positives / total_actual_anomalies * 100 if total_actual_anomalies > 0 else 0
    st.metric("Recall", f"{recall:.1f}%")

st.markdown("---")

# ============================================================
# MODEL PERFORMANCE
# ============================================================
st.subheader("🎯 Model Performance")

col1, col2, col3 = st.columns(3)

with col1:
    # Confusion matrix style
    tp = len(filtered_df[(filtered_df['flagged'] == True) & (filtered_df['is_anomaly'] == True)])
    fp = len(filtered_df[(filtered_df['flagged'] == True) & (filtered_df['is_anomaly'] == False)])
    tn = len(filtered_df[(filtered_df['flagged'] == False) & (filtered_df['is_anomaly'] == False)])
    fn = len(filtered_df[(filtered_df['flagged'] == False) & (filtered_df['is_anomaly'] == True)])

    confusion_data = pd.DataFrame({
        'Metric': ['True Positives (Caught)', 'False Positives (False Alarm)',
                   'True Negatives (Correct Pass)', 'False Negatives (Missed)'],
        'Count': [tp, fp, tn, fn],
        'Status': ['✅ Good', '⚠️ Investigate', '✅ Good', '🔴 Dangerous']
    })
    st.dataframe(confusion_data, use_container_width=True, hide_index=True)

with col2:
    # F1 Score
    f1 = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) > 0 else 0
    accuracy = (tp + tn) / len(filtered_df) * 100 if len(filtered_df) > 0 else 0

    st.metric("F1 Score", f"{f1:.3f}")
    st.metric("Accuracy", f"{accuracy:.1f}%")
    st.metric("False Positive Rate", f"{fp/(fp+tn)*100:.1f}%" if (fp+tn) > 0 else "0%")

with col3:
    # Detection breakdown
    fig_detection = px.pie(
        values=[tp, fp, tn, fn],
        names=['True Positive', 'False Positive', 'True Negative', 'False Negative'],
        title='Detection Breakdown',
        color_discrete_sequence=['#2ecc71', '#f39c12', '#3498db', '#e74c3c']
    )
    fig_detection.update_layout(height=250)
    st.plotly_chart(fig_detection, use_container_width=True)

st.markdown("---")

# ============================================================
# CHARTS ROW 1: Timeline & Risk Distribution
# ============================================================
st.subheader("📈 Anomaly Analysis")

col1, col2 = st.columns(2)

with col1:
    # Transaction timeline with anomalies highlighted
    timeline_data = filtered_df.groupby(['date', 'flagged']).size().reset_index(name='count')
    timeline_data['Status'] = timeline_data['flagged'].map({True: 'Flagged', False: 'Normal'})

    fig_timeline = px.bar(
        timeline_data,
        x='date',
        y='count',
        color='Status',
        title='Daily Transaction Volume (Normal vs Flagged)',
        color_discrete_map={'Normal': '#3498db', 'Flagged': '#e74c3c'},
        barmode='stack'
    )
    fig_timeline.update_layout(height=400)
    st.plotly_chart(fig_timeline, use_container_width=True)

with col2:
    # Risk score distribution
    fig_risk = px.histogram(
        filtered_df,
        x='risk_score',
        color='is_anomaly',
        nbins=30,
        title='Risk Score Distribution (Actual Anomalies vs Normal)',
        color_discrete_map={True: '#e74c3c', False: '#3498db'},
        barmode='overlay',
        opacity=0.7
    )
    fig_risk.add_vline(x=risk_threshold, line_dash="dash", line_color="red",
                       annotation_text=f"Threshold ({risk_threshold})")
    fig_risk.update_layout(height=400)
    st.plotly_chart(fig_risk, use_container_width=True)

# ============================================================
# CHARTS ROW 2: Patterns
# ============================================================
col1, col2 = st.columns(2)

with col1:
    # Anomalies by hour of day
    hourly_anomalies = filtered_df.groupby(['hour_of_day', 'flagged']).size().reset_index(name='count')
    hourly_anomalies['Status'] = hourly_anomalies['flagged'].map({True: 'Flagged', False: 'Normal'})

    fig_hourly = px.bar(
        hourly_anomalies,
        x='hour_of_day',
        y='count',
        color='Status',
        title='Transactions by Hour of Day',
        color_discrete_map={'Normal': '#3498db', 'Flagged': '#e74c3c'},
        barmode='group'
    )
    fig_hourly.update_layout(height=350, xaxis_title='Hour (0-23)')
    st.plotly_chart(fig_hourly, use_container_width=True)

with col2:
    # Anomaly types breakdown
    anomaly_breakdown = flagged_df[flagged_df['is_anomaly'] == True]['anomaly_type'].value_counts().reset_index()
    anomaly_breakdown.columns = ['Anomaly Type', 'Count']

    if len(anomaly_breakdown) > 0:
        fig_types = px.bar(
            anomaly_breakdown,
            x='Count',
            y='Anomaly Type',
            orientation='h',
            title='Detected Anomaly Types',
            color='Count',
            color_continuous_scale='Reds'
        )
        fig_types.update_layout(height=350)
        st.plotly_chart(fig_types, use_container_width=True)
    else:
        st.info("No anomalies detected with current filters.")

# ============================================================
# CHARTS ROW 3: Scatter & Regional
# ============================================================
col1, col2 = st.columns(2)

with col1:
    # Scatter plot: Session Duration vs Risk Score
    fig_scatter = px.scatter(
        filtered_df.sample(min(500, len(filtered_df))),
        x='session_duration_seconds',
        y='risk_score',
        color='flagged',
        title='Session Duration vs Risk Score',
        color_discrete_map={True: '#e74c3c', False: '#3498db'},
        opacity=0.6,
        hover_data=['carrier_name', 'transaction_type', 'anomaly_type']
    )
    fig_scatter.update_layout(height=350)
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    # Regional anomaly distribution
    regional_anomalies = filtered_df.groupby('region').agg(
        total=('flagged', 'count'),
        flagged=('flagged', 'sum')
    ).reset_index()
    regional_anomalies['flag_rate'] = (regional_anomalies['flagged'] / regional_anomalies['total'] * 100).round(1)

    fig_regional = px.bar(
        regional_anomalies,
        x='region',
        y='flag_rate',
        title='Anomaly Rate by Region (%)',
        color='flag_rate',
        color_continuous_scale='RdYlGn_r'
    )
    fig_regional.update_layout(height=350)
    st.plotly_chart(fig_regional, use_container_width=True)

st.markdown("---")

# ============================================================
# FLAGGED TRANSACTIONS TABLE
# ============================================================
st.subheader("🚨 Flagged Transactions")

if len(flagged_df) > 0:
    # Filter by anomaly type if selected
    display_flagged = flagged_df.copy()
    if selected_anomalies is not None and len(selected_anomalies) > 0:
        display_flagged = display_flagged[
            (display_flagged['anomaly_type'].isin(selected_anomalies)) |
            (display_flagged['is_anomaly'] == False)  # Keep false positives too
        ]

    display_cols = [
        'transaction_id', 'carrier_name', 'transaction_type', 'timestamp',
        'risk_score', 'anomaly_type', 'region', 'hour_of_day',
        'session_duration_seconds', 'failed_attempts', 'is_anomaly'
    ]

    display_data = display_flagged[display_cols].sort_values('risk_score', ascending=False).head(50)
    display_data.columns = [
        'Transaction ID', 'Carrier', 'Type', 'Timestamp',
        'Risk Score', 'Anomaly Type', 'Region', 'Hour',
        'Session (sec)', 'Failed Attempts', 'Actual Anomaly'
    ]

    st.dataframe(display_data, use_container_width=True, height=400)
else:
    st.success("No flagged transactions with current settings!")

st.markdown("---")

# ============================================================
# INVESTIGATION PANEL
# ============================================================
st.subheader("🔎 Transaction Investigation")

selected_txn = st.selectbox(
    "Select a flagged transaction to investigate:",
    options=flagged_df['transaction_id'].head(20).tolist() if len(flagged_df) > 0 else ["No flagged transactions"]
)

if selected_txn != "No flagged transactions" and len(flagged_df) > 0:
    txn = flagged_df[flagged_df['transaction_id'] == selected_txn].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Transaction Details**")
        st.write(f"- **ID:** {txn['transaction_id']}")
        st.write(f"- **Type:** {txn['transaction_type']}")
        st.write(f"- **Time:** {txn['timestamp']}")
        st.write(f"- **Document:** {txn['document_type']}")
        st.write(f"- **Amount:** ${txn['amount']:.2f}")

    with col2:
        st.markdown("**Carrier Info**")
        st.write(f"- **Name:** {txn['carrier_name']}")
        st.write(f"- **ID:** {txn['carrier_id']}")
        st.write(f"- **Region:** {txn['region']}")
        st.write(f"- **Email:** {txn['email']}")
        st.write(f"- **Phone:** {txn['phone']}")

    with col3:
        st.markdown("**Risk Indicators**")
        st.write(f"- **Risk Score:** {txn['risk_score']}")
        st.write(f"- **Anomaly Type:** {txn['anomaly_type']}")
        st.write(f"- **Hour:** {txn['hour_of_day']}:00")
        st.write(f"- **Failed Attempts:** {txn['failed_attempts']}")
        st.write(f"- **Session:** {txn['session_duration_seconds']}s")
        st.write(f"- **IP:** {txn['ip_address']}")

    # Risk assessment
    st.markdown("---")
    if txn['risk_score'] >= 80:
        st.error(f"🔴 **HIGH RISK** — Risk Score: {txn['risk_score']}. Immediate investigation recommended.")
    elif txn['risk_score'] >= 60:
        st.warning(f"🟡 **MEDIUM RISK** — Risk Score: {txn['risk_score']}. Review within 24 hours.")
    else:
        st.info(f"🔵 **LOW RISK** — Risk Score: {txn['risk_score']}. Flagged by ML model, may be false positive.")

    # Recommendation
    recommendations = {
        "DUPLICATE_SUBMISSION": "Check if same document was submitted multiple times. Verify carrier identity.",
        "VELOCITY_SPIKE": "Unusual number of transactions in short time. Check for automated/bot activity.",
        "UNUSUAL_HOUR": "Transaction at unusual hour (1-5 AM). Verify if carrier is in a different timezone.",
        "FAKE_IDENTITY": "Suspicious identity markers detected. Cross-reference with government databases.",
        "ADDRESS_MISMATCH": "Address inconsistency detected. Verify physical location of carrier.",
        "RAPID_CHANGES": "Multiple profile changes in short time. May indicate account takeover.",
        "BULK_REGISTRATION": "Multiple registrations from same IP. Possible fraud ring.",
        "SUSPICIOUS_PATTERN": "General suspicious pattern detected. Manual review recommended.",
        "NONE": "Flagged by ML model based on behavioral patterns. Review transaction details."
    }

    st.markdown("**📋 Recommended Action:**")
    st.info(recommendations.get(txn['anomaly_type'], "Manual review recommended."))

# ============================================================
# FOOTER
# ============================================================
st.markdown("---")
st.markdown(
    "Built by **Dhanya** | Relay Product Excellence Portfolio Project | "
    "Powered by Python + Streamlit + Scikit-Learn + Plotly"
)
