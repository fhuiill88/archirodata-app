import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import urllib.parse

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="ArchiroData CRM", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")

# --- IDENTIFIANTS ---
USERS = {
    "admin": "archiro2026",
    "staff1": "staff1",
    "staff2": "staff2"
}

# --- FONCTIONS SYSTÈME (Inchangées) ---
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_all_data():
    try:
        client = get_client()
        ss = client.open("Data_Prospection_Energie")
        df_leads = pd.DataFrame(ss.sheet1.get_all_values()[1:], columns=ss.sheet1.get_all_values()[0])
        try: 
            suivi_vals = ss.worksheet("Suivi_Commerciaux").get_all_values()
            df_suivi = pd.DataFrame(suivi_vals[1:], columns=suivi_vals[0])
        except: df_suivi = pd.DataFrame(columns=["Nom Entreprise", "Statut"])
        try:
            fact_vals = ss.worksheet("Donnees_Factures").get_all_values()
            df_factures = pd.DataFrame(fact_vals[1:], columns=fact_vals[0])
        except: df_factures = pd.DataFrame(columns=["Client", "Etat_Dossier"])
        return df_leads, df_suivi, df_factures
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def save_interaction(commercial, entreprise, ville, statut, note, contact_nom, contact_email):
    try:
        client = get_client()
        try: sheet = client.open("Data_Prospection_Energie").worksheet("Suivi_Commerciaux")
        except: sheet = client.open("Data_Prospection_Energie").add_worksheet("Suivi_Commerciaux", 1000, 10)
        row = [str(datetime.now()), commercial, entreprise, ville, statut, note, contact_nom, contact_email]
        sheet.append_row(row)
        return True
    except: return False

def save_facture(commercial, client_nom, hiv_kwh, ete_kwh, hiv_eur, ete_eur, a_facture):
    try:
        client = get_client()
        try: sheet = client.open("Data_Prospection_Energie").worksheet("Donnees_Factures")
        except: sheet = client.open("Data_Prospection_Energie").add_worksheet("Donnees_Factures", 1000, 10)
        facture_recue = "OUI (PDF)" if a_facture else "NON"
        row = [commercial, client_nom, hiv_kwh, ete_kwh, hiv_eur, ete_eur, str(datetime.now()), facture_recue, "En cours"]
        sheet.append_row(row)
        return True
    except: return False

# --- GESTION DE SESSION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None

# ==============================================================================
# 🌟 PAGE DE CONNEXION (DESIGN PREMIUM)
# ==============================================================================
if not st.session_state.logged_in:
    # CSS Spécifique à la page de connexion
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

        /* Masquer l'interface par défaut de Streamlit */
        [data-testid="collapsedControl"] { display: none; }
        header { display: none !important; }
        footer { display: none !important; }
        
        /* Fond de l'application */
        .stApp {
            background-color: #f4f7f6 !important;
            font-family: 'Poppins', sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Titre ArchiroData avec dégradé */
        .brand-title {
            font-size: 3.2rem;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(135deg, #0A192F 0%, #0052D4 50%, #4364F7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
            padding-bottom: 0px;
            letter-spacing: -1px;
        }
        
        .brand-subtitle {
            text-align: center;
            color: #64748b;
            font-weight: 400;
            font-size: 1.1rem;
            margin-top: -10px;
            margin-bottom: 35px;
            letter-spacing: 0.5px;
        }

        /* Personnalisation des champs de texte */
        .stTextInput input {
            border-radius: 8px !important;
            border: 1px solid #e2e8f0 !important;
            padding: 12px 16px !important;
            font-size: 1rem !important;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.02) !important;
        }
        .stTextInput input:focus {
            border-color: #0052D4 !important;
            box-shadow: 0 0 0 2px rgba(0, 82, 212, 0.2) !important;
        }

        /* Bouton de connexion Premium */
        .stButton>button {
            background: linear-gradient(135deg, #0052D4, #4364F7) !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 14px !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            width: 100% !important;
            transition: all 0.3s ease !important;
            margin-top: 15px !important;
            box-shadow: 0 4px 14px rgba(0, 82, 212, 0.3) !important;
        }
        .stButton>button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 82, 212, 0.4) !important;
        }
        
        /* Cacher les labels "Identifiant" au profit des placeholders */
        .stTextInput label { display: none; }
        </style>
        """, unsafe_allow_html=True)

    # Espacement pour centrer verticalement
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    # Structure de la carte centrée
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        # La "Carte" blanche
        with st.container(border=True):
            st.markdown("<div style='padding: 20px;'>", unsafe_allow_html=True)
            
            # En-tête
            st.markdown("""
                <div style="text-align: center; margin-bottom: 10px;">
                    <img src="https://cdn-icons-png.flaticon.com/512/2991/2991148.png" width="65" style="margin-bottom: 10px;">
                </div>
                <h1 class='brand-title'>ArchiroData</h1>
                <p class='brand-subtitle'>Espace de travail sécurisé</p>
                """, unsafe_allow_html=True)
            
            # Formulaire
            u = st.text_input("ID", placeholder="Identifiant commercial")
            p = st.text_input("PASS", type="password", placeholder="Mot de passe")
            
            if st.button("Accéder au CRM"):
                if u in USERS and USERS[u] == p:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: 
                    st.error("Identifiants incorrects. Veuillez réessayer.")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
    st.stop() # Empêche de charger le reste du code si pas connecté

# ==============================================================================
# 🌟 APPLICATION PRINCIPALE (DESIGN CRM)
# ==============================================================================
# CSS pour l'intérieur de l'application (différent de la page de login)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    .stApp { background-color: #ffffff !important; color: #1f1f1f !important; font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #dee2e6; }
    [data-testid="stSidebar"] * { color: #1f1f1f !important; }
    [data-testid="stDataFrame"] { border: 1px solid #e0e0e0; border-radius: 5px; }
    h1, h2, h3 { color: #0A192F; font-weight: 600; }
    .stButton>button { background-color: #0052D4; color: white; border-radius: 6px; font-weight: 600; width: 100%; border: none;}
    </style>
    """, unsafe_allow_html=True)

user = st.session_state.user
df_leads, df_suivi, df_factures = load_all_data()

if not df_leads.empty and not df_suivi.empty:
    last_status = df_suivi.drop_duplicates(subset=['Nom Entreprise'], keep='last')[['Nom Entreprise', 'Statut']]
    df_leads = df_leads.merge(last_status, left_on='Nom', right_on='Nom Entreprise', how='left').drop(columns=['Nom Entreprise'])
    df_leads['Statut'] = df_leads['Statut'].fillna('Nouveau')

# Sidebar
with st.sidebar:
    st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
            <img src="https://cdn-icons-png.flaticon.com/512/2991/2991148.png" width="30">
            <span style="font-size: 20px; font-weight: 800; color: #0A192F;">ArchiroData</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"👤 **{user.upper()}**")
    st.write("---")
    menu = st.radio("Pipeline de Vente", [
        "1️⃣ Prospection (Tout)", 
        "2️⃣ À Rappeler (Urgent)", 
        "3️⃣ Dossiers à Remplir", 
        "4️⃣ Dossiers En Cours / Validés"
    ])
    
    st.write("---")
    if st.button("Rafraîchir"):
        st.cache_data.clear()
        st.rerun()
    if st.button("Déconnexion"):
        st.session_state.logged_in = False
        st.rerun()

# ------------------------------------------------------------------------------
# SUITE DU CODE CRM (Le contenu des 4 onglets reste exactement le même qu'avant)
# ------------------------------------------------------------------------------

if menu == "1️⃣ Prospection (Tout)":
    st.subheader("📞 Liste Globale de Prospection")
    st.caption("Cliquez sur une ligne pour ouvrir le rapport d'appel.")
    if not df_leads.empty:
        c1, c2 = st.columns(2)
        filtre_ville = c1.selectbox("Filtrer par Ville", ["Toutes"] + sorted(df_leads['Ville'].unique()))
        filtre_secteur = c2.selectbox("Filtrer par Secteur", ["Tous"] + sorted(df_leads['Secteur'].unique()))
        
        df_show = df_leads.copy()
        if filtre_ville != "Toutes": df_show = df_show[df_show['Ville'] == filtre_ville]
        if filtre_secteur != "Tous": df_show = df_show[df_show['Secteur'] == filtre_secteur]
        
        event = st.dataframe(df_show, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=400)
        
        if len(event.selection.rows) > 0:
            idx = event.selection.rows[0]
            lead = df_show.iloc[idx]
            st.markdown("---")
            st.markdown(f"### 📞 Action : {lead['Nom']}")
            col_g, col_d = st.columns([1, 2])
            with col_g:
                st.info(f"📍 {lead['Adresse']}\n\n📞 {lead['Téléphone']} / 📱 {lead['Mobile']}\n\n**Statut:** {lead.get('Statut', 'Nouveau')}")
            with col_d:
                with st.form("call_form"):
                    new_statut = st.radio("Résultat", ["⏳ En attente", "✅ Positif (Dossier à faire)", "❌ Négatif", "📵 Pas de réponse", "⏰ A rappeler"], horizontal=True)
                    note = st.text_area("Notes")
                    contact = st.text_input("Nom Contact")
                    email = st.text_input("Email Contact")
                    if st.form_submit_button("💾 Enregistrer"):
                        if save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, contact, email):
                            st.success("Enregistré !")
                            st.cache_data.clear()
                        else: st.error("Erreur")

elif menu == "2️⃣ À Rappeler (Urgent)":
    st.subheader("⏰ Liste de Rappel")
    if not df_leads.empty:
        df_rappel = df_leads[df_leads['Statut'].isin(["📵 Pas de réponse", "⏰ A rappeler", "⏳ En attente"])]
        if df_rappel.empty: st.success("Rien à rappeler !")
        else:
            event = st.dataframe(df_rappel, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if len(event.selection.rows) > 0:
                lead = df_rappel.iloc[event.selection.rows[0]]
                st.markdown("---")
                st.markdown(f"### 🔁 Rappel : {lead['Nom']}")
                with st.form("rappel_form"):
                    new_statut = st.radio("Résultat", ["✅ Positif (Dossier à faire)", "❌ Négatif", "📵 Toujours pas de réponse"], horizontal=True)
                    note = st.text_input("Note")
                    if st.form_submit_button("Mettre à jour"):
                        save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, "", "")
                        st.success("Mis à jour !")
                        st.cache_data.clear()

elif menu == "3️⃣ Dossiers à Remplir":
    st.subheader("📝 Création de Dossiers")
    if not df_suivi.empty:
        positifs = df_suivi[df_suivi['Statut'].str.contains("Positif", case=False, na=False)]
        if not df_factures.empty:
            deja_fait = df_factures['Client'].unique().tolist()
            a_faire = positifs[~positifs['Nom Entreprise'].isin(deja_fait)]
        else: a_faire = positifs
        
        a_faire = a_faire.drop_duplicates(subset=['Nom Entreprise'])
        
        if a_faire.empty: st.info("Aucun prospect en attente.")
        else:
            event = st.dataframe(a_faire[['Date', 'Nom Entreprise', 'Ville', 'Note']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if len(event.selection.rows) > 0:
                client = a_faire.iloc[event.selection.rows[0]]
                nom_client = client['Nom Entreprise']
                st.markdown("---")
                st.markdown(f"### ⚡ Dossier : {nom_client}")
                with st.form("dossier_form"):
                    c1, c2 = st.columns(2)
                    with c1: hiv_kwh = st.text_input("Hiver kWh"); hiv_eur = st.text_input("Hiver €")
                    with c2: ete_kwh = st.text_input("Eté kWh"); ete_eur = st.text_input("Eté €")
                    uploaded_file = st.file_uploader("Facture PDF", type=['pdf', 'jpg', 'png'])
                    if st.form_submit_button("✅ Valider"):
                        if save_facture(user, nom_client, hiv_kwh, ete_kwh, hiv_eur, ete_eur, uploaded_file is not None):
                            st.success("Dossier envoyé !")
                            st.cache_data.clear()
                        else: st.error("Erreur")

elif menu == "4️⃣ Dossiers En Cours / Validés":
    st.subheader("🚀 Suivi des Dossiers")
    if not df_factures.empty:
        tab1, tab2 = st.tabs(["⏳ En Cours", "✅ Validés"])
        with tab1:
            encours = df_factures[df_factures['Etat_Dossier'] == "En cours"]
            if encours.empty: st.info("Rien en attente.")
            else: st.dataframe(encours, use_container_width=True)
        with tab2:
            valides = df_factures[df_factures['Etat_Dossier'] == "Validé"]
            if valides.empty: st.info("Aucun dossier validé.")
            else: st.dataframe(valides, use_container_width=True)
    else: st.write("Aucun dossier.")
