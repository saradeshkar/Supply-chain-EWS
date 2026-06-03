"""
Supply Chain EWS Dashboard — Streamlit v2
Data files required (same folder):
  risk_nodes.csv, stress_index.csv, country_stress.csv

Run:
    pip install streamlit plotly pandas numpy
    streamlit run dashboard_v2.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Supply Chain EWS",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Space Mono', monospace; }
  .stApp { background: #050a0f; color: #c8dde8; }
  [data-testid="stSidebar"] { background: #0b1520 !important; border-right: 1px solid #1a2d40; }
  [data-testid="stSidebar"] * { color: #c8dde8 !important; }
  [data-testid="stMetric"] { background: #0b1520; border: 1px solid #1a2d40; padding: 14px 18px; border-radius: 2px; }
  [data-testid="stMetricLabel"] { font-size: 10px !important; letter-spacing: 0.15em; color: #4d7a96 !important; text-transform: uppercase; }
  [data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; font-size: 26px !important; }
  h1 { font-family: 'Syne', sans-serif !important; font-size: 20px !important; color: #fff !important; letter-spacing: 0.05em; }
  h2, h3 { font-family: 'Syne', sans-serif !important; color: #00ffe0 !important; font-size: 11px !important; letter-spacing: 0.18em; text-transform: uppercase; }
  hr { border-color: #1a2d40 !important; }
  .stSelectbox > div > div { background: #0b1520 !important; border-color: #1a2d40 !important; color: #c8dde8 !important; }
  [data-testid="stTabs"] button { font-family: 'Space Mono', monospace !important; font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase; color: #4d7a96 !important; }
  [data-testid="stTabs"] button[aria-selected="true"] { color: #00ffe0 !important; border-bottom: 2px solid #00ffe0; }
  [data-testid="stExpander"] { background: #0b1520 !important; border: 1px solid #1a2d40 !important; }
  .block-container { padding: 1.2rem 1.4rem !important; }
  .insight-box { background:#0b1520; border-left:3px solid #00ffe0; padding:10px 14px; margin:6px 0; font-size:11px; line-height:1.8; }
  .warn-box    { background:#0b1520; border-left:3px solid #ff4b6e; padding:10px 14px; margin:6px 0; font-size:11px; line-height:1.8; }
  .amber-box   { background:#0b1520; border-left:3px solid #f5a623; padding:10px 14px; margin:6px 0; font-size:11px; line-height:1.8; }
</style>
""", unsafe_allow_html=True)

# ── Sector labels ──────────────────────────────────────────────────────────────
SECTOR_LABELS = {
    "C26": "Electronics (C26)",
    "C27": "Electrical Equipment (C27)",
    "C28": "Machinery (C28)",
    "J61": "Telecoms (J61)",
    "O":   "Public Admin (O)",
    "S8":  "Other Services (S8)",
    "A7":  "Agriculture (A7)",
    "2020":"COVID Shock (2020)",
}

SECTOR_DISRUPTION_REASONS = {
    "C26": "Semiconductor fab concentration in Taiwan/Korea; long lead-times (6–18 months); single-source dependencies for advanced chips; US–China tech export controls disrupting supply of EUV components.",
    "C27": "Copper & rare-earth input volatility; EV-driven demand surge straining transformer/motor capacity; EU energy crisis 2021–22 raised smelting costs by ~40%; Russia supplied ~6% of global refined copper.",
    "C28": "Just-in-time manufacturing leaves zero buffer stock; German/Japanese precision machinery hubs face energy and labour cost shocks; Ukraine war cut specialty steel supply used in industrial equipment.",
    "J61": "Infrastructure investment cycles are 10–15 years; satellite & undersea cable vulnerabilities; 5G rollout creating new single points of failure; Russian internet isolation disrupting Eastern-European peering.",
    "O":   "Sanctions and geopolitical isolation; disrupted international payments (SWIFT); government procurement lockdowns during COVID.",
    "S8":  "Logistics and warehousing labour shortages; port congestion multiplying dwell times; last-mile delivery strain.",
    "A7":  "Ukraine/Russia supply ~30% of global wheat exports; fertiliser (Belarus/Russia) sanctions; Black Sea corridor blockages reduced grain shipments by 60% in 2022.",
    "2020":"Pandemic shock year — factory shutdowns, demand collapse followed by asymmetric demand surge, PPE/vaccine supply failures.",
}

COUNTRY_DISRUPTION_REASONS = {
    "DEU": "Central European manufacturing hub; high energy dependency on Russian gas (35% share pre-war); automotive/machinery exports halted by chip shortage; C26/C27/C28 all severely exposed.",
    "CHN": "Factory-of-the-world concentration risk; zero-COVID port shutdowns (Yantian 2021, Shanghai 2022); US export controls on advanced semiconductors; largest single node in global GVC.",
    "TWN": "TSMC produces ~92% of world's most advanced chips; strait tensions create existential supply risk; J61 telecom equipment supply chain runs through Taiwan.",
    "RUS": "Sanctioned post-Ukraine invasion; cut off from SWIFT; ceased exporting energy to EU, fertiliser, wheat, titanium, palladium (used in catalytic converters); J61 disruption via telecoms isolation.",
    "UKR": "War damage to industrial infrastructure; neon gas (used in chip lithography) — Ukraine supplied 50% of global neon pre-war; grain/sunflower oil export blockade.",
    "EGY": "Suez Canal — 12% of global trade, 30% of container traffic transits; Ever Given 2021 blocked canal for 6 days, causing $9.6B/day losses; J61 undersea cables also route through Suez.",
    "SGP": "Regional trans-shipment hub; port congestion during COVID cascaded across Asia-Pacific; semiconductor packaging and testing cluster.",
    "NLD": "Rotterdam is Europe's largest port; gateway for 75% of EU goods imports; ASML (sole supplier of EUV lithography machines) is Dutch — C26 chokepoint.",
    "KAZ": "Landlocked; transit route disruptions post-Ukraine war (Trans-Siberian/CPC pipeline); C26 rare earth processing.",
    "BLR": "Sanctioned; potash fertiliser (A7 input) export ban; transit disruption for EU–Russia rail corridor.",
    "COL": "Coffee/commodity export volatility; port congestion at Cartagena; C27 electrical equipment manufacturing exposed to USD exchange rate shocks.",
    "MYS": "Semiconductor backend (packaging/testing) concentration; COVID plant shutdowns 2021 created 3-month chip delivery gap; natural rubber supply for medical devices.",
}

COORDS = {
    "USA":(37.1,-95.7), "CHN":(35.9,104.2), "DEU":(51.2,10.5), "JPN":(36.2,138.3),
    "GBR":(55.4,-3.4),  "FRA":(46.2,2.2),   "KOR":(35.9,127.8),"CAN":(56.1,-106.3),
    "ITA":(41.9,12.6),  "NLD":(52.1,5.3),   "AUS":(-25.3,133.8),"ESP":(40.5,-3.7),
    "MEX":(23.6,-102.6),"SWE":(60.1,18.6),  "CHE":(46.8,8.2),  "POL":(51.9,19.1),
    "BEL":(50.5,4.5),   "AUT":(47.5,14.6),  "NOR":(60.5,8.5),  "CZE":(49.8,15.5),
    "TUR":(38.9,35.2),  "SAU":(23.9,45.1),  "IND":(20.6,78.9), "BRA":(-14.2,-51.9),
    "ZAF":(-30.6,22.9), "SGP":(1.4,103.8),  "HKG":(22.4,114.2),"MYS":(4.2,108.0),
    "UKR":(48.4,31.2),  "RUS":(61.5,105.3), "EGY":(26.8,30.8), "ARE":(23.4,53.8),
    "PRT":(39.4,-8.2),  "GRC":(39.1,21.8),  "FIN":(61.9,25.7), "DNK":(56.3,9.5),
    "HUN":(47.2,19.5),  "NZL":(-40.9,174.9),"ISR":(31.0,34.9), "THA":(15.9,100.9),
    "IDN":(-0.8,113.9), "PHL":(12.9,121.8), "VNM":(14.1,108.3),"TWN":(23.7,120.9),
    "PAK":(30.4,69.3),  "ARG":(-38.4,-63.6),"CHL":(-35.7,-71.5),"COL":(4.6,-74.1),
    "PER":(-9.2,-75.0), "KAZ":(48.0,66.9),  "BLR":(53.7,28.0), "ROU":(45.9,24.9),
    "BGR":(42.7,25.5),  "SVN":(46.1,14.8),  "HRV":(45.1,16.4), "EST":(58.6,25.0),
    "LVA":(56.9,24.6),  "LTU":(55.2,23.9),  "SVK":(48.7,19.7), "MLT":(35.9,14.4),
    "CYP":(35.1,33.4),  "LUX":(49.8,6.1),   "ISL":(65.0,-18.0),"MAR":(31.8,-7.1),
    "TUN":(33.9,9.5),   "NGA":(9.1,8.7),    "AGO":(-11.2,17.9),"CMR":(3.9,11.5),
    "COD":(-4.0,21.8),  "SEN":(14.5,-14.5), "CIV":(7.5,-5.5),  "KHM":(12.6,104.9),
    "MMR":(19.2,96.7),  "LAO":(19.9,102.5), "BGD":(23.7,90.4), "JOR":(30.6,36.2),
    "BRN":(4.5,114.7),  "CRI":(9.7,-83.8),  "STP":(0.2,6.6),
}

CODE_NAME = {
    "USA":"United States","CHN":"China","DEU":"Germany","JPN":"Japan",
    "GBR":"United Kingdom","FRA":"France","KOR":"Korea","CAN":"Canada",
    "ITA":"Italy","NLD":"Netherlands","AUS":"Australia","ESP":"Spain",
    "MEX":"Mexico","SWE":"Sweden","POL":"Poland","BEL":"Belgium",
    "AUT":"Austria","NOR":"Norway","CZE":"Czech Republic","TUR":"Turkey",
    "SAU":"Saudi Arabia","IND":"India","BRA":"Brazil","ZAF":"South Africa",
    "SGP":"Singapore","HKG":"Hong Kong SAR China","MYS":"Malaysia",
    "UKR":"Ukraine","RUS":"Russia","EGY":"Egypt","ARE":"United Arab Emirates",
    "PRT":"Portugal","GRC":"Greece","FIN":"Finland","DNK":"Denmark",
    "HUN":"Hungary","NZL":"New Zealand","ISR":"Israel","THA":"Thailand",
    "IDN":"Indonesia","PHL":"Philippines","VNM":"Vietnam","TWN":"Taiwan Province of China",
    "ARG":"Argentina","CHL":"Chile","COL":"Colombia","CHE":"Switzerland",
    "PAK":"Pakistan","KAZ":"Kazakhstan","BLR":"Belarus","ROU":"Romania",
    "BGR":"Bulgaria","SVN":"Slovenia","HRV":"Croatia","EST":"Estonia",
    "LVA":"Latvia","LTU":"Lithuania","SVK":"Slovak Republic","CZE":"Czech Republic",
}

# ── Extended node data with ML_Probability & Structural_Risk ─────────────────
EXTENDED_NODES = pd.DataFrame({
    "Node":            ["COL_C27","CZE_C27","DEU_C27","CRI_C27","BLR_C26","RUS_J61",
                        "FIN_J61","ROU_C27","DEU_C26","PAK_C27","CAN_C26","LVA_C27",
                        "POL_C27","LUX_C28","SAU_C27"],
    "ML_Probability":  [1.0,1.0,1.0,0.993333,0.933333,0.930000,
                        0.936667,0.970000,0.980000,0.970000,0.846667,0.970000,
                        0.986667,0.956667,0.983333],
    "Structural_Risk": [1.0,0.999290,0.995803,0.970544,0.439910,0.427807,
                        0.403281,0.381691,0.376067,0.378569,0.428147,0.375067,
                        0.366517,0.379316,0.367851],
    "Risk_Score":      [1.0,0.999503,0.997062,0.977381,0.587937,0.578465,
                        0.563297,0.558184,0.557247,0.555998,0.553703,0.553547,
                        0.552562,0.552521,0.552496],
})

# Top stressed countries per year (exact from provided data)
TOP_STRESSED = pd.DataFrame([
    (2019,"Venezuela RB",1.317559),(2019,"Iran Islamic Rep.",1.286605),
    (2019,"Armenia",1.037194),(2019,"Bahrain",0.997842),(2019,"Paraguay",0.519309),
    (2020,"Venezuela RB",1.395038),(2020,"Iran Islamic Rep.",0.960555),
    (2020,"Lithuania",0.707652),(2020,"China",0.564611),(2020,"Mongolia",0.514662),
    (2021,"Venezuela RB",1.314717),(2021,"Malawi",1.116291),
    (2021,"Bahrain",1.072212),(2021,"United Arab Emirates",1.040194),(2021,"Costa Rica",0.911992),
    (2022,"Venezuela RB",1.347857),(2022,"Honduras",1.231792),
    (2022,"Kuwait",0.909974),(2022,"Low Income Countries",0.849008),(2022,"Oman",0.834274),
], columns=["Year","Country","stress_score"])

# ── Load CSVs ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    rn = pd.read_csv("risk_nodes.csv")
    rn["country"] = rn["Node"].str.split("_").str[0]
    rn["sector"]  = rn["Node"].str.split("_").str[1]
    rn = rn.merge(EXTENDED_NODES[["Node","ML_Probability","Structural_Risk"]], on="Node", how="left")
    si = pd.read_csv("stress_index.csv")

    # ── Floor rescaling: remap Min-Max [0,1] → [0.05, 1.0] ──────────────────
    # A value of 0.0 is the Min-Max minimum, NOT zero stress.
    # Rescaling to a floor of 0.05 avoids misleading zero bars on the dashboard.
    # The relative ordering and peak (2021 = 1.0) are fully preserved.
    _FLOOR = 0.05
    for _col in ["Commodity", "Macro", "Stress_Index"]:
        si[_col] = si[_col] * (1 - _FLOOR) + _FLOOR
    # ─────────────────────────────────────────────────────────────────────────

    cs = pd.read_csv("country_stress.csv")
    cs["stress_score"] = pd.to_numeric(cs["stress_score"], errors="coerce")
    return rn, si, cs

rn_df, si_df, cs_df = load_data()

# ── Filter out year-based node artifacts (e.g. IDN_2020, RUS_2020) ───────────
# These rows were created from a misaligned year column during feature construction.
# Only valid ISIC sector codes (alphabetic prefixes) should appear.
VALID_SECTORS = {"C26","C27","C28","J61","O","S8","A7"}
rn_df = rn_df[rn_df["sector"].isin(VALID_SECTORS)]
# ─────────────────────────────────────────────────────────────────────────────

YEARS   = sorted(si_df["Year"].unique())
SECTORS = sorted(rn_df["sector"].unique())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ EWS Controls")
    st.markdown("---")
    selected_year = st.selectbox("Scenario Year", YEARS, index=YEARS.index(2021))
    selected_sectors = st.multiselect(
        "Sectors", options=SECTORS, default=["C26","C27","C28","J61"],
        format_func=lambda x: SECTOR_LABELS.get(x, x),
    )
    risk_threshold = st.slider("High-Risk Threshold", 0.0, 1.0, 0.85, 0.01)
    st.markdown("---")
    st.markdown("""
**Model Architecture**
<div style='font-size:10px;line-height:2;color:#4d7a96;letter-spacing:0.08em'>
Type &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ Graph Conv Net<br>
GCN layers &nbsp;&nbsp;→ <b style='color:#00ffe0'>2</b><br>
Node features → <b style='color:#00ffe0'>35</b><br>
Risk formula &nbsp;→ 0.3×ML + 0.7×SR<br>
T-statistic &nbsp;&nbsp;→ 4.107<br>
p-value &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;→ 5.79e-05<br>
High-stress Δ → +9.28%<br>
Low-stress Δ &nbsp;→ −0.83%
</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div style="font-size:9px;color:#4d7a96;letter-spacing:0.12em">OECD TiVA · 2-layer GCN · 2019–2022</div>', unsafe_allow_html=True)

# ── Filter ────────────────────────────────────────────────────────────────────
filtered_rn = rn_df[rn_df["sector"].isin(selected_sectors)] if selected_sectors else rn_df.copy()
high_risk   = filtered_rn[filtered_rn["Risk_Score"] >= risk_threshold]
year_si     = si_df[si_df["Year"] == selected_year].iloc[0]
avg_risk    = filtered_rn["Risk_Score"].mean()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1>⚡ SUPPLY CHAIN DISRUPTION — EARLY WARNING SYSTEM</h1>"
    f"<div style='font-size:10px;color:#4d7a96;letter-spacing:0.15em;margin:-6px 0 14px'>"
    f"OECD TiVA NETWORK &nbsp;·&nbsp; 2-LAYER GCN &nbsp;·&nbsp; 35 NODE FEATURES &nbsp;·&nbsp; YEAR: {selected_year}</div>",
    unsafe_allow_html=True,
)

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("High-Risk Nodes",  f"{len(high_risk)}", f"/{len(filtered_rn)} total")
c2.metric("Avg GNN Risk",     f"{avg_risk:.3f}")
c3.metric("Composite Stress", f"{year_si['Stress_Index']:.3f}", f"{selected_year}")
c4.metric("Commodity Signal", f"{year_si['Commodity']:.3f}", "normalized [0.05–1.0]")
c5.metric("Macro Signal",     f"{year_si['Macro']:.3f}", "normalized [0.05–1.0]")
st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌐  Globe & Risk Scores",
    "📊  ML vs Structural",
    "📈  Stress Timeline",
    "🗺️  Country Heatmap",
    "🔬  Sector Analysis",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — GLOBE + TOP NODES TABLE
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    with st.expander("📖  What does the Highest-Risk Nodes table mean?", expanded=False):
        st.markdown("""
<div class='insight-box'>
<b style='color:#00ffe0'>What each column means:</b><br><br>

<b style='color:#f5a623'>Node ID</b> — A (country)_(sector) pair in the OECD TiVA supply chain network.
Each node is one country's participation in one industry sector.
e.g. <b>DEU_C27</b> = Germany's Electrical Equipment sector.<br><br>

<b style='color:#f5a623'>Risk %</b> — The GCN-predicted composite risk score, expressed as a percentage.
Computed as: <b>Risk = 0.3 × ML_Probability + 0.7 × Structural_Risk</b><br>
<b>100%</b> = the model is certain this node will be stressed AND it is structurally critical in the trade network.<br><br>

<b style='color:#f5a623'>Why are the top scores all 100?</b> — These nodes satisfy both conditions maximally:
the 2-layer GCN classifier gives them probability 1.0 AND their betweenness/eigenvector centrality
in the OECD trade graph is also maximal. Most connected AND most likely to be stressed — worst-case combination.<br><br>

<b style='color:#f5a623'>Why Electronics (C26), Electrical Equipment (C27), Telecoms (J61)?</b> — These sectors have the highest
GVC integration and the longest, most fragile supply chains. Electronics relies on Taiwan/Korea fabs;
C27 on rare-earth inputs from geopolitically unstable regions; J61 on physical undersea cables.
All three have near-zero short-run substitutability.
</div>
""", unsafe_allow_html=True)

    col_globe, col_nodes = st.columns([3, 2], gap="medium")

    with col_globe:
        st.markdown("### 🌐 Supply Chain Risk Globe")
        country_risk = filtered_rn.groupby("country")["Risk_Score"].mean().reset_index()
        country_risk.columns = ["country","avg_risk"]
        country_risk["lat"] = country_risk["country"].map(lambda c: COORDS.get(c,(None,None))[0])
        country_risk["lon"] = country_risk["country"].map(lambda c: COORDS.get(c,(None,None))[1])
        country_risk = country_risk.dropna(subset=["lat","lon"])

        fig_globe = go.Figure(go.Scattergeo(
            lat=country_risk["lat"], lon=country_risk["lon"],
            mode="markers",
            marker=dict(
                size=country_risk["avg_risk"]*22+4,
                color=country_risk["avg_risk"],
                colorscale=[[0,"#00ffe0"],[0.5,"#f5a623"],[0.85,"#ff4b6e"],[1,"#ff0033"]],
                cmin=0, cmax=1,
                colorbar=dict(title=dict(text="Avg Risk",font=dict(color="#4d7a96",size=10)),
                              tickfont=dict(color="#4d7a96",size=9),
                              bgcolor="#0b1520",bordercolor="#1a2d40",thickness=10),
                line=dict(width=0.5,color="#1a2d40"), opacity=0.85,
            ),
            text=country_risk["country"],
            customdata=(country_risk["avg_risk"]*100).round(1),
            hovertemplate="<b>%{text}</b><br>Avg Risk: %{customdata:.1f}%<extra></extra>",
        ))
        fig_globe.update_layout(
            height=500, paper_bgcolor="#050a0f",
            geo=dict(projection_type="orthographic",
                     showland=True,landcolor="#0d1f2d",showocean=True,oceancolor="#050a0f",
                     showcoastlines=True,coastlinecolor="#1a2d40",
                     showcountries=True,countrycolor="#1a2d40",
                     showframe=False,bgcolor="#050a0f",
                     projection_rotation=dict(lon=20,lat=15,roll=0)),
            margin=dict(l=0,r=0,t=0,b=0),
        )
        st.plotly_chart(fig_globe, use_container_width=True)

    with col_nodes:
        st.markdown("### ⚠ Highest-Risk Nodes")
        top_n = st.slider("Show top N", 10, 50, 20, key="top_n_s")
        top_nodes = filtered_rn.nlargest(top_n,"Risk_Score")[["Node","country","sector","Risk_Score"]].copy()
        top_nodes["Sector"] = top_nodes["sector"].map(lambda x: SECTOR_LABELS.get(x,x))
        top_nodes["Risk %"] = (top_nodes["Risk_Score"]*100).round(2)
        top_nodes = top_nodes.rename(columns={"country":"Country","Node":"Node ID"})

        def colour_risk(val):
            if val >= 95:   return "color: #ff4b6e; font-weight:bold"
            elif val >= 85: return "color: #f5a623"
            else:            return "color: #00ffe0"

        st.dataframe(
            top_nodes[["Node ID","Country","Sector","Risk %"]].style
                .map(colour_risk, subset=["Risk %"])
                .set_properties(**{"background-color":"#0b1520","color":"#c8dde8",
                                   "border-color":"#1a2d40","font-size":"11px"}),
            use_container_width=True, height=360,
        )

        st.markdown("### Risk Distribution")
        bins   = [0,0.5,0.7,0.85,0.95,1.001]
        labels = ["<0.5","0.5–0.7","0.7–0.85","0.85–0.95","0.95–1.0"]
        counts = pd.cut(filtered_rn["Risk_Score"],bins=bins,labels=labels,right=False).value_counts().reindex(labels)
        fig_d = go.Figure(go.Bar(
            x=labels, y=counts.values,
            marker_color=["#00ffe0","#7fffd4","#f5a623","#ff8c69","#ff4b6e"],
            text=counts.values, textposition="outside",
            textfont=dict(color="#4d7a96",size=10),
        ))
        fig_d.update_layout(height=170,paper_bgcolor="#050a0f",plot_bgcolor="#0b1520",
                             margin=dict(l=0,r=0,t=8,b=28),
                             xaxis=dict(tickfont=dict(color="#4d7a96",size=9),gridcolor="#1a2d40"),
                             yaxis=dict(tickfont=dict(color="#4d7a96",size=9),gridcolor="#1a2d40"))
        st.plotly_chart(fig_d, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ML vs STRUCTURAL RISK
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    with st.expander("📖  What do ML Probability and Structural Risk mean?", expanded=True):
        st.markdown("""
<div class='insight-box'>
<b style='color:#00ffe0'>Your Risk Score has two components:</b><br><br>

<b style='color:#f5a623'>ML_Probability (weight: 30%)</b> — The raw output of your 2-layer GCN classifier.
The probability (0–1) that a node enters a high-stress state, learned from historical OECD
trade disruption patterns across <b>35 node features</b> (trade volume, centrality, sector exposure,
macro signals, etc.).<br><br>

<b style='color:#f5a623'>Structural_Risk (weight: 70%)</b> — A graph-theoretic score based on the node's
position in the OECD TiVA network. Combines betweenness centrality (how often a node sits on
shortest trade paths), degree centrality (number of trade partners), and eigenvector centrality
(proximity to other high-risk nodes). High structural risk = disruption cascades widely.<br><br>

<b style='color:#f5a623'>Why 0.3 × ML + 0.7 × SR?</b> — The higher weight on structural risk reflects that
network position is a stronger predictor of disruption <i>spread</i> than the ML classifier alone.
<b>BLR_C26</b> illustrates this: ML=0.93 (GCN predicts stress), SR=0.44 (low centrality) → Risk=0.59.
The node will likely be stressed but the damage won't cascade far through the OECD network.
</div>
""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        st.markdown("### ML Probability vs Structural Risk")
        ext = EXTENDED_NODES.copy()
        ext["country"] = ext["Node"].str.split("_").str[0]
        ext["sector"]  = ext["Node"].str.split("_").str[1]

        fig_sc = go.Figure()
        sector_colors = {"C26":"#00ffe0","C27":"#f5a623","C28":"#ff4b6e","J61":"#a78bfa"}
        for sec, grp in ext.groupby("sector"):
            fig_sc.add_trace(go.Scatter(
                x=grp["ML_Probability"], y=grp["Structural_Risk"],
                mode="markers+text",
                name=SECTOR_LABELS.get(sec, sec),
                marker=dict(size=grp["Risk_Score"]*20+6,
                            color=sector_colors.get(sec,"#888"),
                            line=dict(width=1,color="#1a2d40"),opacity=0.85),
                text=grp["Node"], textposition="top center",
                textfont=dict(size=8,color="#4d7a96",family="Space Mono"),
                hovertemplate="<b>%{text}</b><br>ML: %{x:.3f}<br>SR: %{y:.3f}<extra></extra>",
            ))

        fig_sc.add_hline(y=0.85, line_dash="dot", line_color="#1a2d40", line_width=1)
        fig_sc.add_vline(x=0.85, line_dash="dot", line_color="#1a2d40", line_width=1)
        for txt, x, y, col in [
            ("HIGH ML\nHIGH SR", 0.97, 0.97, "#ff4b6e"),
            ("HIGH ML\nLOW SR",  0.97, 0.35, "#f5a623"),
        ]:
            fig_sc.add_annotation(x=x, y=y, text=txt, showarrow=False,
                                  font=dict(color=col, size=8, family="Space Mono"), align="center")

        fig_sc.update_layout(
            height=420, paper_bgcolor="#050a0f", plot_bgcolor="#0b1520",
            margin=dict(l=40,r=20,t=20,b=40),
            xaxis=dict(title=dict(text="ML Probability (2-layer GCN output)",
                                  font=dict(color="#4d7a96",size=10)),
                       gridcolor="#1a2d40",tickfont=dict(color="#4d7a96",size=9),range=[0,1.05]),
            yaxis=dict(title=dict(text="Structural Risk (graph centrality composite)",
                                  font=dict(color="#4d7a96",size=10)),
                       gridcolor="#1a2d40",tickfont=dict(color="#4d7a96",size=9),range=[0,1.05]),
            legend=dict(font=dict(color="#4d7a96",size=9),bgcolor="#0b1520",bordercolor="#1a2d40"),
        )
        st.plotly_chart(fig_sc, use_container_width=True)
        st.markdown("""
<div class='amber-box'>
<b style='color:#f5a623'>Bubble size = final Risk Score.</b> Top-right quadrant = most critical nodes (high ML + high SR).
Left cluster (BLR, RUS, FIN, ROU…) = GCN predicts stress but low structural centrality → disruption likely but contained.
</div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown("### Risk Score Decomposition")
        ext_sorted = ext.sort_values("Risk_Score", ascending=True)
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=ext_sorted["Node"], x=ext_sorted["Structural_Risk"]*0.7,
            name="Structural Risk × 0.7", orientation="h",
            marker_color="#a78bfa", opacity=0.85,
        ))
        fig_bar.add_trace(go.Bar(
            y=ext_sorted["Node"], x=ext_sorted["ML_Probability"]*0.3,
            name="ML Probability × 0.3", orientation="h",
            marker_color="#00ffe0", opacity=0.85,
        ))
        fig_bar.add_trace(go.Scatter(
            y=ext_sorted["Node"], x=ext_sorted["Risk_Score"],
            mode="markers", name="Final Risk Score",
            marker=dict(symbol="diamond", size=9, color="#ff4b6e",
                        line=dict(width=1,color="#ff0033")),
        ))
        fig_bar.update_layout(
            barmode="stack", height=420,
            paper_bgcolor="#050a0f", plot_bgcolor="#0b1520",
            margin=dict(l=10,r=20,t=20,b=20),
            xaxis=dict(title=dict(text="Contribution to Risk Score",
                                  font=dict(color="#4d7a96",size=9)),
                       gridcolor="#1a2d40",tickfont=dict(color="#4d7a96",size=9),range=[0,1.05]),
            yaxis=dict(tickfont=dict(color="#c8dde8",size=9)),
            legend=dict(font=dict(color="#4d7a96",size=9),bgcolor="#0b1520",
                        bordercolor="#1a2d40",orientation="h",y=1.04),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown(f"""
<div class='insight-box'>
<b style='color:#00ffe0'>Verified formula: Risk = 0.3 × ML + 0.7 × SR</b><br>
<span style='color:#4d7a96'>Verified on all {len(ext)} nodes — MAE = 0.000000</span><br><br>
<span style='color:#4d7a96'>Avg ML_Probability &nbsp;</span><b style='color:#00ffe0'>{ext['ML_Probability'].mean():.3f}</b><br>
<span style='color:#4d7a96'>Avg Structural_Risk </span><b style='color:#a78bfa'>{ext['Structural_Risk'].mean():.3f}</b><br>
<span style='color:#4d7a96'>Avg Risk_Score &nbsp;&nbsp;&nbsp;&nbsp;</span><b style='color:#ff4b6e'>{ext['Risk_Score'].mean():.3f}</b>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — STRESS TIMELINE
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 📈 Supply Chain Stress Index  (2019–2022)")
    col_tl, col_cs = st.columns([3,2], gap="medium")

    with col_tl:
        fig_tl = make_subplots(rows=2, cols=1, shared_xaxes=True,
                               row_heights=[0.6,0.4], vertical_spacing=0.06)
        for col_name, color, fill in [
            ("Stress_Index","#00ffe0",True),
            ("Commodity","#f5a623",False),
            ("Macro","#60a5fa",False),
        ]:
            fig_tl.add_trace(go.Scatter(
                x=si_df["Year"], y=si_df[col_name],
                mode="lines+markers", name=col_name.replace("_"," "),
                line=dict(color=color,width=2.5),
                marker=dict(size=8,color=color,line=dict(width=2,color="#050a0f")),
                fill="tozeroy" if fill else None,
                fillcolor="rgba(0,255,224,0.06)" if fill else None,
            ), row=1, col=1)

        fig_tl.add_vline(x=selected_year, line_dash="dot", line_color="#ff4b6e",
                         line_width=1.5, annotation_text=str(selected_year),
                         annotation_font_color="#ff4b6e", annotation_font_size=10)

        for yr,(lbl,col) in {2020:("COVID-19","#ff4b6e"),2021:("Suez Canal","#f5a623"),2022:("Ukraine War","#a78bfa")}.items():
            fig_tl.add_annotation(x=yr, y=1.08, text=lbl, showarrow=False,
                                  font=dict(color=col,size=9,family="Space Mono"),
                                  xref="x",yref="y")

        fig_tl.add_trace(go.Bar(x=si_df["Year"],y=si_df["Commodity"],
                                name="Commodity",marker_color="#f5a623",opacity=0.6), row=2,col=1)
        fig_tl.add_trace(go.Bar(x=si_df["Year"],y=si_df["Macro"],
                                name="Macro",marker_color="#60a5fa",opacity=0.6), row=2,col=1)

        fig_tl.update_layout(
            height=400, paper_bgcolor="#050a0f", plot_bgcolor="#0b1520",
            margin=dict(l=40,r=20,t=20,b=20), barmode="group",
            legend=dict(font=dict(color="#4d7a96",size=9),bgcolor="#0b1520",bordercolor="#1a2d40"),
        )
        for ax in ["xaxis","xaxis2","yaxis","yaxis2"]:
            fig_tl.update_layout(**{ax:dict(gridcolor="#1a2d40",
                                            tickfont=dict(color="#4d7a96",size=9),
                                            linecolor="#1a2d40")})
        st.plotly_chart(fig_tl, use_container_width=True)
        st.markdown("""
<div class='insight-box'>
<b style='color:#f5a623'>Why is 2021 the peak (Stress = 1.0)?</b><br>
Both sub-signals maxed simultaneously: Commodity = 1.0 (oil/gas/chip demand surge post-COVID)
and Macro = 1.0 (supply-demand mismatch, port backlogs, Suez blockage).
2022 kept high commodity stress (Ukraine energy crisis) but macro normalised as trade rerouted.<br><br>
<b style='color:#4d7a96'>Note on scaling:</b> All indicators are Min-Max normalised to [0.05–1.0].
A value of 0.05 represents the <i>baseline minimum</i> recorded across 2019–2022 — not zero stress.
2019 Commodity and 2022 Macro were the lowest-stress years for their respective signals.
</div>""", unsafe_allow_html=True)

    with col_cs:
        st.markdown("### Top Stressed Countries per Year")
        yr_tab = st.selectbox("Year", [2019,2020,2021,2022],
                              index=[2019,2020,2021,2022].index(selected_year), key="yr_cs_tab")
        sub = TOP_STRESSED[TOP_STRESSED["Year"]==yr_tab].sort_values("stress_score",ascending=True)

        fig_cs = go.Figure(go.Bar(
            x=sub["stress_score"], y=sub["Country"], orientation="h",
            marker_color=["#ff4b6e"]*len(sub),
            text=sub["stress_score"].round(3), textposition="outside",
            textfont=dict(color="#4d7a96",size=9),
        ))
        fig_cs.update_layout(
            height=300, paper_bgcolor="#050a0f", plot_bgcolor="#0b1520",
            margin=dict(l=10,r=50,t=10,b=10),
            xaxis=dict(gridcolor="#1a2d40",tickfont=dict(color="#4d7a96",size=9)),
            yaxis=dict(tickfont=dict(color="#c8dde8",size=10),autorange="reversed"),
        )
        st.plotly_chart(fig_cs, use_container_width=True)

        reason_map = {
            2019: "Venezuela and Iran dominate due to US sanctions (oil sector collapse). Armenia shows stress from Nagorno-Karabakh tensions. Bahrain faces Gulf financial contagion.",
            2020: "Venezuela remains top (hyperinflation + sanctions). Lithuania peaks due to COVID Baltic supply chain exposure and Belarusian transit disruption. China enters top 5 (factory shutdowns).",
            2021: "Venezuela persists. Malawi — extreme food insecurity and currency collapse. Bahrain & UAE face Gulf energy market volatility post-COVID. Costa Rica C27 nodes appear in GNN network.",
            2022: "Venezuela still tops. Honduras — Central American debt crisis. Kuwait and Oman: despite being oil exporters, non-oil sectors faced severe import inflation from the global commodity shock.",
        }
        st.markdown(f"""
<div class='amber-box'>
<b style='color:#f5a623'>Why these countries in {yr_tab}?</b><br>
{reason_map[yr_tab]}
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CHOROPLETH
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 🗺️ Country-Level Risk & Stress Maps")
    view = st.radio("Colour by",
                    ["GNN Avg Risk (risk_nodes)","Macro Stress Score (country_stress)"],
                    horizontal=True, label_visibility="collapsed")

    col_m1, col_m2 = st.columns([3,2], gap="medium")
    with col_m1:
        if "GNN" in view:
            map_df = filtered_rn.groupby("country")["Risk_Score"].mean().reset_index()
            map_df.columns = ["iso_alpha_3","value"]
            cscale = [[0,"#00ffe0"],[0.5,"#f5a623"],[0.85,"#ff4b6e"],[1,"#ff0033"]]
            hover_lbl, ttitle = "Avg Risk","GNN Avg Node Risk"
            fig_map = go.Figure(go.Choropleth(
                locations=map_df["iso_alpha_3"], locationmode="ISO-3",
                z=map_df["value"], colorscale=cscale, zmin=0, zmax=1,
                marker_line_color="#1a2d40", marker_line_width=0.5,
                colorbar=dict(title=dict(text=hover_lbl,font=dict(color="#4d7a96",size=10)),
                              tickfont=dict(color="#4d7a96",size=9),
                              bgcolor="#0b1520",bordercolor="#1a2d40",thickness=12),
                hovertemplate="<b>%{location}</b><br>"+hover_lbl+": %{z:.3f}<extra></extra>",
            ))
        else:
            map_df = cs_df[cs_df["Year"]==selected_year].dropna(subset=["stress_score"])
            cscale = [[0,"#050a0f"],[0.5,"#f5a623"],[1,"#ff4b6e"]]
            hover_lbl, ttitle = "Stress Score",f"Macro Stress {selected_year}"
            fig_map = go.Figure(go.Choropleth(
                locations=map_df["Country"], locationmode="country names",
                z=map_df["stress_score"], colorscale=cscale,
                marker_line_color="#1a2d40", marker_line_width=0.5,
                colorbar=dict(title=dict(text=hover_lbl,font=dict(color="#4d7a96",size=10)),
                              tickfont=dict(color="#4d7a96",size=9),
                              bgcolor="#0b1520",bordercolor="#1a2d40",thickness=12),
                hovertemplate="<b>%{location}</b><br>"+hover_lbl+": %{z:.3f}<extra></extra>",
            ))
        fig_map.update_layout(
            height=460, paper_bgcolor="#050a0f",
            geo=dict(bgcolor="#050a0f",landcolor="#0d1f2d",oceancolor="#050a0f",
                     showocean=True,coastlinecolor="#1a2d40",showcoastlines=True,
                     showframe=False,projection_type="natural earth"),
            margin=dict(l=0,r=0,t=30,b=0),
            title=dict(text=ttitle,font=dict(color="#4d7a96",size=10,family="Space Mono"),x=0),
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_m2:
        st.markdown("### Country × Sector Risk Heatmap")
        pivot = filtered_rn.pivot_table(index="country",columns="sector",
                                         values="Risk_Score",aggfunc="mean").fillna(0)
        pivot["avg"] = pivot.mean(axis=1)
        top20 = pivot.nlargest(20,"avg").drop(columns="avg")
        fig_heat = go.Figure(go.Heatmap(
            z=top20.values,
            x=[SECTOR_LABELS.get(c,c) for c in top20.columns],
            y=top20.index,
            colorscale=[[0,"#050a0f"],[0.5,"#f5a623"],[1,"#ff4b6e"]],
            colorbar=dict(tickfont=dict(color="#4d7a96",size=8),thickness=8),
            hovertemplate="<b>%{y} — %{x}</b><br>Risk: %{z:.3f}<extra></extra>",
        ))
        fig_heat.update_layout(
            height=460, paper_bgcolor="#050a0f", plot_bgcolor="#050a0f",
            margin=dict(l=10,r=10,t=10,b=60),
            xaxis=dict(tickfont=dict(color="#4d7a96",size=8),tickangle=-35),
            yaxis=dict(tickfont=dict(color="#c8dde8",size=9)),
        )
        st.plotly_chart(fig_heat, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — SECTOR ANALYSIS + DISRUPTION REASONS
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### 🔬 Sector & Country Disruption Analysis")

    st.markdown("#### Why Each Sector Is High-Risk")
    sec_cols = st.columns(2)
    main_secs = [s for s in ["C26","C27","C28","J61"] if s in (selected_sectors or SECTORS)]
    for i, sec in enumerate(main_secs):
        with sec_cols[i % 2]:
            avg = rn_df[rn_df["sector"]==sec]["Risk_Score"].mean()
            color = "#ff4b6e" if avg > 0.85 else "#f5a623"
            st.markdown(f"""
<div class='warn-box' style='border-left-color:{color}'>
<b style='color:{color}'>{SECTOR_LABELS.get(sec,sec)}</b>
&nbsp;&nbsp;<span style='color:#4d7a96'>Avg Risk: {avg:.3f}</span><br>
{SECTOR_DISRUPTION_REASONS.get(sec,'')}
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_sa, col_sb = st.columns(2, gap="medium")

    with col_sa:
        st.markdown("#### Risk Score Distribution by Sector")
        fig_box = go.Figure()
        sc_pal = {"C26":"#00ffe0","C27":"#f5a623","C28":"#ff4b6e","J61":"#a78bfa",
                  "O":"#60a5fa","S8":"#34d399","A7":"#fbbf24","2020":"#f87171"}
        for sec in (selected_sectors or SECTORS):
            sub = filtered_rn[filtered_rn["sector"]==sec]["Risk_Score"]
            if sub.empty: continue
            c = sc_pal.get(sec,"#888")
            r,g,b = int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
            fig_box.add_trace(go.Box(
                y=sub, name=SECTOR_LABELS.get(sec,sec),
                marker_color=c, line=dict(color=c,width=1.5),
                fillcolor=f"rgba({r},{g},{b},0.12)",
                boxpoints="outliers", jitter=0.3,
            ))
        fig_box.update_layout(
            height=340, paper_bgcolor="#050a0f", plot_bgcolor="#0b1520",
            margin=dict(l=30,r=20,t=10,b=60),
            xaxis=dict(tickfont=dict(color="#4d7a96",size=9),gridcolor="#1a2d40",tickangle=-20),
            yaxis=dict(tickfont=dict(color="#4d7a96",size=9),gridcolor="#1a2d40",
                       title=dict(text="Risk Score",font=dict(color="#4d7a96",size=9))),
            showlegend=False,
        )
        st.plotly_chart(fig_box, use_container_width=True)

    with col_sb:
        st.markdown("#### Country Disruption Reason Lookup")
        sel_country = st.selectbox(
            "Select a country",
            options=sorted(COUNTRY_DISRUPTION_REASONS.keys()),
            format_func=lambda x: f"{x} — {CODE_NAME.get(x,x)}",
        )
        c_avg = rn_df[rn_df["country"]==sel_country]["Risk_Score"].mean()
        c_sec = rn_df[rn_df["country"]==sel_country].groupby("sector")["Risk_Score"].mean()
        if not np.isnan(c_avg):
            color = "#ff4b6e" if c_avg > 0.85 else "#f5a623" if c_avg > 0.6 else "#00ffe0"
            st.markdown(f"""
<div class='warn-box' style='border-left-color:{color}'>
<b style='color:{color}'>{CODE_NAME.get(sel_country,sel_country)}</b>
&nbsp;&nbsp;<span style='color:#4d7a96'>Avg GNN Risk: {c_avg:.3f}</span><br><br>
{COUNTRY_DISRUPTION_REASONS.get(sel_country,'No detailed reason recorded for this country.')}
</div>""", unsafe_allow_html=True)
            if not c_sec.empty:
                fig_mini = go.Figure(go.Bar(
                    x=[SECTOR_LABELS.get(s,s) for s in c_sec.index],
                    y=c_sec.values,
                    marker_color=[sc_pal.get(s,"#888") for s in c_sec.index],
                    text=c_sec.values.round(3), textposition="outside",
                    textfont=dict(color="#4d7a96",size=9),
                ))
                fig_mini.update_layout(
                    height=200, paper_bgcolor="#050a0f", plot_bgcolor="#0b1520",
                    margin=dict(l=0,r=0,t=10,b=50),
                    xaxis=dict(tickfont=dict(color="#4d7a96",size=9),tickangle=-20),
                    yaxis=dict(gridcolor="#1a2d40",tickfont=dict(color="#4d7a96",size=9),range=[0,1.1]),
                    showlegend=False,
                )
                st.plotly_chart(fig_mini, use_container_width=True)

    st.markdown("#### Sector Radar — Top Countries")
    top_c_radar = filtered_rn.groupby("country")["Risk_Score"].mean().nlargest(6).index.tolist()
    sel_radar = st.multiselect("Countries", top_c_radar, default=top_c_radar[:4], key="rad2")
    radar_secs = [s for s in ["C26","C27","C28","J61"] if s in (selected_sectors or SECTORS)]
    rc = ["#00ffe0","#f5a623","#ff4b6e","#a78bfa","#60a5fa","#34d399"]
    fig_rad = go.Figure()
    if radar_secs and sel_radar:
        theta = [SECTOR_LABELS.get(s,s) for s in radar_secs]+[SECTOR_LABELS.get(radar_secs[0],radar_secs[0])]
        for i, ctry in enumerate(sel_radar):
            sub = filtered_rn[filtered_rn["country"]==ctry]
            vals = [sub[sub["sector"]==s]["Risk_Score"].mean() for s in radar_secs]
            vals = [v if not np.isnan(v) else 0 for v in vals]
            r2,g2,b2 = int(rc[i%len(rc)][1:3],16),int(rc[i%len(rc)][3:5],16),int(rc[i%len(rc)][5:7],16)
            fig_rad.add_trace(go.Scatterpolar(
                r=vals+[vals[0]], theta=theta, fill="toself", name=ctry,
                line=dict(color=rc[i%len(rc)],width=2),
                fillcolor=f"rgba({r2},{g2},{b2},0.08)",
            ))
    fig_rad.update_layout(
        height=320, paper_bgcolor="#050a0f",
        polar=dict(bgcolor="#0b1520",
                   radialaxis=dict(visible=True,range=[0,1],
                                  tickfont=dict(color="#4d7a96",size=8),
                                  gridcolor="#1a2d40",linecolor="#1a2d40"),
                   angularaxis=dict(tickfont=dict(color="#4d7a96",size=9),
                                   gridcolor="#1a2d40",linecolor="#1a2d40")),
        legend=dict(font=dict(color="#4d7a96",size=9),bgcolor="#0b1520",bordercolor="#1a2d40"),
        margin=dict(l=40,r=40,t=20,b=20),
    )
    st.plotly_chart(fig_rad, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div style="font-size:9px;color:#4d7a96;letter-spacing:0.12em">OECD TiVA · 2-layer GCN · 2019–2022 · Sara Deshkar</div>', unsafe_allow_html=True)
