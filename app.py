import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="ArchiroData CRM", layout="wide", initial_sidebar_state="collapsed")

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
            sheet.append_row(["Commercial", "Client", "Conso_Hiver", "Conso_Ete", "Montant_Hiver", "Montant_Ete", "Date_Saisie", "Facture_Recue", "Etat_Dossier"])
        
        facture_recue = "OUI (PDF)" if a_facture else "NON"
        row = [str(commercial), str(client_nom), str(hiv_kwh), str(ete_kwh), str(hiv_eur), str(ete_eur), str(datetime.now()), facture_recue, "En cours"]
        sheet.append_row(row)
        return True, ""
    except Exception as e: 
        return False, f"Erreur Google : {str(e)}"

# --- GESTION DE SESSION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None

# ==============================================================================
# PAGE DE CONNEXION (Restée Premium)
# ==============================================================================
if not st.session_state.logged_in:
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
        [data-testid="collapsedControl"] { display: none; }
        section[data-testid="stSidebar"] { display: none; }
        .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
        .brand-title {
            font-size: 3rem; font-weight: 800; text-align: center;
            background: linear-gradient(135deg, #0f172a 0%, #2563eb 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
        }
        .brand-subtitle { text-align: center; color: #64748b; font-size: 1.1rem; margin-top: -10px; margin-bottom: 30px; }
        .stTextInput input { border-radius: 8px !important; border: 1px solid #e2e8f0 !important; padding: 12px 16px !important; }
        .stButton>button { background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important; border-radius: 8px !important; border: none !important; padding: 12px !important; font-weight: 600 !important; }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h1 class='brand-title'>ArchiroData</h1>", unsafe_allow_html=True)
            st.markdown("<p class='brand-subtitle'>Plateforme de gestion commerciale</p>", unsafe_allow_html=True)
            u = st.text_input("Identifiant", placeholder="Entrez votre identifiant")
            p = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if u in USERS and USERS[u] == p:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: 
                    st.error("Identifiants incorrects.")
    st.stop()

# ==============================================================================
# APPLICATION PRINCIPALE (NOUVEAU DESIGN SANS SIDEBAR)
# ==============================================================================
st.markdown("""
    <style>
    /* Masquer la sidebar et les éléments par défaut */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Couleurs et polices générales */
    .stApp { background-color: #f8fafc !important; color: #0f172a !important; font-family: 'Inter', sans-serif; }
    h1, h2, h3 { color: #0f172a; font-weight: 600; }
    
    /* Style du menu de navigation du haut (Radio buttons stylisés) */
    div.row-widget.stRadio > div { flex-direction: row; justify-content: center; background-color: #ffffff; padding: 10px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; margin-bottom: 20px;}
    div.row-widget.stRadio > div > label { background-color: transparent; padding: 10px 20px; border-radius: 6px; margin: 0 5px; cursor: pointer; transition: all 0.2s;}
    
    /* Style des conteneurs (Cartes flottantes) */
    [data-testid="stVerticalBlockBorderWrapper"] { box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; padding: 10px;}
    
    /* Boutons standards */
    .stButton>button { background-color: #2563eb; color: white; border-radius: 6px; font-weight: 500; border: none;}
    .stButton>button:hover { background-color: #1d4ed8; }
    
    /* Cartes de KPI (Indicateurs) */
    div[data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    </style>
    """, unsafe_allow_html=True)

user = st.session_state.user
df_leads, df_suivi, df_factures = load_all_data()

# Traitement des données
if not df_leads.empty and not df_suivi.empty:
    last_status = df_suivi.drop_duplicates(subset=['Nom Entreprise'], keep='last')[['Nom Entreprise', 'Statut']]
    df_leads = df_leads.merge(last_status, left_on='Nom', right_on='Nom Entreprise', how='left').drop(columns=['Nom Entreprise'])
    df_leads['Statut'] = df_leads['Statut'].fillna('Nouveau')

# --- EN-TÊTE / TOP BAR ---
col_logo, col_user = st.columns([4, 1])
with col_logo:
    st.markdown("<h2 style='margin-top: 0; color: #1e293b; font-weight: 800;'>ArchiroData</h2>", unsafe_allow_html=True)
with col_user:
    st.markdown(f"<div style='text-align: right; margin-top: 10px; font-weight: 500;'>Utilisateur : {user.upper()}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Actualiser", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with c2:
        if st.button("Quitter", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

st.markdown("---")

# --- KPI / TABLEAU DE BORD RAPIDE ---
# Calculs rapides pour le dashboard
total_leads = len(df_leads) if not df_leads.empty else 0
dossiers_gagnes = len(df_suivi[df_suivi['Statut'].str.contains("Positif", case=False, na=False)]) if not df_suivi.empty else 0
dossiers_en_cours = len(df_factures[df_factures['Etat_Dossier'] == "En cours"]) if not df_factures.empty else 0

m1, m2, m3 = st.columns(3)
m1.metric("Base de prospection", f"{total_leads} cibles")
m2.metric("Dossiers positifs (Historique)", dossiers_gagnes)
m3.metric("Dossiers en attente de validation", dossiers_en_cours)

st.markdown("<br>", unsafe_allow_html=True)

# --- NAVIGATION PRINCIPALE (Le nouveau menu du haut) ---
menu = st.radio("Navigation", [
    "Prospection globale", 
    "Rappels urgents", 
    "Dossiers a remplir", 
    "Suivi des dossiers"
], horizontal=True, label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# CONTENU DES ONGLETS
# ------------------------------------------------------------------------------

if menu == "Prospection globale":
    st.subheader("Base de données de prospection")
    if not df_leads.empty:
        c1, c2 = st.columns(2)
        filtre_ville = c1.selectbox("Filtrer par Ville", ["Toutes"] + sorted(df_leads['Ville'].unique()))
        filtre_secteur = c2.selectbox("Filtrer par Secteur", ["Tous"] + sorted(df_leads['Secteur'].unique()))
        
        df_show = df_leads.copy()
        if filtre_ville != "Toutes": df_show = df_show[df_show['Ville'] == filtre_ville]
        if filtre_secteur != "Tous": df_show = df_show[df_show['Secteur'] == filtre_secteur]
        
        event = st.dataframe(df_show, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=350)
        
        if len(event.selection.rows) > 0:
            lead = df_show.iloc[event.selection.rows[0]]
            st.markdown("---")
            st.markdown(f"### Fiche Prospect : {lead['Nom']}")
            
            with st.container(border=True):
                col_g, col_d = st.columns([1, 2])
                with col_g:
                    st.markdown("**Informations de contact**")
                    st.write(f"Adresse : {lead['Adresse']}")
                    st.write(f"Standard : {lead['Téléphone']}")
                    st.write(f"Mobile : {lead['Mobile']}")
                    st.write(f"Statut actuel : {lead.get('Statut', 'Nouveau')}")
                with col_d:
                    with st.form("call_form"):
                        st.markdown("**Saisie du rapport d'appel**")
                        # Valeurs nettoyées (sans emojis) pour la nouvelle base
                        new_statut = st.radio("Résultat de l'appel", ["En attente", "Positif", "Negatif", "Pas de reponse", "A rappeler"], horizontal=True)
                        note = st.text_area("Compte-rendu")
                        contact = st.text_input("Nom du décisionnaire")
                        email = st.text_input("Email du décisionnaire")
                        if st.form_submit_button("Enregistrer le rapport", type="primary"):
                            success, err_msg = save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, contact, email)
                            if success:
                                st.success("Rapport enregistré avec succès.")
                                st.cache_data.clear()
                            else: st.error(f"Erreur technique : {err_msg}")

elif menu == "Rappels urgents":
    st.subheader("Liste des rappels programmés")
    if not df_leads.empty:
        # On garde les anciens statuts avec emojis au cas où, pour ne pas perdre les vieilles données
        df_rappel = df_leads[df_leads['Statut'].isin(["Pas de reponse", "A rappeler", "En attente", "📵 Pas de réponse", "⏰ A rappeler", "⏳ En attente"])]
        if df_rappel.empty: 
            st.info("Aucun rappel en attente.")
        else:
            event = st.dataframe(df_rappel, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if len(event.selection.rows) > 0:
                lead = df_rappel.iloc[event.selection.rows[0]]
                st.markdown("---")
                st.markdown(f"### Mise à jour : {lead['Nom']}")
                with st.container(border=True):
                    with st.form("rappel_form"):
                        new_statut = st.radio("Nouveau statut", ["Positif", "Negatif", "Pas de reponse", "A rappeler"], horizontal=True)
                        note = st.text_input("Nouvelle note additionnelle")
                        if st.form_submit_button("Actualiser le dossier", type="primary"):
                            success, err_msg = save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, "", "")
                            if success:
                                st.success("Dossier actualisé.")
                                st.cache_data.clear()
                            else: st.error(f"Erreur : {err_msg}")

elif menu == "Dossiers a remplir":
    st.subheader("Finalisation des dossiers clients")
    if not df_suivi.empty:
        positifs = df_suivi[df_suivi['Statut'].str.contains("Positif", case=False, na=False)]
        if not df_factures.empty:
            deja_fait = df_factures['Client'].unique().tolist()
            a_faire = positifs[~positifs['Nom Entreprise'].isin(deja_fait)]
        else: a_faire = positifs
        
        a_faire = a_faire.drop_duplicates(subset=['Nom Entreprise'])
        
        if a_faire.empty: 
            st.info("Aucun prospect en attente de facturation.")
        else:
            event = st.dataframe(a_faire[['Date', 'Nom Entreprise', 'Ville', 'Note']], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
            if len(event.selection.rows) > 0:
                client = a_faire.iloc[event.selection.rows[0]]
                nom_client = client['Nom Entreprise']
                st.markdown("---")
                st.markdown(f"### Saisie des données : {nom_client}")
                
                with st.container(border=True):
                    with st.form("dossier_form"):
                        c1, c2 = st.columns(2)
                        with c1: 
                            st.markdown("**Période Hivernale**")
                            hiv_kwh = st.text_input("Consommation (kWh)")
                            hiv_eur = st.text_input("Montant HT/TTC (€)")
                        with c2: 
                            st.markdown("**Période Estivale**")
                            ete_kwh = st.text_input("Consommation (kWh) ")
                            ete_eur = st.text_input("Montant HT/TTC (€) ")
                        
                        st.markdown("**Pièces justificatives**")
                        uploaded_file = st.file_uploader("Importer la facture (PDF, JPG)", type=['pdf', 'jpg', 'png'])
                        
                        if st.form_submit_button("Transmettre le dossier", type="primary"):
                            try:
                                success, err_msg = save_facture(user, nom_client, hiv_kwh, ete_kwh, hiv_eur, ete_eur, uploaded_file is not None)
                                if success:
                                    st.success("Le dossier a été transmis au service d'administration.")
                                    st.cache_data.clear()
                                else: 
                                    st.error(f"Erreur lors de la transmission : {err_msg}")
                            except Exception as e:
                                st.error(f"Erreur système : {e}")

elif menu == "Suivi des dossiers":
    st.subheader("Suivi administratif")
    if not df_factures.empty:
        tab1, tab2 = st.tabs(["Dossiers en cours de traitement", "Dossiers validés"])
        with tab1:
            encours = df_factures[df_factures['Etat_Dossier'] == "En cours"]
            if encours.empty: 
                st.info("Aucun dossier en cours d'analyse.")
            else: 
                st.dataframe(encours, use_container_width=True)
        with tab2:
            valides = df_factures[df_factures['Etat_Dossier'] == "Validé"]
            if valides.empty: 
                st.info("Aucun dossier validé pour le moment.")
            else: 
                st.dataframe(valides, use_container_width=True)
    else: 
        st.write("L'historique des dossiers est vide.")
