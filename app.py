import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date

st.set_page_config(page_title="MAUDE Search", layout="wide")
st.title("🔍 MAUDE Adverse Event Search")

# Search inputs
search_option = st.selectbox("Search by", [
    "Device Generic Name", 
    "Product Code", 
    "UDI-DI"
])

search_term = st.text_input("Enter your search term (e.g. 'defibrillator', 'LWS', or '00643169356566')")

# Date range picker
start_date, end_date = st.date_input(
    "Date received range (YYYY-MM-DD)",
    value=(date(2020, 1, 1), date.today())
)

limit = st.slider("Number of records to fetch", 1, 100, 25)

if st.button("Search"):
    base_url = "https://api.fda.gov/device/event.json"

    if search_option == "Device Generic Name":
        query = f"device.generic_name:{search_term}"
    elif search_option == "Product Code":
        query = f"device.device_report_product_code:{search_term}"
    elif search_option == "UDI-DI":
        query = f"device.udi_di:{search_term}"
    else:
        query = ""

    # Format dates
    start_str = start_date.strftime("%Y%m%d")
    end_str = end_date.strftime("%Y%m%d")

    # Add date range and sort
    query += f"+AND+date_received:[{start_str}+TO+{end_str}]"
    url = f"{base_url}?search={query}&sort=date_received:desc&limit={limit}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            st.warning("No results found.")
        else:
            records = []
            for entry in results:
                device = entry.get("device", [{}])[0]
                openfda = device.get("openfda", {})

                records.append({
                    "Manufacturer": device.get("manufacturer_d_name"),
                    "Brand Name": device.get("brand_name"),
                    "Generic Name": device.get("generic_name"),
                    "Product Code": device.get("device_report_product_code"),
                    "UDI DI": device.get("udi_di"),
                    "Device Name (FDA)": openfda.get("device_name"),
                    "Device Class": openfda.get("device_class"),
                    "Event Type": entry.get("event_type"),
                    "Event Date": entry.get("date_of_event"),
                    "Received Date": entry.get("date_received"),
                    "FEI Number": "; ".join(openfda.get("fei_number", [])),
                })

            df = pd.DataFrame(records)
            st.subheader("📋 Results Table")
            st.dataframe(df)

            # Pareto Chart: Event Type Count
            st.subheader("📊 Event Type Pareto Chart")
            if "Event Type" in df.columns:
                event_counts = df["Event Type"].value_counts().sort_values(ascending=False)
                fig, ax = plt.subplots()
                event_counts.plot(kind="bar", ax=ax)
                ax.set_ylabel("Count")
                ax.set_title("Event Type Frequency (Pareto)")
                st.pyplot(fig)

            # CSV download
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, file_name="maude_results.csv", mime="text/csv")

    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error: {e}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
