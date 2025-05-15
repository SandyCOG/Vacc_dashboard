import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="Vaccination Dashboard", layout="wide")

@st.cache_data
def fetch_data():
    url = "https://app-api.enumeration.africa/api/FieldData/GetFieldData?ProjectId=312&TableId=843174"
    headers = {
        "accept": "application/json",
        "apiKey": "X3QtKDK35rEYjuW3BM0iBUNiYCffLKo4WQ8=",
        "content-type": "text/plain"
    }
    params = {
        "PageSize": 700,
        "PageNumber": 1
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    items = data['payload']['items']
    records = []

    for item in items:
        base = {
            'id': item['id'],
            'submittedByUserId': item['submittedByUserId'],
            'clientId': item['clientId'],
            'approvalStatus': item['approvalStatus'],
            'approvalRemark': item['approvalRemark'],
            'dateCreated': item['dateCreated'],
            'longitude': item['geometry']['coordinates'][0],
            'latitude': item['geometry']['coordinates'][1]
        }
        base.update(item['properties'])
        records.append(base)

    df = pd.DataFrame(records)
    return df

df = fetch_data()

st.title("📊 Vaccination Program Dashboard")

# Clean data
df['DATE_SUBMITTED'] = pd.to_datetime(df['DATE_SUBMITTED'], errors='coerce')
df['AGE_OF_CHILD'] = pd.to_numeric(df['AGE_OF_CHILD'], errors='coerce')

# Metric cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📅 Latest Submission", df['DATE_SUBMITTED'].max().strftime('%Y-%m-%d') if not df['DATE_SUBMITTED'].isna().all() else "N/A")

with col2:
    last_vaccine = df['VA_FIVE'].dropna().astype(str).iloc[-1] if not df['VA_FIVE'].isna().all() else "N/A"
    st.metric("💉 Last Vaccine (VA_FIVE)", last_vaccine)

with col3:
    state = df['STATE_NAME'].dropna().astype(str).iloc[-1] if not df['STATE_NAME'].isna().all() else "N/A"
    st.metric("📍 Location (State)", state)

with col4:
    st.metric("🗺️ No. of States Covered", df['STATE_NAME'].nunique())

# Children count
st.subheader("👶 Total Number of Children")
st.write(df['FIRSTNAME_CHILD'].dropna().nunique())

# ========== Gender Doughnut Chart ==========
st.subheader("⚥ Gender Distribution")
gender_counts = df['GENDER'].value_counts().reset_index()
gender_counts.columns = ['Gender', 'Count']
fig_gender = px.pie(gender_counts, values='Count', names='Gender', hole=0.4, title='Gender Distribution of Children')
st.plotly_chart(fig_gender, use_container_width=True)

# ========== Vaccination by Age Group ==========
st.subheader("📊 Vaccination Status by Age Group")
age_bins = [0, 1, 5, 10, 18]
age_labels = ['<1', '1-4', '5-9', '10-17']
df['Age Group'] = pd.cut(df['AGE_OF_CHILD'], bins=age_bins, labels=age_labels)

vacc_group = df.groupby(['Age Group', 'VACC_STAT']).size().reset_index(name='Count')
fig_vacc = px.bar(vacc_group, x='Age Group', y='Count', color='VACC_STAT', barmode='group',
                  title='Vaccination Status by Age Group')
st.plotly_chart(fig_vacc, use_container_width=True)

# ========== Geographic Coverage ==========
st.subheader("🗺️ Geographic Coverage")
geo_df = df[['latitude', 'longitude', 'STATE_NAME', 'LGA_NAME']].dropna()

fig_map = px.scatter_mapbox(
    geo_df,
    lat='latitude',
    lon='longitude',
    color='STATE_NAME',
    hover_name='LGA_NAME',
    zoom=5,
    height=500
)
fig_map.update_layout(mapbox_style='open-street-map')
st.plotly_chart(fig_map, use_container_width=True)
