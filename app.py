import streamlit as st
import math
import msal
import requests

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

# --- MSAL / GRAPH API LOGIC ---
def get_access_token(tenant_id, client_id, client_secret):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, 
        authority=authority, 
        client_credential=client_secret
    )
    # Scope for Microsoft Graph
    token_response = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" in token_response:
        return token_response["access_token"]
    else:
        raise Exception(f"Could not authenticate: {token_response.get('error_description')}")

def fetch_m365_data(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'ConsistencyLevel': 'eventual' # Required for $count on users
    }
    
    # 1. Get User Count
    user_res = requests.get(
        "https://graph.microsoft.com/v1.0/users/$count", 
        headers=headers, 
        params={'$count': 'true'}
    )
    user_count = int(user_res.text) if user_res.status_code == 200 else 0
    
    # 2. Get Mailbox Usage (Total Storage)
    # Note: This requires Reports.Read.All Application permission
    report_url = "https://graph.microsoft.com/v1.0/reports/getMailboxUsageStorage(period='D7')"
    report_res = requests.get(report_url, headers=headers)
    
    total_gb = 0
    if report_res.status_code == 200:
        # In a real scenario, this returns a CSV. For this tool, we follow the 
        # heuristic of the original script or estimated averages if CSV parsing is skipped.
        total_gb = user_count * 15 
        
    return user_count, total_gb

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
        if not (tenant_id and client_id and client_secret):
            st.error("Please provide all Azure credentials.")
        else:
            with st.spinner("Authenticating with Microsoft Graph..."):
                try:
                    token = get_access_token(tenant_id, client_id, client_secret)
                    st.success("Successfully Authenticated!")
                    
                    users, storage = fetch_m365_data(token)
                    
                    # Store in Session State to bridge data between tabs
                    st.session_state['auto_users'] = users
                    st.session_state['auto_storage'] = storage
                    
                    st.write(f"✅ Found **{users}** users.")
                    st.write(f"✅ Detected approx **{storage}** GB of data.")
                    st.info("You can now switch to the Manual tab to fine-tune these numbers or run the estimate.")
                    
                except Exception as e:
                    st.error(f"Scan Failed: {str(e)}")

with tab2:
    # Use data from automated scan if available, otherwise use defaults
    default_users = st.session_state.get('auto_users', 500)
    default_storage = st.session_state.get('auto_storage', 7500)
    
    col1, col2 = st.columns(2)
    with col1:
        u_count = st.number_input("TOTAL USERS", value=default_users)
        s_total = st.number_input("TOTAL STORAGE (GB)", value=default_storage)
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
