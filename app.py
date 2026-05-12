import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from geopy.distance import geodesic
import gdown

# ---------------- LOAD ---------------- #

FILE_ID = st.secrets["FILE_ID"]

DOWNLOAD_URL = f"https://drive.google.com/uc?id={FILE_ID}"

LOCAL_FILE = "transformer_data.xlsx"

@st.cache_data
def load_data():

    # Download latest file
    gdown.download(
        DOWNLOAD_URL,
        LOCAL_FILE,
        quiet=True
    )

    # Read Excel
    df = pd.read_excel(LOCAL_FILE)

    text_cols = [
        'DT CODE',
        'DT NAME',
        'Feeder Name',
        'ZONE',
        'DIVISION',
        'CIRCLE'
    ]

    for col in text_cols:
        df[col] = df[col].astype(str).fillna("")

    return df

try:
    df = load_data()

except Exception as e:
    st.error(f"Error loading Google Drive file: {e}")
    st.stop()
# ---------------- CLEAN ---------------- #

df['Lattitude'] = pd.to_numeric(df['Lattitude'], errors='coerce')
df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
df['% LOADING (TIMESLOT-WISE)'] = pd.to_numeric(df['% LOADING (TIMESLOT-WISE)'], errors='coerce')

df = df.dropna(subset=['Lattitude', 'Longitude', '% LOADING (TIMESLOT-WISE)'])
df['LOAD_PCT'] = df['% LOADING (TIMESLOT-WISE)'] * 100

# ---------------- FAULT DETECTION ---------------- #

df['Voltage_R'] = pd.to_numeric(df['VOLTAGE AT DAY PEAK (R Phase)'], errors='coerce')
df['Voltage_Y'] = pd.to_numeric(df['VOLTAGE AT DAY PEAK (Y Phase)'], errors='coerce')
df['Voltage_B'] = pd.to_numeric(df['VOLTAGE AT DAY PEAK (B Phase)'], errors='coerce')

df['Current_R'] = pd.to_numeric(df['CURRENT AT DAY PEAK (R Phase)'], errors='coerce')
df['Current_Y'] = pd.to_numeric(df['CURRENT AT DAY PEAK (Y Phase)'], errors='coerce')
df['Current_B'] = pd.to_numeric(df['CURRENT AT DAY PEAK (B Phase)'], errors='coerce')

def faulty_phase(v, i):
    return ((v == 0) & (i != 0)) | ((v != 0) & (i == 0))

df['FAULTY'] = (
    faulty_phase(df['Voltage_R'], df['Current_R']) |
    faulty_phase(df['Voltage_Y'], df['Current_Y']) |
    faulty_phase(df['Voltage_B'], df['Current_B'])
)

# ---------------- STATUS ---------------- #

def get_status(load):

    if load < 25:
        return "NEGLIGIBLY LOADED"

    elif load < 50:
        return "UNDER LOADED"

    elif load < 80:
        return "OPTIMALLY LOADED"

    elif load < 100:
        return "OVERLOADED"

    elif load < 150:
        return "CRITICALLY LOADED"

    else:
        return "ABNORMALLY LOADED"

df['STATUS'] = df['LOAD_PCT'].apply(get_status)

# ---------------- COLORS ---------------- #

status_colors = {

    "NEGLIGIBLY LOADED": "#81C784",

    "UNDER LOADED": "#43A047",

    "OPTIMALLY LOADED": "#1E88E5",

    "OVERLOADED": "#FB8C00",

    "CRITICALLY LOADED": "#D32F2F",

    "ABNORMALLY LOADED": "#4A0000"
}

df['color'] = df['STATUS'].map(status_colors).fillna("#78909C")

# ---------------- UI ---------------- #

st.set_page_config(layout="wide")
st.title("Transformer Management System")

# ---------------- KPI ---------------- #


counts = df['STATUS'].value_counts()

cols = st.columns(7)

def kpi(col, label, value, color):

    col.markdown(
        f"""
<div style="
background:{color};
padding:18px;
border-radius:12px;
text-align:center;
color:white;
height:120px;
display:flex;
flex-direction:column;
justify-content:center;
align-items:center;
box-shadow:0px 2px 8px rgba(0,0,0,0.15);
">

<div style="
font-size:15px;
font-weight:600;
line-height:1.4;
margin-bottom:10px;
">
{label}
</div>

<div style="
font-size:30px;
font-weight:bold;
">
{value}
</div>

</div>
""",
        unsafe_allow_html=True
    )

# -------- KPI CARDS -------- #

kpi(
    cols[0],
    "Total Transformers",
    len(df),
    "#546E7A"
)

kpi(
    cols[1],
    "Negligibly Loaded<br>(0% to <25%)",
    counts.get("NEGLIGIBLY LOADED", 0),
    "#81C784"
)

kpi(
    cols[2],
    "Under Loaded<br>(25% to <50%)",
    counts.get("UNDER LOADED", 0),
    "#43A047"
)

kpi(
    cols[3],
    "Optimally Loaded<br>(50% to <80%)",
    counts.get("OPTIMALLY LOADED", 0),
    "#1E88E5"
)

kpi(
    cols[4],
    "Overloaded<br>(80% to <100%)",
    counts.get("OVERLOADED", 0),
    "#FB8C00"
)

kpi(
    cols[5],
    "Critically Loaded<br>(100% to <150%)",
    counts.get("CRITICALLY LOADED", 0),
    "#D32F2F"
)

kpi(
    cols[6],
    "Abnormally Loaded<br>(≥150%)",
    counts.get("ABNORMALLY LOADED", 0),
    "#4A0000"
)
# ---------------- REQUEST BUTTON ---------------- #

st.markdown(
    """
    <style>
    .request-button {
        display: inline-block;
        background-color: #1976D2;
        color: white !important;
        padding: 14px 28px;
        border-radius: 12px;
        text-decoration: none !important;
        font-size: 20px;
        font-weight: 600;
        text-align: center;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.18);
        margin-top: 20px;
        margin-bottom: 20px;
    }

    .request-button:hover {
        background-color: #1565C0;
        color: white !important;
        text-decoration: none !important;
    }
    </style>

    <a class="request-button"
       href="https://docs.google.com/forms/d/e/1FAIpQLSc_R9NvcMn6ojAotyXCDPMroEyc-BSFOrusiu7OFnFSU9SnSQ/viewform"
       target="_blank">
       Raise DT / MF Change Request
    </a>
    """,
    unsafe_allow_html=True)
# ---------------- FILTER ---------------- #

f1, f2, f3, f4 = st.columns(4)
st.info(
    "Select or enter an Overloaded or Critically Loaded transformer to generate optimal swap recommendations."
)

# -------- CIRCLE -------- #

circle = f1.multiselect(
    "Circle",
    sorted(df['CIRCLE'].dropna().unique())
)

# -------- DIVISION (depends on Circle) -------- #

if len(circle) == 0:
    division_options = sorted(df['DIVISION'].dropna().unique())
else:
    division_options = sorted(
        df[df['CIRCLE'].isin(circle)]['DIVISION'].dropna().unique()
    )

division = f2.multiselect(
    "Division",
    division_options
)

# -------- ZONE (depends on Circle + Division) -------- #

temp_df = df.copy()

if len(circle) > 0:
    temp_df = temp_df[temp_df['CIRCLE'].isin(circle)]

if len(division) > 0:
    temp_df = temp_df[temp_df['DIVISION'].isin(division)]

zone_options = sorted(temp_df['ZONE'].dropna().unique())

zone = f3.multiselect(
    "Zone",
    zone_options
)

# -------- STATUS -------- #

status_display_map = {

    "NEGLIGIBLY LOADED (0% to <25%)":
        "NEGLIGIBLY LOADED",

    "UNDER LOADED (25% to <50%)":
        "UNDER LOADED",

    "OPTIMALLY LOADED (50% to <80%)":
        "OPTIMALLY LOADED",

    "OVERLOADED (80% to <100%)":
        "OVERLOADED",

    "CRITICALLY LOADED (100% to <150%)":
        "CRITICALLY LOADED",

    "ABNORMALLY LOADED (≥150%)":
        "ABNORMALLY LOADED"
}

status_filter = f4.multiselect(
    "Status",
    list(status_display_map.keys())
)
# -------- FINAL FILTERING -------- #

df_filtered = df.copy()

if len(circle) > 0:
    df_filtered = df_filtered[df_filtered['CIRCLE'].isin(circle)]

if len(division) > 0:
    df_filtered = df_filtered[df_filtered['DIVISION'].isin(division)]

if len(zone) > 0:
    df_filtered = df_filtered[df_filtered['ZONE'].isin(zone)]

if len(status_filter) > 0:

    actual_status = [
        status_display_map[s]
        for s in status_filter
    ]

    df_filtered = df_filtered[
        df_filtered['STATUS'].isin(actual_status)
    ]

# ---------------- SEARCH ---------------- #

manual_code = st.text_input("Enter DT Code manually")

# normalize both sides
manual_code_clean = manual_code.strip().upper()

df['DT CODE CLEAN'] = df['DT CODE'].str.strip().str.upper()

df_filtered['DISPLAY'] = df_filtered['DT CODE'] + " | " + df_filtered['DT NAME']

selected_display = st.selectbox("Or select from list", ["ALL"] + df_filtered['DISPLAY'].tolist())

selected = None

# -------- FIXED MATCH -------- #
if manual_code_clean:
    match = df[df['DT CODE CLEAN'] == manual_code_clean]

    if not match.empty:
        selected = match.iloc[0]
    else:
        st.warning("No transformer found for entered DT Code")

elif selected_display != "ALL":
    selected = df_filtered[df_filtered['DISPLAY']==selected_display].iloc[0]

# ---------------- FUTURE ---------------- #

def years_safe(load):
    rate = 1.08
    y = 0
    while load < 100:
        load *= rate
        y += 1
        if y > 20:
            break
    return y

# ---------------- RECOMMENDER ---------------- #

rec_df = pd.DataFrame()

if selected is not None and selected['STATUS'] in ["OVERLOADED","CRITICALLY LOADED"]:

    under_df = df[
        (df['STATUS'].isin(["NEGLIGIBLY LOADED", "UNDER LOADED"])) &
        (~df['FAULTY'])
    ]

    # PRIORITY SEARCH ORDER
    for level in ["ZONE", "DIVISION", "CIRCLE"]:

        subset = under_df[
            under_df[level] == selected[level]
        ].copy()

        # SAME FEEDER PRIORITY
        subset["Feeder Priority"] = (
            subset["Feeder Name"] == selected["Feeder Name"]
        )

        temp = []

        for _, row in subset.iterrows():

            try:
                new_sel = (
                    row['LOAD_PCT'] *
                    row['DT CAPACITY (IN KVA)']
                ) / selected['DT CAPACITY (IN KVA)']

                new_can = (
                    selected['LOAD_PCT'] *
                    selected['DT CAPACITY (IN KVA)']
                ) / row['DT CAPACITY (IN KVA)']

            except:
                continue

            # BOTH MUST REMAIN HEALTHY
            if get_status(new_sel) not in ["UNDER LOADED","OPTIMALLY LOADED"]:
                continue

            if get_status(new_can) not in ["UNDER LOADED","OPTIMALLY LOADED"]:
                continue

            # MINIMUM SAFE YEARS
            yrs = min(
                years_safe(new_sel),
                years_safe(new_can)
            )

            if yrs < 5:
                continue

            # DISTANCE
            dist = geodesic(
                (
                    selected['Lattitude'],
                    selected['Longitude']
                ),
                (
                    row['Lattitude'],
                    row['Longitude']
                )
            ).km

            temp.append({

                "Same Feeder":
                    "YES" if row["Feeder Name"] == selected["Feeder Name"]
                    else "NO",

                "Feeder Priority":
                    1 if row["Feeder Name"] == selected["Feeder Name"]
                    else 0,

                "Circle": row['CIRCLE'],
                "Division": row['DIVISION'],
                "Zone": row['ZONE'],

                "Proposed DT Code": row['DT CODE'],
                "Proposed DT Name": row['DT NAME'],
                "Feeder": row['Feeder Name'],

                "Proposed Capacity (kVA)":
                    f"{row['DT CAPACITY (IN KVA)']} kVA",

                "Problem DT Load (Before Swap)":
                    f"{round(selected['LOAD_PCT'],1)} %",

                "Problem DT Load (After Swap)":
                    f"{round(new_sel,1)} %",

                "Problem DT Status (After Swap)":
                    get_status(new_sel),

                "Proposed DT Load (Before Swap)":
                    f"{round(row['LOAD_PCT'],1)} %",

                "Proposed DT Load (After Swap)":
                    f"{round(new_can,1)} %",

                "Proposed DT Status (After Swap)":
                    get_status(new_can),

                "Years Safe (Post Swap)":
                    f"{yrs} years",

                "Distance (km)": dist,

                "Lat": row['Lattitude'],
                "Long": row['Longitude']
            })

        if temp:

            rec_df = (
                pd.DataFrame(temp)
                .sort_values(
                    by=[
                        "Feeder Priority",
                        "Years Safe (Post Swap)",
                        "Distance (km)"
                    ],
                    ascending=[False, False, True]
                )
                .head(5)
                .reset_index(drop=True)
            )

            rec_df["Distance (km)"] = (
                rec_df["Distance (km)"]
                .round(2)
                .astype(str) + " km"
            )

            break# ---------------- MAP ---------------- #

fig = go.Figure()

# -------- SHOW ALL ONLY WHEN NOTHING IS SELECTED -------- #

if selected is None:

    fig.add_trace(go.Scattermap(
        lat=df_filtered['Lattitude'],
        lon=df_filtered['Longitude'],
        mode='markers',
        name="All Transformers",
        marker=dict(
            size=8,
            opacity=0.4,
            color=df_filtered['color']
        ),

        text=df_filtered['DT NAME'],

        customdata=df_filtered[[
    'DT CODE',
    'METER NO.',
    'DT CAPACITY (IN KVA)',
    'STATUS',
    'LOAD_PCT',
    'CIRCLE',
    'DIVISION',
    'ZONE'
]],

hovertemplate=
"<b>%{text}</b><br>" +
"DT Code: %{customdata[0]}<br>" +
"Meter No: %{customdata[1]}<br>" +
"Capacity: %{customdata[2]} kVA<br>" +
"Status: %{customdata[3]}<br>" +
"Load: %{customdata[4]:.1f}%<br>" +
"Circle: %{customdata[5]}<br>" +
"Division: %{customdata[6]}<br>" +
"Zone: %{customdata[7]}<extra></extra>"
    ))

# -------- RECOMMENDED -------- #

if not rec_df.empty:

    fig.add_trace(go.Scattermap(
        lat=rec_df['Lat'],
        lon=rec_df['Long'],
        mode='markers',
        name="Recommended",

        marker=dict(
            size=14,
            color="#FFD54F"
        ),

        text=rec_df['Proposed DT Name'],

        customdata=rec_df[[
            'Proposed DT Code',
            'Proposed Capacity (kVA)',
            'Circle',
            'Division',
            'Zone',
            'Years Safe (Post Swap)',
            'Distance (km)'
        ]],

        hovertemplate=
        "<b>%{text}</b><br>" +
        "DT Code: %{customdata[0]}<br>" +
        "Capacity: %{customdata[1]}<br>" +
        "Circle: %{customdata[2]}<br>" +
        "Division: %{customdata[3]}<br>" +
        "Zone: %{customdata[4]}<br>" +
        "Years Safe: %{customdata[5]}<br>" +
        "Distance: %{customdata[6]}<extra></extra>"
    ))
# -------- SELECTED -------- #

if selected is not None:

    fig.add_trace(go.Scattermap(
        lat=[selected['Lattitude']],
        lon=[selected['Longitude']],
        mode='markers',
        name="Selected",

        marker=dict(
            size=18,
            color="black"
        ),

        text=[selected['DT NAME']],

        customdata=[[
            selected['DT CODE'],
            selected['METER NO.'],
            selected['DT CAPACITY (IN KVA)'],
            selected['LOAD_PCT'],
            selected['STATUS'],
            selected['CIRCLE'],
            selected['DIVISION'],
            selected['ZONE']
        ]],

        hovertemplate=
        "<b>%{text}</b><br>" +
        "DT Code: %{customdata[0]}<br>" +
        "Meter No: %{customdata[1]}<br>" +
        "Capacity: %{customdata[2]} kVA<br>" +
        "Load: %{customdata[3]:.1f}%<br>" +
        "Status: %{customdata[4]}<br>" +
        "Circle: %{customdata[5]}<br>" +
        "Division: %{customdata[6]}<br>" +
        "Zone: %{customdata[7]}<extra></extra>"
    ))
# -------- MAP CENTER -------- #

if selected is not None:

    center_lat = selected['Lattitude']
    center_lon = selected['Longitude']
    zoom_level = 13

else:

    center_lat = df_filtered['Lattitude'].mean()
    center_lon = df_filtered['Longitude'].mean()
    zoom_level = 5

fig.update_layout(
    map=dict(
        style="carto-positron",

        center=dict(
            lat=center_lat,
            lon=center_lon
        ),

        zoom=zoom_level
    ),

    height=800,

    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0
    )
)

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "scrollZoom": True
    }
)
# ---------------- DETAILS ---------------- #

if selected is not None:
    st.subheader("Selected Transformer Details")

    st.dataframe(pd.DataFrame({
        "Attribute":[
            "DT Code","DT Name","Feeder","Zone","Division","Circle",
            "Capacity (kVA)","Load (%)","Status"
        ],
        "Value":[
            selected['DT CODE'],
            selected['DT NAME'],
            selected['Feeder Name'],
            selected['ZONE'],
            selected['DIVISION'],
            selected['CIRCLE'],
            selected['DT CAPACITY (IN KVA)'],
            round(selected['LOAD_PCT'],2),
            selected['STATUS']
        ]
    }), use_container_width=True)

# ---------------- PIVOT OUTPUT ---------------- #

if not rec_df.empty:
    st.subheader("Recommended Transformer Swaps")

    pivot_data = {}

    for i, row in rec_df.iterrows():
        pivot_data[f"Best {len(pivot_data)+1}"] = [
            row["Circle"],
            row["Division"],
            row["Zone"],
            row["Proposed DT Code"],
            row["Proposed DT Name"],
            row["Feeder"],
            row["Proposed Capacity (kVA)"],

            row["Problem DT Load (Before Swap)"],
            row["Problem DT Load (After Swap)"],
            row["Problem DT Status (After Swap)"],

            row["Proposed DT Load (Before Swap)"],
            row["Proposed DT Load (After Swap)"],
            row["Proposed DT Status (After Swap)"],

            row["Years Safe (Post Swap)"],
            row["Distance (km)"]
        ]

    pivot_df = pd.DataFrame(
        pivot_data,
        index=[
            "Circle",
            "Division",
            "Zone",
            "DT Code",
            "DT Name",
            "Feeder",
            "Capacity",
            "Problem DT Load (Before)",
            "Problem DT Load (After)",
            "Problem DT Status (After)",
            "Proposed DT Load (Before)",
            "Proposed DT Load (After)",
            "Proposed DT Status (After)",
            "Years Safe",
            "Distance"
        ]
    )

    pivot_df = pivot_df.reset_index()
    pivot_df.columns = ["Metric"] + list(pivot_df.columns[1:])

    row_height = 38
    total_rows = len(pivot_df) + 1

    st.dataframe(
    pivot_df.style.set_properties(**{
        'white-space': 'normal',
        'max-width': '120px'
    }),
    use_container_width=True,
    height=600,
    hide_index=True
)

# ---------------- ABNORMAL TABLE ---------------- #

abnormal_df = df[df['STATUS']=="ABNORMALLY LOADED"]

if not abnormal_df.empty:
    st.subheader("Abnormally Loaded Transformers")

    display_df = abnormal_df[[
        'DT CODE','DT NAME','Feeder Name','ZONE','DIVISION','CIRCLE',
        'DT CAPACITY (IN KVA)','LOAD_PCT','STATUS'
    ]].rename(columns={
        'LOAD_PCT': 'Load %'
    })

    st.dataframe(
        display_df,
        use_container_width=True
    )

# ---------------- FAULTY TRANSFORMERS ---------------- #

faulty_df = df[df['FAULTY']]

if not faulty_df.empty:
    st.subheader("Suspected DT Meter wiring issues")

    st.dataframe(
        faulty_df[[
            'DT CODE','DT NAME','Feeder Name',
            'Voltage_R','Current_R','Voltage_Y','Current_Y','Voltage_B','Current_B'
        ]],
        use_container_width=True
    )
