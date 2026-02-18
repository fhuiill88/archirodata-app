import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="ArchiroData | Gestion Énergie", layout="wide", page_icon="⚡")

# --- STYLE PROFESSIONNEL (FORCE MODE CLAIR & TEXTE NOIR) ---
st.markdown("""
    <style>
    /* Force le fond blanc et le texte noir PARTOUT */
    .stApp {
        background-color: #ffffff !important;
        color: #1f1f1f !important;
    }
    
    /* Sidebar grise professionnelle */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        border-right: 1px solid #dee2e6;
    }
    [data-testid="stSidebar"] * { color: #1f1f1f !important; }

    /* Boîtes de métriques blanches */
    div[data-testid="stMetric"] { 
        background-color: #ffffff !important; 
        padding: 15px; 
        border-radius: 8px; 
        border: 1px solid #dee2e6; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
    }
    div[data-testid="stMetricLabel"] p { color: #6c757d !important; }
    div[data-testid="stMetricValue"] div { color: #1f1f1f !important; }

    /* Boutons bleus */
    .stButton>button { 
        width: 100%; 
        border-radius: 6px; 
        font-weight: 600; 
        background-color: #0d6efd; 
        color: white !important; 
        border: none;
        padding: 10px;
        transition: all 0.2s;
    }
    .stButton>button:hover { 
        background-color: #0b5ed7; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Textes généraux en noir */
    h1, h2, h3, p, span, div { color: #1f1f1f; }
    
    /* Logo container Sidebar */
    .logo-container { display: flex; align-items: center; gap: 12px; margin-bottom: 25px; }
    .logo-text { font-size: 24px; font-weight: 800; color: #1f1f1f !important; font-family: 'Helvetica Neue', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- AUTHENTIFICATION ---
CREDS_FILE = "credentials.json"
ADMIN_USER, ADMIN_PASS = "admin", "archiro2026"
STAFF_USER, STAFF_PASS = "staff", "energie2026"

# --- FONCTIONS SYSTÈME ---
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # 1. Essayer de charger depuis le Coffre-fort du Cloud
    if "gcp_service_account" in st.secrets:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # 2. Sinon, chercher le fichier local (sur ton PC)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def charger_donnees():
    try:
        client = get_gspread_client()
        sheet = client.open("Data_Prospection_Energie").sheet1
        valeurs = sheet.get_all_values()
        if len(valeurs) > 1:
            df = pd.DataFrame(valeurs[1:], columns=valeurs[0])
            df.columns = df.columns.str.strip()
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- GESTION SESSION ---
if 'connecte' not in st.session_state: st.session_state.connecte = False
if 'role' not in st.session_state: st.session_state.role = None

# --- 1. PAGE DE CONNEXION (VERSION "DROITE" RESTAURÉE) ---
if not st.session_state.connecte:
    st.markdown("<br><br>", unsafe_allow_html=True)
    # Colonnes 1-1-1 pour un centrage parfait
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        # Alignement vertical : Image -> Titre -> Sous-titre
        st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <img src='https://static.vecteezy.com/system/resources/previews/015/515/874/non_2x/arc-letter-logo-design-on-black-background-arc-creative-initials-letter-logo-concept-arc-letter-design-vector.jpg' width='60'>
                <h2 style='margin-top: 15px; margin-bottom: 5px; color: #1f1f1f;'>ArchiroData</h2>
                <p style='color: #666; font-size: 14px;'>Portail de Connexion Sécurisé</p>
            </div>
            """, unsafe_allow_html=True)
        
        with st.container(border=True):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("Se connecter"):
                if u == ADMIN_USER and p == ADMIN_PASS:
                    st.session_state.connecte, st.session_state.role = True, "admin"
                    st.rerun()
                elif u == STAFF_USER and p == STAFF_PASS:
                    st.session_state.connecte, st.session_state.role = True, "user"
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")
    st.stop()

# --- 2. APPLICATION PRINCIPALE ---

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div class='logo-container'>
            <img src='https://static.vecteezy.com/system/resources/previews/015/515/874/non_2x/arc-letter-logo-design-on-black-background-arc-creative-initials-letter-logo-concept-arc-letter-design-vector.jpg' width='35'>
            <span class='logo-text'>ArchiroData</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.write(f"👤 Connecté : **{st.session_state.role.upper()}**")
    
    menu = ["Tableau de Bord"]
    if st.session_state.role == "admin": 
        menu.append("Administration")
    
    choix = st.radio("Navigation", menu)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Se déconnecter"):
        st.session_state.connecte = False
        st.rerun()

# Page : Tableau de Bord
if choix == "Tableau de Bord":
    st.subheader("📊 Tableau de Bord des Leads")
    st.markdown("---")
    
    df = charger_donnees()
    
    if not df.empty:
        # Métriques
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Leads Totaux", len(df))
        with c2: 
            if 'Secteur' in df.columns: st.metric("Secteurs Activité", df['Secteur'].nunique())
            else: st.metric("Secteurs", "N/A")
        with c3:
            if 'Mobile' in df.columns:
                nb_mobiles = len(df[df['Mobile'].str.contains('06|07', na=False)])
                st.metric("Mobiles Qualifiés", nb_mobiles)
            else: st.metric("Mobiles", "N/A")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Filtres
        search = st.text_input("🔍 Rechercher un prospect (Nom, Ville, Téléphone...)")
        
        filtered_df = df.copy()
        if search:
            filtered_df = filtered_df[filtered_df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        
        # Tableau
        st.dataframe(filtered_df, use_container_width=True, height=500)
        
        # Bouton Export
        csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Exporter les données (CSV)", csv, "export_archirodata.csv", "text/csv")
        
    else:
        st.info("La base de données est vide ou inaccessible. Veuillez contacter l'administrateur.")

# Page : Administration
elif choix == "Administration":
    st.subheader("⚙️ Administration & Import")
    st.markdown("---")
    
    st.info("ℹ️ Cette interface permet de mettre à jour la base de données centrale.")
    
    uploaded_file = st.file_uploader("Importer le fichier CSV (Scraping)", type="csv")
    
    if uploaded_file:
        try:
            new_df = pd.read_csv(uploaded_file)
            # Nettoyage préventif
            new_df = new_df.loc[:, ~new_df.columns.str.contains('^Unnamed')]
            new_df = new_df.fillna("N/A")
            
            st.write(f"✅ Fichier chargé : **{len(new_df)} lignes** détectées.")
            st.dataframe(new_df.head(3), use_container_width=True)
            
            if st.button("🚀 DÉPLOYER EN PRODUCTION"):
                with st.spinner("Synchronisation avec le Cloud Google en cours..."):
                    client = get_gspread_client()
                    sheet = client.open("Data_Prospection_Energie").sheet1
                    sheet.clear()
                    
                    # Préparation des données pour l'envoi
                    data_list = [new_df.columns.values.tolist()] + new_df.values.tolist()
                    sheet.update('A1', data_list)
                    
                    st.success("Succès ! La base de données a été mise à jour.")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {e}") 