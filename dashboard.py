import streamlit as st
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from textblob import TextBlob
import streamlit.components.v1 as components
from pyvis.network import Network
from neo4j import GraphDatabase
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Milano-Cortina 2026 ❄️", page_icon="🏔️", layout="wide")

# --- CUSTOM CSS : Thème Olympique Hivernal ---
st.markdown("""
<style>
    /* === POLICE & FOND GLOBAL === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(160deg, #0a0e27 0%, #0d1b3e 40%, #0f1f45 70%, #0a0e27 100%);
    }
    
    /* === SIDEBAR STYLÉE === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1b3e 0%, #162447 50%, #1a1a5e 100%) !important;
        border-right: 1px solid rgba(100, 180, 255, 0.15);
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #c8d6e5 !important;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #74b9ff !important;
    }
    
    /* === HEADER HERO === */
    .hero-container {
        background: linear-gradient(135deg, rgba(15,25,60,0.95) 0%, rgba(20,40,90,0.9) 50%, rgba(30,50,100,0.85) 100%);
        border: 1px solid rgba(100, 180, 255, 0.2);
        border-radius: 20px;
        padding: 2.5rem 2rem;
        margin-bottom: 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 100, 255, 0.15), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .hero-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(ellipse at center, rgba(100,180,255,0.05) 0%, transparent 60%);
        animation: shimmer 8s ease-in-out infinite;
    }
    @keyframes shimmer {
        0%, 100% { transform: translateX(-20%) translateY(-20%); }
        50% { transform: translateX(20%) translateY(20%); }
    }
    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #74b9ff, #a29bfe, #fd79a8, #ffeaa7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        position: relative;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        color: #b2bec3;
        font-size: 1.05rem;
        font-weight: 300;
        letter-spacing: 2px;
        text-transform: uppercase;
        position: relative;
    }
    .hero-rings {
        font-size: 1.8rem;
        margin-top: 0.8rem;
        position: relative;
        letter-spacing: 6px;
    }
    
    /* === CARTES MÉTRIQUES STYLÉES === */
    .metric-card {
        background: linear-gradient(145deg, rgba(20,30,65,0.9), rgba(25,40,80,0.8));
        border: 1px solid rgba(100, 180, 255, 0.15);
        border-radius: 16px;
        padding: 1.8rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 4px 20px rgba(0, 50, 150, 0.2);
        position: relative;
        overflow: hidden;
    }
    .metric-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 16px 16px 0 0;
    }
    .metric-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 40px rgba(0, 100, 255, 0.25);
        border-color: rgba(100, 180, 255, 0.35);
    }
    .metric-card.blue::after { background: linear-gradient(90deg, #0984e3, #74b9ff); }
    .metric-card.purple::after { background: linear-gradient(90deg, #6c5ce7, #a29bfe); }
    .metric-card.gold::after { background: linear-gradient(90deg, #f39c12, #ffeaa7); }
    .metric-card.pink::after { background: linear-gradient(90deg, #e84393, #fd79a8); }
    
    .metric-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 2.8rem;
        font-weight: 800;
        color: #ffffff;
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .metric-label {
        color: #b2bec3;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* === SECTION TITLES === */
    .section-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 2rem 0 1.2rem 0;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid rgba(100, 180, 255, 0.1);
    }
    .section-header h2 {
        color: #dfe6e9;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }
    .section-badge {
        background: linear-gradient(135deg, #0984e3, #6c5ce7);
        color: white;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* === GLASSMORPHISM PANELS === */
    .glass-panel {
        background: rgba(15, 25, 55, 0.7);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(100, 180, 255, 0.12);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 24px rgba(0, 30, 100, 0.15);
    }
    
    /* === TABLE DES TWEETS POPULAIRES === */
    .tweet-row {
        display: flex;
        align-items: center;
        padding: 0.7rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.4rem;
        transition: background 0.3s;
    }
    .tweet-row:hover {
        background: rgba(100, 180, 255, 0.08);
    }
    .tweet-rank {
        font-size: 1.4rem;
        font-weight: 800;
        width: 40px;
        color: #636e72;
    }
    .tweet-rank.gold { color: #ffd700; }
    .tweet-rank.silver { color: #c0c0c0; }
    .tweet-rank.bronze { color: #cd7f32; }
    .tweet-text {
        flex: 1;
        color: #dfe6e9;
        font-size: 0.88rem;
        line-height: 1.4;
        margin: 0 1rem;
    }
    .tweet-likes {
        background: rgba(255, 107, 107, 0.15);
        color: #ff6b6b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        white-space: nowrap;
    }
    
    /* === BOUTONS CUSTOM === */
    .stButton > button {
        background: linear-gradient(135deg, #0984e3 0%, #6c5ce7 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.7rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        letter-spacing: 0.5px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(9, 132, 227, 0.3) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(9, 132, 227, 0.5) !important;
    }
    
    /* === ANIMATION NEIGE === */
    .snowfall {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9999;
        overflow: hidden;
    }
    .snowflake {
        position: absolute;
        top: -10px;
        color: rgba(255,255,255,0.5);
        font-size: 1rem;
        animation: fall linear infinite;
    }
    @keyframes fall {
        0% { transform: translateY(-10px) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0.2; }
    }
    
    /* === STYLE PLOTLY CONTAINERS === */
    .stPlotlyChart {
        border-radius: 16px;
        overflow: hidden;
    }
    
    /* === INFO CARDS === */
    .info-pill {
        display: inline-block;
        background: rgba(100, 180, 255, 0.1);
        border: 1px solid rgba(100, 180, 255, 0.2);
        color: #74b9ff;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        margin: 4px;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Fix text colors */
    .stMarkdown p, .stMarkdown li { color: #b2bec3; }
    h1, h2, h3 { color: #dfe6e9 !important; }
</style>
""", unsafe_allow_html=True)

# --- ANIMATION NEIGE (subtile) ---
snow_html = """
<div class="snowfall">
""" + "".join([
    f'<div class="snowflake" style="left:{i*4.3}%;animation-duration:{3+i%5}s;animation-delay:{i*0.4}s;font-size:{0.5+i%3*0.3}rem;">❄</div>'
    for i in range(22)
]) + """
</div>
"""
components.html(snow_html, height=0)

# --- HERO HEADER ---
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Milano-Cortina 2026</div>
    <div class="hero-subtitle">Social Intelligence Dashboard</div>
    <div class="hero-rings">🔵🟡⚫🟢🔴</div>
</div>
""", unsafe_allow_html=True)

# --- 2. CONNEXIONS AUX BASES ---
@st.cache_resource
def init_connections():
    load_dotenv()
    mongo_client = MongoClient(os.getenv("MONGO_URI"))
    db = mongo_client["milano2026"]
    return db

db = init_connections()

# --- 3. SIDEBAR STYLÉE ---
st.sidebar.markdown("""
<div style="text-align:center; padding: 1rem 0;">
    <div style="font-size:3rem;">🏔️</div>
    <div style="font-size:1.2rem; font-weight:700; color:#74b9ff; letter-spacing:1px;">MILANO 2026</div>
    <div style="font-size:0.75rem; color:#636e72; letter-spacing:2px; text-transform:uppercase;">Centre de Commande</div>
    <hr style="border: none; border-top: 1px solid rgba(100,180,255,0.15); margin: 1rem 0;">
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "🧭 Navigation",
    ("📊 Statistiques Globales", "🧠 Analyse de Sentiments (IA)", "🌐 Graphe Réseau (Neo4j)")
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="text-align:center; padding: 0.5rem; opacity: 0.6;">
    <div style="font-size:0.7rem; color:#636e72;">Propulsé par</div>
    <div style="font-size:0.8rem; color:#b2bec3;">MongoDB · Neo4j · TextBlob</div>
</div>
""", unsafe_allow_html=True)

# ===================================================
# 📊 VUE 1 : STATISTIQUES GLOBALES (ENRICHIE)
# ===================================================
if menu == "📊 Statistiques Globales":
    
    # --- Métriques principales avec cartes stylées ---
    nb_users = db.users.count_documents({})
    nb_tweets = db.tweets.count_documents({})
    nb_hashtags = len(db.tweets.distinct("hashtags"))
    nb_replies = db.tweets.count_documents({"in_reply_to_tweet_id": {"$ne": None}})
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card blue">
            <div class="metric-icon">👥</div>
            <div class="metric-value">{nb_users}</div>
            <div class="metric-label">Utilisateurs</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card purple">
            <div class="metric-icon">💬</div>
            <div class="metric-value">{nb_tweets}</div>
            <div class="metric-label">Tweets Publiés</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card gold">
            <div class="metric-icon">#️⃣</div>
            <div class="metric-value">{nb_hashtags}</div>
            <div class="metric-label">Hashtags Uniques</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card pink">
            <div class="metric-icon">↩️</div>
            <div class="metric-value">{nb_replies}</div>
            <div class="metric-label">Réponses</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # --- Deux colonnes : Top Hashtags + Répartition Rôles ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("""
        <div class="section-header">
            <h2>🔥 Top 10 Hashtags</h2>
            <span class="section-badge">MongoDB</span>
        </div>""", unsafe_allow_html=True)
        
        pipeline = [
            {"$unwind": "$hashtags"},
            {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        data_hashtags = list(db.tweets.aggregate(pipeline))
        
        if data_hashtags:
            labels = [item['_id'] for item in data_hashtags]
            counts = [item['count'] for item in data_hashtags]
            
            colors_gradient = [
                '#0984e3', '#0984e3', '#6c5ce7', '#6c5ce7', '#a29bfe',
                '#a29bfe', '#74b9ff', '#74b9ff', '#81ecec', '#81ecec'
            ]
            
            fig_hash = go.Figure(go.Bar(
                x=counts[::-1],
                y=labels[::-1],
                orientation='h',
                marker=dict(
                    color=colors_gradient[:len(labels)][::-1],
                    line=dict(width=0),
                    cornerradius=6
                ),
                text=counts[::-1],
                textposition='outside',
                textfont=dict(color='#b2bec3', size=12, family='Inter')
            ))
            fig_hash.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#b2bec3', family='Inter'),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                yaxis=dict(showgrid=False, tickfont=dict(size=13, color='#dfe6e9')),
                margin=dict(l=10, r=60, t=20, b=20),
                height=400,
                bargap=0.25
            )
            st.plotly_chart(fig_hash, use_container_width=True, config={'displayModeBar': False})
    
    with col_right:
        st.markdown("""
        <div class="section-header">
            <h2>🎭 Répartition par Rôle</h2>
            <span class="section-badge">MongoDB</span>
        </div>""", unsafe_allow_html=True)
        
        pipeline_roles = [
            {"$group": {"_id": "$role", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        data_roles = list(db.users.aggregate(pipeline_roles))
        
        if data_roles:
            role_labels = [r['_id'].capitalize() for r in data_roles]
            role_counts = [r['count'] for r in data_roles]
            role_colors = ['#0984e3', '#6c5ce7', '#fd79a8', '#ffeaa7', '#55efc4', '#ff7675']
            
            fig_roles = go.Figure(go.Pie(
                labels=role_labels,
                values=role_counts,
                hole=0.55,
                marker=dict(colors=role_colors[:len(role_labels)], line=dict(color='#0a0e27', width=3)),
                textinfo='label+percent',
                textfont=dict(size=13, color='white', family='Inter'),
                hovertemplate="<b>%{label}</b><br>%{value} utilisateurs<br>%{percent}<extra></extra>"
            ))
            fig_roles.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#b2bec3', family='Inter'),
                showlegend=True,
                legend=dict(
                    font=dict(size=12, color='#b2bec3'),
                    bgcolor='rgba(0,0,0,0)'
                ),
                margin=dict(l=20, r=20, t=20, b=20),
                height=400,
                annotations=[dict(
                    text=f"<b>{nb_users}</b><br>Users", 
                    x=0.5, y=0.5, font_size=18, showarrow=False,
                    font=dict(color='#dfe6e9', family='Inter')
                )]
            )
            st.plotly_chart(fig_roles, use_container_width=True, config={'displayModeBar': False})
    
    # --- Top 5 Tweets les plus populaires ---
    st.markdown("""
    <div class="section-header">
        <h2>🏆 Tweets les plus populaires</h2>
        <span class="section-badge">Top 5</span>
    </div>""", unsafe_allow_html=True)
    
    top_tweets = list(db.tweets.find({}, {"_id": 0, "tweet_id": 1, "text": 1, "favorite_count": 1, "user_id": 1})
                      .sort("favorite_count", -1).limit(5))
    
    medals = ["gold", "silver", "bronze", "", ""]
    medal_icons = ["🥇", "🥈", "🥉", "4", "5"]
    
    for i, tweet in enumerate(top_tweets):
        # Récupérer le username
        user = db.users.find_one({"user_id": tweet.get("user_id")}, {"_id": 0, "username": 1})
        username = user.get("username", "Inconnu") if user else "Inconnu"
        text_preview = tweet.get("text", "")[:120]
        rank_class = medals[i] if i < 3 else ""
        
        st.markdown(f"""
        <div class="tweet-row">
            <div class="tweet-rank {rank_class}">{medal_icons[i]}</div>
            <div class="tweet-text">
                <strong style="color:#74b9ff;">@{username}</strong><br>{text_preview}
            </div>
            <div class="tweet-likes">❤️ {tweet.get('favorite_count', 0):,}</div>
        </div>""", unsafe_allow_html=True)
    
    # --- Activité par Pays ---
    st.markdown("""
    <div class="section-header">
        <h2>🌍 Répartition par Pays</h2>
        <span class="section-badge">Géographie</span>
    </div>""", unsafe_allow_html=True)
    
    pipeline_country = [
        {"$group": {"_id": "$country", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    data_country = list(db.users.aggregate(pipeline_country))
    
    if data_country:
        country_labels = [c['_id'] for c in data_country]
        country_counts = [c['count'] for c in data_country]
        
        fig_country = go.Figure(go.Bar(
            x=country_labels,
            y=country_counts,
            marker=dict(
                color=country_counts,
                colorscale=[[0, '#6c5ce7'], [0.5, '#0984e3'], [1, '#00cec9']],
                line=dict(width=0),
                cornerradius=8
            ),
            text=country_counts,
            textposition='outside',
            textfont=dict(color='#b2bec3', size=12, family='Inter')
        ))
        fig_country.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#b2bec3', family='Inter'),
            xaxis=dict(showgrid=False, tickfont=dict(size=11, color='#dfe6e9'), tickangle=-45),
            yaxis=dict(showgrid=True, gridcolor='rgba(100,180,255,0.06)', zeroline=False),
            margin=dict(l=20, r=20, t=20, b=80),
            height=350,
            bargap=0.3
        )
        st.plotly_chart(fig_country, use_container_width=True, config={'displayModeBar': False})


# ===================================================
# 🧠 VUE 2 : ANALYSE DE SENTIMENTS (IA)
# ===================================================
elif menu == "🧠 Analyse de Sentiments (IA)":
    
    st.markdown("""
    <div class="section-header">
        <h2>🧠 Analyse de Sentiments par IA</h2>
        <span class="section-badge">TextBlob NLP</span>
    </div>
    <div class="glass-panel">
        <p style="color:#dfe6e9; margin:0;">
            Cette intelligence artificielle analyse le <strong>texte de chaque tweet</strong> pour déterminer
            s'il exprime une opinion <span style="color:#55efc4;">positive</span>, 
            <span style="color:#ff6b6b;">négative</span> ou 
            <span style="color:#b2bec3;">neutre</span>.
            L'algorithme utilise le traitement du langage naturel (NLP) via <strong>TextBlob</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("⚡ Lancer l'analyse IA"):
        with st.spinner('🔍 Lecture et analyse NLP des tweets...'):
            tweets = list(db.tweets.find({}, {"_id": 0, "text": 1, "tweet_id": 1}))
            positif, negatif, neutre = 0, 0, 0
            scores = []
            
            progress = st.progress(0)
            for idx, t in enumerate(tweets):
                score = TextBlob(t.get("text", "")).sentiment.polarity
                scores.append(score)
                if score > 0.1: positif += 1
                elif score < -0.1: negatif += 1
                else: neutre += 1
                progress.progress((idx + 1) / len(tweets))
            
            progress.empty()
            total = positif + negatif + neutre
            
            # --- Métriques Sentiments ---
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                pct_pos = round(positif/total*100, 1) if total else 0
                st.markdown(f"""
                <div class="metric-card blue">
                    <div class="metric-icon">😊</div>
                    <div class="metric-value" style="color:#55efc4;">{positif}</div>
                    <div class="metric-label">Positifs ({pct_pos}%)</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                pct_neu = round(neutre/total*100, 1) if total else 0
                st.markdown(f"""
                <div class="metric-card gold">
                    <div class="metric-icon">😐</div>
                    <div class="metric-value" style="color:#ffeaa7;">{neutre}</div>
                    <div class="metric-label">Neutres ({pct_neu}%)</div>
                </div>""", unsafe_allow_html=True)
            with c3:
                pct_neg = round(negatif/total*100, 1) if total else 0
                st.markdown(f"""
                <div class="metric-card pink">
                    <div class="metric-icon">😠</div>
                    <div class="metric-value" style="color:#ff6b6b;">{negatif}</div>
                    <div class="metric-label">Négatifs ({pct_neg}%)</div>
                </div>""", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # --- Graphiques côte à côte ---
            col_pie, col_hist = st.columns(2)
            
            with col_pie:
                fig_sent = go.Figure(go.Pie(
                    labels=['Positifs 😊', 'Neutres 😐', 'Négatifs 😠'],
                    values=[positif, neutre, negatif],
                    hole=0.6,
                    marker=dict(
                        colors=['#55efc4', '#ffeaa7', '#ff6b6b'],
                        line=dict(color='#0a0e27', width=4)
                    ),
                    textinfo='percent',
                    textfont=dict(size=16, color='white', family='Inter'),
                    hovertemplate="<b>%{label}</b><br>%{value} tweets<br>%{percent}<extra></extra>"
                ))
                fig_sent.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#b2bec3', family='Inter'),
                    showlegend=True,
                    legend=dict(font=dict(size=12, color='#b2bec3'), bgcolor='rgba(0,0,0,0)',
                                orientation='h', yanchor='bottom', y=-0.15, xanchor='center', x=0.5),
                    margin=dict(l=20, r=20, t=30, b=40),
                    height=380,
                    annotations=[dict(
                        text=f"<b>{total}</b><br>Tweets", 
                        x=0.5, y=0.5, font_size=20, showarrow=False,
                        font=dict(color='#dfe6e9', family='Inter')
                    )]
                )
                st.plotly_chart(fig_sent, use_container_width=True, config={'displayModeBar': False})
            
            with col_hist:
                fig_hist = go.Figure(go.Histogram(
                    x=scores,
                    nbinsx=30,
                    marker=dict(
                        color=scores,
                        colorscale=[[0, '#ff6b6b'], [0.45, '#ffeaa7'], [1, '#55efc4']],
                        line=dict(color='#0a0e27', width=1)
                    ),
                    hovertemplate="Polarité: %{x:.2f}<br>Tweets: %{y}<extra></extra>"
                ))
                fig_hist.update_layout(
                    title=dict(text="Distribution de la Polarité", font=dict(size=14, color='#dfe6e9')),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#b2bec3', family='Inter'),
                    xaxis=dict(
                        title="← Négatif | Positif →", showgrid=False,
                        zeroline=True, zerolinecolor='rgba(255,255,255,0.2)',
                        tickfont=dict(color='#b2bec3')
                    ),
                    yaxis=dict(
                        title="Nombre de tweets", showgrid=True,
                        gridcolor='rgba(100,180,255,0.06)',
                        tickfont=dict(color='#b2bec3')
                    ),
                    margin=dict(l=20, r=20, t=50, b=40),
                    height=380,
                    bargap=0.05
                )
                # Ligne verticale au centre
                fig_hist.add_vline(x=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
                st.plotly_chart(fig_hist, use_container_width=True, config={'displayModeBar': False})
            
            # --- Verdict IA ---
            dominant = "POSITIVE 😊" if positif >= max(neutre, negatif) else ("NÉGATIVE 😠" if negatif >= neutre else "NEUTRE 😐")
            avg_score = sum(scores) / len(scores) if scores else 0
            
            st.markdown(f"""
            <div class="glass-panel" style="text-align:center; margin-top:1rem;">
                <div style="font-size:0.8rem; color:#636e72; text-transform:uppercase; letter-spacing:2px;">Verdict de l'IA</div>
                <div style="font-size:1.8rem; font-weight:800; color:#74b9ff; margin:0.5rem 0;">Tendance {dominant}</div>
                <div style="color:#b2bec3;">Score moyen de polarité : <strong style="color:#ffeaa7;">{avg_score:.3f}</strong></div>
            </div>
            """, unsafe_allow_html=True)


# ===================================================
# 🌐 VUE 3 : GRAPHE RÉSEAU NEO4J
# ===================================================
elif menu == "🌐 Graphe Réseau (Neo4j)":
    
    st.markdown("""
    <div class="section-header">
        <h2>🌐 Cartographie des Influenceurs</h2>
        <span class="section-badge">Neo4j Aura</span>
    </div>
    <div class="glass-panel">
        <p style="color:#dfe6e9; margin:0;">
            Ce graphe interactif est généré en <strong>temps réel</strong> depuis la base de données graphe <strong>Neo4j Aura</strong>. 
            Il visualise les connexions sociales autour du compte officiel <span style="color:#FFA500; font-weight:600;">Milano Ops</span>.
        </p>
        <div style="margin-top:0.8rem;">
            <span class="info-pill">🟠 Nœud central = Milano Ops</span>
            <span class="info-pill">🔵 Nœuds connectés = Utilisateurs</span>
            <span class="info-pill">➡️ Arêtes = Relations</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Générer le réseau interactif"):
        with st.spinner("Interrogation de Neo4j et construction du graphe..."):
            try:
                driver = GraphDatabase.driver(
                    os.getenv("NEO4J_URI"), 
                    auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
                )
                
                # Pyvis avec style amélioré
                net = Network(height="600px", width="100%", bgcolor="#0a0e27", font_color="#dfe6e9")
                net.barnes_hut(gravity=-5000, central_gravity=0.35, spring_length=150, spring_strength=0.02)
                
                with driver.session() as session:
                    query = """
                    MATCH (m:User {username: 'Milano Ops'})-[r]-(other:User)
                    RETURN m.username AS source, type(r) AS relation, other.username AS target
                    """
                    resultats = session.run(query)
                    
                    relation_colors = {
                        "FOLLOWS": "#74b9ff",
                        "AUTHORED": "#a29bfe",
                        "RETWEETS": "#55efc4",
                    }
                    
                    for record in resultats:
                        source = record["source"]
                        cible = record["target"]
                        rel = record["relation"]
                        
                        # Milano Ops : gros nœud orange avec bordure
                        net.add_node(source, label=source, 
                                    color={"background": "#FFA500", "border": "#ffeaa7", "highlight": {"background": "#fdcb6e", "border": "#ffeaa7"}},
                                    size=35 if source == "Milano Ops" else 20,
                                    font={"size": 16 if source == "Milano Ops" else 12, "color": "#dfe6e9"},
                                    borderWidth=3 if source == "Milano Ops" else 1,
                                    shadow=True)
                        
                        net.add_node(cible, label=cible,
                                    color={"background": "#0984e3", "border": "#74b9ff", "highlight": {"background": "#74b9ff", "border": "#a29bfe"}},
                                    size=20,
                                    font={"size": 12, "color": "#dfe6e9"},
                                    borderWidth=1,
                                    shadow=True)
                        
                        edge_color = relation_colors.get(rel, "#636e72")
                        net.add_edge(source, cible, title=rel, color=edge_color, width=2, smooth={"type": "curvedCW", "roundness": 0.1})
                
                driver.close()
                
                chemin_html = "graphe_neo4j_temp.html"
                net.save_graph(chemin_html)
                
                with open(chemin_html, 'r', encoding='utf-8') as f:
                    html_data = f.read()
                    components.html(html_data, height=620)
                
                st.markdown("""
                <div class="glass-panel" style="text-align:center; margin-top:0.5rem;">
                    <span style="color:#55efc4; font-weight:600;">✅ Graphe généré avec succès</span>
                    <span style="color:#636e72;"> — Glissez et zoomez pour explorer !</span>
                </div>
                """, unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"❌ Impossible de générer le graphe. Vérifie tes identifiants Neo4j. Erreur : {e}")