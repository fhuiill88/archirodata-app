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
        except: df_suivi = pd.DataFrame(columns=["Date", "Commercial", "Nom Entreprise", "Ville", "Statut", "Note", "Contact_Nom", "Contact_Email"])
        try:
            fact_vals = ss.worksheet("Donnees_Factures").get_all_values()
            df_factures = pd.DataFrame(fact_vals[1:], columns=fact_vals[0])
        except: df_factures = pd.DataFrame(columns=["Commercial", "Client", "Conso_Hiver", "Conso_Ete", "Montant_Hiver", "Montant_Ete", "Date_Saisie", "Facture_Recue", "Etat_Dossier"])
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
        try: sheet = doc.worksheet("Donnees_Factures")
        except: 
            sheet = doc.add_worksheet(title="Donnees_Factures", rows=1000, cols=10)
            sheet.append_row(["Commercial", "Client", "Conso_Hiver", "Conso_Ete", "Montant_Hiver", "Montant_Ete", "Date_Saisie", "Facture_Recue", "Etat_Dossier"])
        
        facture_recue = "OUI (PDF)" if a_facture else "NON"
        row = [str(commercial), str(client_nom), str(hiv_kwh), str(ete_kwh), str(hiv_eur), str(ete_eur), str(datetime.now()), facture_recue, "En cours"]
        sheet.append_row(row)
        return True, ""
    except Exception as e: return False, f"Erreur Google : {str(e)}"

# --- GESTION DE SESSION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None
if 'active_deal' not in st.session_state: st.session_state.active_deal = None

# ==============================================================================
# 🎨 TEMPLATE VISUEL (Style Pipedrive / SaaS Moderne)
# ==============================================================================
st.markdown("""
    <style>
    /* Nettoyage */
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    
    /* Couleurs de fond (Gris très clair façon SaaS) */
    .stApp { background-color: #f7f9fa !important; color: #1f2937 !important; font-family: 'Inter', sans-serif; }
    
    /* Boutons stylisés */
    .stButton>button { border-radius: 6px; font-weight: 500; border: 1px solid #e5e7eb; background-color: #ffffff; color: #374151; transition: all 0.2s; }
    .stButton>button:hover { border-color: #d1d5db; background-color: #f3f4f6; }
    button[data-testid="baseButton-primary"] { background-color: #2563eb !important; color: white !important; border: none !important; }
    button[data-testid="baseButton-primary"]:hover { background-color: #1d4ed8 !important; }
    
    /* Conteneurs et Cartes (Blanc avec bordure fine) */
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); }
    
    /* Onglets (Tabs) */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; font-weight: 600;}
    .stTabs [aria-selected="true"] { color: #2563eb !important; border-bottom: 3px solid #2563eb !important; }
    
    /* Titres */
    h1, h2, h3 { color: #111827; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 1. PAGE DE CONNEXION (Style Épuré)
# ==============================================================================
if not st.session_state.logged_in:
    st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.container(border=True):
            st.markdown("""
                <div style='text-align: center; padding: 10px;'>
                    <h1 style='color: #2563eb; font-weight: 800; font-size: 2.5rem; margin-bottom: 0;'>ArchiroData</h1>
                    <p style='color: #6b7280; margin-top: -10px; margin-bottom: 25px;'>Espace de travail sécurisé</p>
                </div>
            """, unsafe_allow_html=True)
            u = st.text_input("Identifiant", placeholder="Entrez votre identifiant")
            p = st.text_input("Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Accéder au CRM", use_container_width=True, type="primary"):
                if u in USERS and USERS[u] == p:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: 
                    st.error("Identifiants incorrects.")
    st.stop()

# ==============================================================================
# 2. APPLICATION PRINCIPALE CRM
# ==============================================================================
user = st.session_state.user
df_leads, df_suivi, df_factures = load_all_data()

# Préparation des données
if not df_leads.empty and not df_suivi.empty:
    last_status = df_suivi.drop_duplicates(subset=['Nom Entreprise'], keep='last')[['Nom Entreprise', 'Statut']]
    df_leads = df_leads.merge(last_status, left_on='Nom', right_on='Nom Entreprise', how='left').drop(columns=['Nom Entreprise'])
    df_leads['Statut'] = df_leads['Statut'].fillna('Nouveau')

# --- EN-TÊTE ---
col_logo, col_space, col_user = st.columns([2, 5, 2])
with col_logo:
    st.markdown("<h2 style='margin-top: 0; color: #111827; font-weight: 800;'>ArchiroData</h2>", unsafe_allow_html=True)
with col_user:
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

# ==============================================================================
# 3. GESTION DES VUES (PIPELINE vs ÉDITION)
# ==============================================================================

# VUE 1 : L'utilisateur a cliqué sur un dossier pour le modifier
if st.session_state.active_deal is not None:
    deal_name = st.session_state.active_deal
    action_type = st.session_state.action_type # "appel" ou "facture"
    
    if st.button("⬅️ Retour au Pipeline"):
        st.session_state.active_deal = None
        st.rerun()
        
    st.markdown(f"<h2>Gestion du dossier : <span style='color:#2563eb;'>{deal_name}</span></h2>", unsafe_allow_html=True)
    
    # Récupérer les infos de la base
    try: deal_info = df_leads[df_leads['Nom'] == deal_name].iloc[0]
    except: deal_info = {"Ville": "Inconnue", "Téléphone": "Inconnu"}

    with st.container(border=True):
        col_form, col_info = st.columns([2, 1])
        
        with col_info:
            st.markdown("#### Détails Prospect")
            st.write(f"**Ville:** {deal_info.get('Ville', 'N/A')}")
            st.write(f"**Tél:** {deal_info.get('Téléphone', 'N/A')}")
            st.write(f"**Mobile:** {deal_info.get('Mobile', 'N/A')}")

        with col_form:
            if action_type == "appel":
                st.markdown("#### Mise à jour du Statut")
                with st.form("edit_call"):
                    new_statut = st.radio("Résultat", ["En attente", "Positif", "Negatif", "Pas de reponse", "A rappeler"], horizontal=True)
                    note = st.text_input("Nouvelle note / Compte-rendu")
                    if st.form_submit_button("Enregistrer", type="primary"):
                        success, err = save_interaction(user, deal_name, deal_info.get('Ville', ''), new_statut, note, "", "")
                        if success:
                            st.session_state.active_deal = None
                            st.cache_data.clear()
                            st.rerun()
                        else: st.error(err)
            
            elif action_type == "facture":
                st.markdown("#### Saisie des Factures")
                with st.form("edit_facture"):
                    c1, c2 = st.columns(2)
                    with c1: 
                        hiv_kwh = st.text_input("Hiver (kWh)")
                        hiv_eur = st.text_input("Hiver (€)")
                    with c2: 
                        ete_kwh = st.text_input("Eté (kWh)")
                        ete_eur = st.text_input("Eté (€)")
                    uploaded_file = st.file_uploader("Facture PDF (Optionnel)", type=['pdf', 'jpg'])
                    
                    if st.form_submit_button("Transmettre le dossier", type="primary"):
                        success, err = save_facture(user, deal_name, hiv_kwh, ete_kwh, hiv_eur, ete_eur, uploaded_file is not None)
                        if success:
                            st.session_state.active_deal = None
                            st.cache_data.clear()
                            st.rerun()
                        else: st.error(f"Détail erreur : {err}")

# VUE 2 : Le Tableau de bord principal (Onglets)
else:
    tab_pipeline, tab_prospect = st.tabs(["📊 PIPELINE DES DOSSIERS", "🔍 CHERCHER UN NOUVEAU PROSPECT"])
    
    # ---------------------------------------------------------
    # ONGLET 1 : LE PIPELINE (Façon Kanban)
    # ---------------------------------------------------------
    with tab_pipeline:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        
        # Filtrer les données pour chaque colonne
        if not df_suivi.empty:
            # Col 1: A Relancer
            a_relancer = df_suivi[df_suivi['Statut'].isin(["Pas de reponse", "A rappeler", "En attente", "📵 Pas de réponse", "⏰ A rappeler", "⏳ En attente"])]
            a_relancer = a_relancer.drop_duplicates(subset=['Nom Entreprise'], keep='last')
            
            # Col 2: Positifs (sans factures)
            positifs = df_suivi[df_suivi['Statut'].str.contains("Positif", case=False, na=False)]
            if not df_factures.empty:
                deja_fait = df_factures['Client'].unique().tolist()
                positifs = positifs[~positifs['Nom Entreprise'].isin(deja_fait)]
            positifs = positifs.drop_duplicates(subset=['Nom Entreprise'], keep='last')
        else:
            a_relancer = pd.DataFrame()
            positifs = pd.DataFrame()
            
        # Col 3 et 4: Factures
        en_cours = df_factures[df_factures['Etat_Dossier'] == "En cours"] if not df_factures.empty else pd.DataFrame()
        valides = df_factures[df_factures['Etat_Dossier'] == "Validé"] if not df_factures.empty else pd.DataFrame()

        # DESSIN DES COLONNES
        with col1:
            st.markdown("<div style='background-color:#fef3c7; color:#92400e; padding:8px; border-radius:6px; font-weight:bold; margin-bottom:10px; text-align:center;'>📞 À Relancer (" + str(len(a_relancer)) + ")</div>", unsafe_allow_html=True)
            for idx, row in a_relancer.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Nom Entreprise']}**")
                    st.caption(f"{row['Ville']} | {row['Statut']}")
                    if st.button("Modifier", key=f"btn_rel_{idx}", use_container_width=True):
                        st.session_state.active_deal = row['Nom Entreprise']
                        st.session_state.action_type = "appel"
                        st.rerun()

        with col2:
            st.markdown("<div style='background-color:#dbeafe; color:#1e40af; padding:8px; border-radius:6px; font-weight:bold; margin-bottom:10px; text-align:center;'>📝 Dossier à Remplir (" + str(len(positifs)) + ")</div>", unsafe_allow_html=True)
            for idx, row in positifs.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Nom Entreprise']}**")
                    st.caption(f"Note: {row['Note']}")
                    if st.button("Saisir factures", key=f"btn_pos_{idx}", type="primary", use_container_width=True):
                        st.session_state.active_deal = row['Nom Entreprise']
                        st.session_state.action_type = "facture"
                        st.rerun()

        with col3:
            st.markdown("<div style='background-color:#f3f4f6; color:#374151; padding:8px; border-radius:6px; font-weight:bold; margin-bottom:10px; text-align:center;'>⏳ En Analyse (" + str(len(en_cours)) + ")</div>", unsafe_allow_html=True)
            for idx, row in en_cours.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Client']}**")
                    st.caption(f"Saisi le : {row['Date_Saisie'][:10]}")
                    st.info("Traitement admin", icon="🔒")

        with col4:
            st.markdown("<div style='background-color:#d1fae5; color:#065f46; padding:8px; border-radius:6px; font-weight:bold; margin-bottom:10px; text-align:center;'>🏆 Validé (" + str(len(valides)) + ")</div>", unsafe_allow_html=True)
            for idx, row in valides.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Client']}**")
                    st.caption(f"Factures: {row['Facture_Recue']}")
                    st.success("Terminé", icon="✅")

    # ---------------------------------------------------------
    # ONGLET 2 : BASE DE PROSPECTION
    # ---------------------------------------------------------
    with tab_prospect:
        st.markdown("<br>", unsafe_allow_html=True)
        if not df_leads.empty:
            c1, c2 = st.columns(2)
            filtre_ville = c1.selectbox("Filtrer par Ville", ["Toutes"] + sorted(df_leads['Ville'].unique()))
            filtre_secteur = c2.selectbox("Filtrer par Secteur", ["Tous"] + sorted(df_leads['Secteur'].unique()))
            
            df_show = df_leads.copy()
            if filtre_ville != "Toutes": df_show = df_show[df_show['Ville'] == filtre_ville]
            if filtre_secteur != "Tous": df_show = df_show[df_show['Secteur'] == filtre_secteur]
            
            st.markdown(f"**{len(df_show)} prospects trouvés.** Cliquez sur une ligne pour lancer l'appel.")
            event = st.dataframe(df_show, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", height=350)
            
            if len(event.selection.rows) > 0:
                lead = df_show.iloc[event.selection.rows[0]]
                st.session_state.active_deal = lead['Nom']
                st.session_state.action_type = "appel"
                st.rerun()
