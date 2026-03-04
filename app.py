import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io

# --- 1. SETUP (100% OFFLINE, NO API) ---
st.set_page_config(page_title="GCC Risk Hub", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>.block-container {padding-top: 1rem;}</style>""", unsafe_allow_html=True)

st.title("🏦 GCC Risk Intelligence & Automation Hub")

# --- 2. FILE UPLOAD & LOGIC ---
uploaded_file = st.sidebar.file_uploader("📂 Upload Dataset (CSV)", type="csv")

if uploaded_file is not None:
    @st.cache_data
    def load_data(file):
        df = pd.read_csv(file)
        df.columns = [c.strip().lower() for c in df.columns]
        return df

    df = load_data(uploaded_file)
    
    # Smart Context Detection
    context = "General Finance"
    if 'class' in df.columns and 'v1' in df.columns: context = "Credit Card Fraud"
    elif 'exited' in df.columns or 'churn' in df.columns: context = "Customer Churn"
    elif 'loan_status' in df.columns or 'cibil_score' in df.columns: context = "Loan Risk"
    elif 'accountbalance' in df.columns or 'balance' in df.columns: context = "Banking Liquidity"

    num_cols = df.select_dtypes(include=['number']).columns
    
    # --- DYNAMIC RISK CALCULATION ---
    total_rows = len(df)
    risky_rows_count = 0
    
    if not num_cols.empty:
        risk_mask = pd.Series([False] * total_rows)
        cols_to_scan = num_cols[:10] if total_rows > 50000 else num_cols
        
        for col in cols_to_scan:
            mean_val = df[col].mean()
            std_val = df[col].std()
            risk_mask = risk_mask | ((df[col] > mean_val + 2*std_val) | (df[col] < mean_val - 2*std_val))
        
        risky_rows_count = risk_mask.sum()

    risk_pct = (risky_rows_count / total_rows) * 100 if total_rows > 0 else 0
    safe_pct = 100 - risk_pct

    st.sidebar.success(f"✅ Active: {total_rows} Rows")
    st.sidebar.info(f"📂 Mode: {context}")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data Inspector", "⚠️ Automated Risk Scanner", "🧠 Strategy Engine", "📘 Layman Guide"])

    # ========================== TAB 1: INSPECTOR ==========================
    with tab1:
        st.subheader("1️⃣ Deep Dive Inspector")
        total_cells = df.shape[0] * df.shape[1]
        
        # Large Dataset Crash Prevention
        if total_cells > 200000:
            st.warning("⚠️ Large Dataset: Optimization Mode Enabled (Styling Disabled)")
            st.dataframe(df, use_container_width=True, height=400)
        else:
            view = st.radio("View Mode:", ["Full Data", "Missing Only"], horizontal=True)
            if view == "Full Data":
                st.dataframe(df.style.highlight_null(color='pink'), use_container_width=True, height=400)
            else:
                missing = df[df.isnull().any(axis=1)]
                if not missing.empty:
                    st.dataframe(missing.style.highlight_null(color='red'), use_container_width=True)
                else:
                    st.success("Data is Clean (No Missing Values)")

        c1, c2 = st.columns(2)
        with c1:
            st.write("### 📉 Statistics")
            st.dataframe(df.describe().T, use_container_width=True)
        with c2:
            st.write("### 📈 Distribution")
            target_viz = st.selectbox("Visualize:", df.columns[:20]) 
            fig, ax = plt.subplots(figsize=(6, 2.5))
            try:
                plot_data = df[target_viz].sample(5000) if len(df) > 5000 else df[target_viz]
                if df[target_viz].dtype in ['int64', 'float64']:
                    sns.histplot(plot_data, kde=True, ax=ax, color='teal')
                else:
                    sns.countplot(y=plot_data, ax=ax, palette="viridis", order=plot_data.value_counts().head(10).index)
                st.pyplot(fig)
            except: 
                st.error("Cannot plot this column")

    # ========================== TAB 2: RISK SCANNER ==========================
    with tab2:
        st.subheader("🚩 Automated Risk Scanner")
        if not num_cols.empty:
            scan_cols = num_cols[:15]
            for col in scan_cols:
                mean_val = df[col].mean()
                std_val = df[col].std()
                upper = mean_val + (2 * std_val)
                lower = mean_val - (2 * std_val)
                
                outliers = df[(df[col] > upper) | (df[col] < lower)]
                count = len(outliers)
                is_risky = count > 0
                
                label = f"⚠️ {col.upper()} ({count} Outliers)" if is_risky else f"✅ {col.upper()} (Stable)"
                
                with st.expander(label, expanded=is_risky):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if is_risky:
                            st.error("High Risk Detected")
                            st.metric("Outliers", count, delta="Action Needed", delta_color="inverse")
                        else:
                            st.success("Within Safe Limits")
                            st.metric("Outliers", 0)
                    with c2:
                        fig_box, ax_box = plt.subplots(figsize=(6, 2))
                        color = 'salmon' if is_risky else 'lightgreen'
                        plot_data = df[col].sample(5000) if len(df) > 5000 else df[col]
                        sns.boxplot(x=plot_data, ax=ax_box, color=color)
                        st.pyplot(fig_box)

    # ========================== TAB 3: STRATEGY (OFFLINE RULE-BASED) ==========================
    with tab3:
        st.subheader("🧠 Strategic Business Consultant")
        c1, c2 = st.columns([2, 1])
        
        with c1:
            if context == "Credit Card Fraud":
                st.error(f"🚨 **CRITICAL:** Potential Fraud Volume: {risk_pct:.2f}%")
                st.markdown("**Action Plan:**\n1. Freeze accounts with >3 outliers.\n2. Enable 2FA for 'Class 1' transactions.")
            elif context == "Customer Churn":
                st.error(f"🚨 **CRITICAL:** Churn Risk Volume: {risk_pct:.2f}%")
                st.markdown("**Action Plan:**\n1. Loyalty Bonus for tenure > 3 yrs.\n2. Call customers with 'Exited=1'.")
            elif context == "Banking Liquidity":
                st.error(f"🚨 **CRITICAL:** Variance Risk: {risk_pct:.2f}%")
                st.markdown("**Action Plan:**\n1. Audit top 1% high-balance accounts.\n2. Re-activate zero-balance users.")
            else:
                st.info(f"ℹ️ **Observation:** General Audit (Variance: {risk_pct:.2f}%)")
                st.markdown("**Action Plan:**\n1. Monitor daily logs.\n2. Manual spot check on red flags.")
                
        with c2:
            st.write("### 🚀 Real-Time Impact")
            st.caption(f"Based on {total_rows} records")
            fig_pie, ax_pie = plt.subplots(figsize=(4, 3))
            
            if risk_pct == 0: 
                sizes, labels, colors = [100], ['Safe'], ['lightgreen']
            else:
                sizes = [risk_pct, safe_pct]
                labels = ['At Risk', 'Safe']
                colors = ['salmon', 'lightgreen']
                
            ax_pie.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            st.pyplot(fig_pie)

    # ========================== TAB 4: LAYMAN GUIDE ==========================
    with tab4:
        st.subheader("📘 Guide for Everyone")
        with st.expander(f"❓ What is '{context}'?", expanded=True):
            if context == "Credit Card Fraud": st.write("Think of this as a **Thief Detector**. We look for weird patterns (Outliers) to catch fraud.")
            elif context == "Customer Churn": st.write("Think of a **Leaky Bucket**. We are finding the holes (Customers leaving) to patch them.")
            elif context == "Banking Liquidity": st.write("Think of a **Wallet Inspection**. Checking for empty wallets and suspicious fat wallets.")
            else: st.write("This is a digital health checkup for your financial data.")
        
        with st.expander("🔮 How does AI predict?"):
            st.write("It uses statistics (Mean + 2SD). Imagine a classroom average is 50%. If someone gets 99%, they are an 'Outlier' (Special Case).")

    # --- EXCEL EXPORT (BUG FIXED) ---
    st.sidebar.divider()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.head(10000).to_excel(writer, sheet_name='Raw Data', index=False)
        df.describe().to_excel(writer, sheet_name='Statistics')
    
    buffer.seek(0) # FIX: Makes sure the Excel file isn't blank
    st.sidebar.download_button("📊 Download Report", buffer, "Audit_Report.xlsx")

else:
    st.info("👈 Upload CSV to Start")
