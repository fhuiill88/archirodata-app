import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="ArchiroData CRM", layout="wide", page_icon="⚡", initial_sidebar_state="collapsed")

# --- IDENTIFIANTS ---
USERS = {
    "admin": "archiro2026",
    "staff1": "staff1",
    "staff2": "staff2"
}

# --- FONCTIONS SYSTÈME ---
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
        row = [str(datetime.now()), str(commercial), str(entreprise), str(ville), str(statut), str(note), str(contact_nom), str(contact_email)]
        sheet.append_row(row)
        return True, ""
    except Exception as e: return False, str(e)

def save_facture(commercial, client_nom, hiv_kwh, ete_kwh, hiv_eur, ete_eur, a_facture):
    try:
        client = get_client()
        doc = client.open("Data_Prospection_Energie")
        try: 
            sheet = doc.worksheet("Donnees_Factures")
        except: 
            sheet = doc.add_worksheet(title="Donnees_Factures", rows=1000, cols=10)
        
        facture_recue = "OUI (PDF)" if a_facture else "NON"
        # On convertit tout en string (texte) pour éviter que Google Sheets ne bloque l'insertion
        row = [str(commercial), str(client_nom), str(hiv_kwh), str(ete_kwh), str(hiv_eur), str(ete_eur), str(datetime.now()), facture_recue, "En cours"]
        sheet.append_row(row)
        return True, ""
    except Exception as e: 
        return False, str(e)

# --- GESTION DE SESSION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None

# ==============================================================================
# 🌟 PAGE DE CONNEXION
# ==============================================================================
if not st.session_state.logged_in:
    st.markdown("""
        <style>
        /* Nettoyage de l'interface par défaut */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp { background-color: #f4f7f6 !important; }
        
        /* Titre ArchiroData avec dégradé */
        .brand-title {
            font-size: 3rem;
            font-weight: 800;
            text-align: center;
            background: linear-gradient(135deg, #0A192F 0%, #0052D4 50%, #4364F7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }
        .brand-subtitle {
            text-align: center;
            color: #64748b;
            font-size: 1.1rem;
            margin-top: -10px;
            margin-bottom: 30px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h1 class='brand-title'>⚡ ArchiroData</h1>", unsafe_allow_html=True)
            st.markdown("<p class='brand-subtitle'>Espace de travail sécurisé</p>", unsafe_allow_html=True)
            
            u = st.text_input("Identifiant commercial")
            p = st.text_input("Mot de passe", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Utilisation de use_container_width=True et type="primary" pour forcer le design du bouton
            if st.button("Accéder au CRM", use_container_width=True, type="primary"):
                if u in USERS and USERS[u] == p:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: 
                    st.error("Identifiants incorrects.")
    st.stop()

# ==============================================================================
# 🌟 APPLICATION PRINCIPALE (CRM)
# ==============================================================================
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; color: #1f1f1f !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #dee2e6; }
    [data-testid="stSidebar"] * { color: #1f1f1f !important; }
    [data-testid="stDataFrame"] { border: 1px solid #e0e0e0; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

user = st.session_state.user
df_leads, df_suivi, df_factures = load_all_data()

if not df_leads.empty and not df_suivi.empty:
    last_status = df_suivi.drop_duplicates(subset=['Nom Entreprise'], keep='last')[['Nom Entreprise', 'Statut']]
    df_leads = df_leads.merge(last_status, left_on='Nom', right_on='Nom Entreprise', how='left').drop(columns=['Nom Entreprise'])
    df_leads['Statut'] = df_leads['Statut'].fillna('Nouveau')

with st.sidebar:
    st.markdown("### ⚡ ArchiroData")
    st.markdown(f"👤 **{user.upper()}**")
    st.write("---")
    menu = st.radio("Pipeline de Vente", [
        "1️⃣ Prospection (Tout)", 
        "2️⃣ À Rappeler (Urgent)", 
        "3️⃣ Dossiers à Remplir", 
        "4️⃣ Dossiers En Cours / Validés"
    ])
    st.write("---")
    if st.button("Rafraîchir", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("Déconnexion", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ------------------------------------------------------------------------------
# ONGLETS CRM
# ------------------------------------------------------------------------------

if menu == "1️⃣ Prospection (Tout)":
    st.subheader("📞 Liste Globale de Prospection")
    if not df_leads.empty:
        c1, c2 = st.columns(2)
        filtre_ville = c1.selectbox("Filtrer par Ville", ["Toutes"] + sorted(df_leads['Ville'].unique()))
        filtre_secteur = c2.selectbox("Filtrer par Secteur", ["Tous"] + sorted(df_leads['Secteur'].unique()))
        
        df_show = df_leads.copy()
        if filtre_ville != "Toutes": df_show = df_show[df_show['Ville'] == filtre_ville]
        if filtre_secteur != "Tous": df_show = df_show[df_show['Secteur'] == filtre_secteur]
        
        event = st.dataframe(df_show, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=400)
        
        if len(event.selection.rows) > 0:
            lead = df_show.iloc[event.selection.rows[0]]
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
                    if st.form_submit_button("💾 Enregistrer", type="primary"):
                        success, err_msg = save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, contact, email)
                        if success:
                            st.success("Enregistré !")
                            st.cache_data.clear()
                        else: st.error(f"Erreur technique : {err_msg}")

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
                    if st.form_submit_button("Mettre à jour", type="primary"):
                        success, err_msg = save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, "", "")
                        if success:
                            st.success("Mis à jour !")
                            st.cache_data.clear()
                        else: st.error(f"Erreur : {err_msg}")

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
                    
                    if st.form_submit_button("✅ Valider le Dossier", type="primary"):
                        # Capture de la réponse pour afficher la véritable erreur
                        success, err_msg = save_facture(user, nom_client, hiv_kwh, ete_kwh, hiv_eur, ete_eur, uploaded_file is not None)
                        if success:
                            st.success("Dossier envoyé avec succès !")
                            st.cache_data.clear()
                        else: 
                            st.error(f"L'enregistrement a échoué. Cause : {err_msg}")

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
