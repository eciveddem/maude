import streamlit as st
import json
import pandas as pd

st.title("MAUDE Device Event Viewer")

uploaded_file = st.file_uploader("Upload MAUDE JSON file", type=["json"])

if uploaded_file:
    data = json.load(uploaded_file)
    results = data.get("results", [])

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
    st.dataframe(df)

    if st.button("Download as Excel"):
        df.to_excel("maude_output.xlsx", index=False)
        st.success("File saved as maude_output.xlsx")

else:
    st.info("Please upload a MAUDE device event JSON file.")
