import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURATION INITIALE ---
st.set_page_config(page_title="ArchiroData Enterprise", layout="wide", initial_sidebar_state="collapsed")

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
if 'current_app' not in st.session_state: st.session_state.current_app = "hub"

# ==============================================================================
# 🎨 TEMPLATE VISUEL (GRIS/BLANC + RAYURES)
# ==============================================================================
st.markdown("""
    <style>
    /* Nettoyage de l'interface par défaut */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    
    /* 1. FOND GLOBAL : Mélange gris/blanc avec rayures diagonales élégantes */
    .stApp { 
        background-color: #f1f5f9 !important; 
        background-image: repeating-linear-gradient(
            45deg,
            #f8fafc,
            #f8fafc 20px,
            #f1f5f9 20px,
            #f1f5f9 40px
        ) !important;
        color: #1e293b !important; 
        font-family: 'Inter', sans-serif; 
    }

    /* 2. CARTES ET CONTENEURS : Blanc pur pour faire ressortir l'information */
    [data-testid="stVerticalBlockBorderWrapper"], 
    div[data-testid="stMetric"], 
    div[data-testid="stForm"] { 
        background-color: #ffffff !important; 
        border: 1px solid #cbd5e1 !important; 
        border-radius: 12px !important; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03) !important; 
        padding: 15px;
    }

    /* 3. TYPOGRAPHIE ET TITRES */
    h1, h2, h3, p { color: #0f172a; }
    
    .brand-title {
        font-size: 3rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #0f172a 0%, #3b82f6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0px;
    }
    .brand-subtitle { text-align: center; color: #64748b; font-size: 1.1rem; margin-top: -10px; margin-bottom: 30px; }

    /* 4. BOUTONS : Style moderne */
    .stButton>button { 
        background-color: #334155 !important; 
        color: white !important; 
        border-radius: 8px !important; 
        font-weight: 600 !important; 
        border: none !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover { background-color: #0f172a !important; transform: translateY(-1px); }
    
    /* Boutons Principaux (Bleus) */
    button[data-testid="baseButton-primary"] { background-color: #2563eb !important; }
    button[data-testid="baseButton-primary"]:hover { background-color: #1d4ed8 !important; }

    /* 5. CHAMPS DE SAISIE : Fond très légèrement gris pour se détacher du blanc */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { 
        border-radius: 8px !important; 
        border: 1px solid #cbd5e1 !important; 
        background-color: #f8fafc !important; 
        padding: 10px !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 1. PAGE DE CONNEXION
# ==============================================================================
if not st.session_state.logged_in:
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        with st.container(border=True):
            st.markdown("<h1 class='brand-title'>ArchiroData</h1>", unsafe_allow_html=True)
            st.markdown("<p class='brand-subtitle'>Plateforme de gestion d'entreprise</p>", unsafe_allow_html=True)
            u = st.text_input("Identifiant", placeholder="Entrez votre identifiant")
            p = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if u in USERS and USERS[u] == p:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.session_state.current_app = "hub"
                    st.rerun()
                else: 
                    st.error("Identifiants incorrects.")
    st.stop()

# ==============================================================================
# 2. LE PORTAIL D'APPLICATIONS (HUB)
# ==============================================================================
if st.session_state.logged_in and st.session_state.current_app == "hub":
    st.markdown("<br>", unsafe_allow_html=True)
    col_titre, col_logout = st.columns([4, 1])
    with col_titre:
        st.markdown(f"<h2>Bienvenue, {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748b; font-size: 1.1rem;'>Sélectionnez une application pour commencer votre session.</p>", unsafe_allow_html=True)
    with col_logout:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Se déconnecter", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("---")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("<h3 style='color: #2563eb; margin-bottom: 5px;'>Data Prospection</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: #64748b; font-size: 0.95rem; height: 60px;'>Outil CRM dédié à la gestion des leads énergétiques, suivis d'appels et facturation.</p>", unsafe_allow_html=True)
            if st.button("Ouvrir l'application", use_container_width=True, type="primary"):
                st.session_state.current_app = "crm"
                st.rerun()
    st.stop()

# ==============================================================================
# 3. APPLICATION : DATA PROSPECTION (CRM)
# ==============================================================================
if st.session_state.logged_in and st.session_state.current_app == "crm":
    user = st.session_state.user
    df_leads, df_suivi, df_factures = load_all_data()

    if not df_leads.empty and not df_suivi.empty:
        last_status = df_suivi.drop_duplicates(subset=['Nom Entreprise'], keep='last')[['Nom Entreprise', 'Statut']]
        df_leads = df_leads.merge(last_status, left_on='Nom', right_on='Nom Entreprise', how='left').drop(columns=['Nom Entreprise'])
        df_leads['Statut'] = df_leads['Statut'].fillna('Nouveau')

    # --- EN-TÊTE DU CRM ---
    with st.container(border=True):
        col_logo, col_menu, col_actions = st.columns([1.5, 2, 1])
        with col_logo:
            st.markdown("<h3 style='margin-top: 5px; color: #1e293b; font-weight: 800;'>Data Prospection</h3>", unsafe_allow_html=True)
        with col_menu:
            menu = st.selectbox("Navigation du module :", [
                "Prospection globale", 
                "Rappels urgents", 
                "Dossiers a remplir", 
                "Suivi des dossiers"
            ], label_visibility="collapsed")
        with col_actions:
            c_retour, c_maj = st.columns(2)
            with c_retour:
                if st.button("Accueil", use_container_width=True):
                    st.session_state.current_app = "hub"
                    st.rerun()
            with c_maj:
                if st.button("Actualiser", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()

    # --- KPI / TABLEAU DE BORD RAPIDE ---
    total_leads = len(df_leads) if not df_leads.empty else 0
    dossiers_gagnes = len(df_suivi[df_suivi['Statut'].str.contains("Positif", case=False, na=False)]) if not df_suivi.empty else 0
    dossiers_en_cours = len(df_factures[df_factures['Etat_Dossier'] == "En cours"]) if not df_factures.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric("Base de prospection", f"{total_leads} cibles")
    m2.metric("Dossiers positifs", dossiers_gagnes)
    m3.metric("Dossiers en attente", dossiers_en_cours)

    st.markdown("<br>", unsafe_allow_html=True)

    # ------------------------------------------------------------------------------
    # CONTENU DES VUES
    # ------------------------------------------------------------------------------

    if menu == "Prospection globale":
        if not df_leads.empty:
            with st.container(border=True):
                st.markdown("#### Filtres de recherche")
                c1, c2 = st.columns(2)
                filtre_ville = c1.selectbox("Ville", ["Toutes"] + sorted(df_leads['Ville'].unique()))
                filtre_secteur = c2.selectbox("Secteur", ["Tous"] + sorted(df_leads['Secteur'].unique()))
            
            df_show = df_leads.copy()
            if filtre_ville != "Toutes": df_show = df_show[df_show['Ville'] == filtre_ville]
            if filtre_secteur != "Tous": df_show = df_show[df_show['Secteur'] == filtre_secteur]
            
            st.markdown("#### Liste des entreprises")
            event = st.dataframe(df_show, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=350)
            
            if len(event.selection.rows) > 0:
                lead = df_show.iloc[event.selection.rows[0]]
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
            df_rappel = df_leads[df_leads['Statut'].isin(["Pas de reponse", "A rappeler", "En attente"])]
            if df_rappel.empty: 
                st.info("Aucun rappel en attente.")
            else:
                event = st.dataframe(df_rappel, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
                if len(event.selection.rows) > 0:
                    lead = df_rappel.iloc[event.selection.rows[0]]
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
