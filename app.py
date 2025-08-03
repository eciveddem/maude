import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Apple-Style MAUDE App", layout="wide")

st.markdown("""
<div style='text-align: right; padding: 0.5rem;'>
    <a href='https://www.buymeacoffee.com/eciveddem' target='_blank'>
        <img src='https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png' height='32' />
    </a>
</div>
""", unsafe_allow_html=True)

# --- Apple-like styling ---
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #ffffff;
    color: #111;
}
div.stButton > button {
    background-color: #007aff;
    color: white;
    border-radius: 8px;
    font-size: 16px;
    padding: 0.5rem 1.2rem;
    border: none;
    margin-top: 1rem;
}
table {
    font-size: 14px;
    width: 100%;
    border-collapse: collapse;
    background-color: #000;
    color: #fff;
}
th, td {
    border-bottom: 1px solid #444;
    padding: 8px 12px;
    text-align: left;
}
th {
    background-color: #222;
    font-weight: 600;
}
tr:nth-child(even) {
    background-color: #111;
}
</style>
""", unsafe_allow_html=True)

st.title("🔍 Medical Device Adverse Event Search")

# Tabs layout
tab1, tab2, tab3 = st.tabs(["🔎 Search", "📋 Results", "📊 Charts"])

with tab1:
    st.markdown("#### Find Adverse Events by Device Info")
    col1, col2 = st.columns(2)
    with col1:
        search_option = st.selectbox("Search by", ["Device Generic Name", "Product Code", "UDI-DI"])
    with col2:
        search_term = st.text_input("Search term", placeholder="e.g. defibrillator")

    col3, col4 = st.columns(2)
    with col3:
        start_date, end_date = st.date_input(
            "Date received range",
            value=(date(2020, 1, 1), date.today())
        )
    with col4:
        limit = st.slider("Number of records", 1, 100, 25)

    search_button = st.button("🔎 Search")
col_recent1, col_recent2 = st.columns(2)
with col_recent1:
    pull_malfunctions_button = st.button("📥 Pull 100 Malfunctions")
with col_recent2:
    pull_injuries_button = st.button("📥 Pull 100 Injuries")

if 'results_df' not in st.session_state:
    st.session_state.results_df = pd.DataFrame()

if search_button or pull_malfunctions_button or pull_injuries_button:
    base_url = "https://api.fda.gov/device/event.json"
    if pull_malfunctions_button:
        url = f"{base_url}?search=event_type:Malfunction&sort=date_received:desc&limit=100"
    elif pull_injuries_button:
        url = f"{base_url}?search=event_type:Injury&sort=date_received:desc&limit=100"
    else:
        if search_option == "Device Generic Name":
            query = f"device.generic_name:{search_term}"
        elif search_option == "Product Code":
            query = f"device.device_report_product_code:{search_term}"
        elif search_option == "UDI-DI":
            query = f"device.udi_di:{search_term}"
        else:
            query = ""

        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        query += f"+AND+date_received:[{start_str}+TO+{end_str}]"
        url = f"{base_url}?search={query}&sort=date_received:desc&limit={limit}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        results = response.json().get("results", [])
        records = []
        for entry in results:
            device = entry.get("device", [{}])[0]
            openfda = device.get("openfda", {})
            pma_number = entry.get("pma_pmn_number")
            if pma_number and pma_number.startswith("K"):
                pma_display = f'<a href="https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID={pma_number}" target="_blank">{pma_number}</a>'
            else:
                pma_display = pma_number or ""

            records.append({
                "Manufacturer": device.get("manufacturer_d_name"),
                "Brand Name": device.get("brand_name"),
                "Generic Name": device.get("generic_name"),
                "Product Code": device.get("device_report_product_code"),
                "UDI DI": device.get("udi_di"),
                "Device Name (FDA)": openfda.get("device_name"),
                "Device Class": openfda.get("device_class"),
                "510k/PMA Number": pma_display,
                "Event Type": entry.get("event_type"),
                "Event Date": entry.get("date_of_event"),
                "Received Date": entry.get("date_received"),
                "FEI Number": "; ".join(openfda.get("fei_number", [])),
            })

        st.session_state.results_df = pd.DataFrame(records)
    except Exception as e:
        st.error(f"❌ Error: {e}")

with tab2:
    if not st.session_state.results_df.empty:
        st.markdown("#### 📋 Results Table")
        html_table = st.session_state.results_df.to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)
        st.download_button("⬇️ Download CSV", st.session_state.results_df.to_csv(index=False), "maude_results.csv")
    else:
        st.info("No results to display yet.")

with tab3:
    df = st.session_state.results_df
    if not df.empty:
        st.markdown("#### 📊 Event Pareto Charts")

        malfunction_df = df[df["Event Type"] == "Malfunction"]
        if not malfunction_df.empty:
            fig1, ax1 = plt.subplots(figsize=(12, 3))
            malfunction_df["Manufacturer"].value_counts().plot(kind="bar", ax=ax1)
            ax1.set_title("Malfunction Events by Manufacturer")
            ax1.set_ylabel("Count")
            st.pyplot(fig1)

        injury_df = df[df["Event Type"] == "Injury"]
        if not injury_df.empty:
            fig2, ax2 = plt.subplots(figsize=(12, 3))
            injury_df["Manufacturer"].value_counts().plot(kind="bar", ax=ax2)
            ax2.set_title("Injury Events by Manufacturer")
            ax2.set_ylabel("Count")
            st.pyplot(fig2)

        if "Product Code" in df.columns:
            fig3, ax3 = plt.subplots(figsize=(12, 3))
            df["Product Code"].value_counts().plot(kind="bar", ax=ax3)
            ax3.set_title("Events by Product Code")
            ax3.set_ylabel("Count")
            st.pyplot(fig3)
    else:
        st.info("No charts to show.")
