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
                pma_number = entry.get("pma_pmn_number")
                hyperlink = ""

                # Create link for 510(k)
                if pma_number and pma_number.startswith("K"):
                    hyperlink = f"https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/pmn.cfm?ID={pma_number}"
                    pma_display = f"[{pma_number}]({hyperlink})"
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

            df = pd.DataFrame(records)

            st.subheader("📋 Results Table")
            st.markdown(
                df.to_markdown(index=False), 
                unsafe_allow_html=True
            )

            # Pareto Chart 1: Malfunction Events by Manufacturer
            st.subheader("📊 Pareto Chart: Malfunction Events by Manufacturer")
            malfunction_df = df[df["Event Type"] == "Malfunction"]
            if not malfunction_df.empty:
                malfunction_counts = malfunction_df["Manufacturer"].value_counts().sort_values(ascending=False)
                fig1, ax1 = plt.subplots()
                malfunction_counts.plot(kind="bar", ax=ax1)
                ax1.set_ylabel("Malfunction Count")
                ax1.set_title("Malfunction Events (Pareto)")
                st.pyplot(fig1)
            else:
                st.info("No malfunction events found in results.")

            # Pareto Chart 2: Injury Events by Manufacturer
            st.subheader("📊 Pareto Chart: Injury Events by Manufacturer")
            injury_df = df[df["Event Type"] == "Injury"]
            if not injury_df.empty:
                injury_counts = injury_df["Manufacturer"].value_counts().sort_values(ascending=False)
                fig2, ax2 = plt.subplots()
                injury_counts.plot(kind="bar", ax=ax2)
                ax2.set_ylabel("Injury Count")
                ax2.set_title("Injury Events (Pareto)")
                st.pyplot(fig2)
            else:
                st.info("No injury events found in results.")

            # CSV download
            st.download_button(
                "Download CSV", 
                df.to_csv(index=False), 
                file_name="maude_results.csv", 
                mime="text/csv"
            )

    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error: {e}")
    except Exception as e:
        st.error(f"❌ Error: {e}")
