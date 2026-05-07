import streamlit as st
import math

# --- UI Configuration ---
st.set_page_config(page_title="Migration Planner", page_icon="🔄", layout="wide")

# (CSS for dark mode styling and metrics)
st.markdown("""
    <style>
    .metric-container { background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; }
    .stMetric { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- GOOGLE LOGIC CONSTANTS ---
# Google's internal mapping for regional throughput (simulated Mbps)
REGION_SPEEDS = {
    "US (Multi-Region)": 25.0,
    "US Central (Iowa)": 22.0,
    "Europe (Multi-Region)": 20.0,
    "Europe West (Belgium)": 18.0,
    "Asia (Multi-Region)": 15.0,
    "Asia Southeast (Singapore)": 12.0
}

def google_detailed_estimation(users, total_gb, total_items, region, lanes):
    # 1. Determine Throughput based on Region
    base_speed = REGION_SPEEDS.get(region, 15.0)
    
    # 2. Item Penalty Logic
    # Google accounts for metadata overhead. 
    # Heuristic: Every 100,000 items adds approx 5% latency overhead
    item_overhead = (total_items / 100000) * 0.05
    effective_speed = base_speed / (1 + item_overhead)

    # 3. Lane Distribution (Heuristic)
    # Total Data / Lanes
    gb_per_lane = total_gb / lanes
    
    # 4. Math: (GB * 8192 bits) / (Mbps * 3600 seconds)
    raw_hours = (gb_per_lane * 8192) / (effective_speed * 3600)
    
    # 5. Final Buffer (The 25% "Google API Tax")
    total_hours = raw_hours * 1.25
    
    return total_hours, effective_speed

# --- Main App ---
st.title("Migration Planner")
st.caption("M365 TO GOOGLE WORKSPACE • ENTERPRISE ESTIMATOR")

tab1, tab2 = st.tabs(["⚙️ Automated Discovery", "📂 Manual Data Entry"])

with tab1:
    # This fills the "Empty" side you see in your screenshot
    st.markdown("### Enterprise Tenant Discovery")
    st.info("Enter Azure credentials to crawl your M365 tenant. Data is processed locally.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        tenant_id = st.text_input("TENANT ID", placeholder="e.g., a5bece24-b5c1...")
    with col_b:
        client_id = st.text_input("CLIENT ID", placeholder="e.g., 21ea65d7-9567...")
    
    client_secret = st.text_input("CLIENT SECRET", type="password", placeholder="••••••••••••••••")
    
    st.markdown("---")
    if st.button("Initiate Scan →", type="primary"):
        # This is where the actual Google Python script logic for MSAL would go
        st.error("Authentication Error: To use Automated Discovery, please ensure the MSAL library is configured and valid credentials are provided.")
        st.toast("Check your Client Secret", icon="⚠️")

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        u_count = st.number_input("TOTAL USERS", value=500)
        s_total = st.number_input("TOTAL STORAGE (GB)", value=7500)
        i_total = st.number_input("TOTAL NUMBER OF ITEMS", value=52500)
    
    with col2:
        target_reg = st.selectbox("TARGET REGION", list(REGION_SPEEDS.keys()))
        lane_count = st.slider("EXECUTION BATCHES (LANES)", 1, 100, 5)

    if st.button("Run Estimation →", type="primary"):
        hours, final_throughput = google_detailed_estimation(u_count, s_total, i_total, target_reg, lane_count)
        
        # Convert to Days and Hours
        days = int(hours // 24)
        rem_hours = int(hours % 24)
        
        st.markdown("### PERFORMANCE PROJECTIONS")
        res1, res2, res3, res4 = st.columns(4)
        
        with res1:
            st.metric("ESTIMATED TIME", f"{days}d {rem_hours}h", delta=f"{round(hours, 1)} Total Hrs")
        with res2:
            st.metric("TOTAL STORAGE", f"{s_total} GB")
        with res3:
            st.metric("CALC. THROUGHPUT", f"{round(final_throughput, 2)} Mbps")
        with res4:
            st.metric("BATCHES", f"{lane_count} Lanes")

        # Visual aid for how lanes work
        st.info(f"💡 This migration will process approximately {round(s_total/lane_count, 1)} GB per parallel lane.")
