import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="ArchiroData CRM", layout="wide", page_icon="⚡")

# --- STYLE CSS (Tableaux compacts et lisibles) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; color: #1f1f1f !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #dee2e6; }
    [data-testid="stSidebar"] * { color: #1f1f1f !important; }
    /* Style pour rendre le tableau plus "Excel" */
    [data-testid="stDataFrame"] { border: 1px solid #e0e0e0; border-radius: 5px; }
    h1, h2, h3 { color: #1f1f1f; }
    .stSuccess { background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- IDENTIFIANTS ---
USERS = {
    "admin": "archiro2026",
    "staff1": "staff1",
    "staff2": "staff2"
}

# --- FONCTIONS GOOGLE SHEETS ---
def get_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=60) # Rafraîchissement rapide (1 min) pour voir les changements
def load_all_data():
    try:
        client = get_client()
        ss = client.open("Data_Prospection_Energie")
        
        # 1. Base Leads
        df_leads = pd.DataFrame(ss.sheet1.get_all_values()[1:], columns=ss.sheet1.get_all_values()[0])
        
        # 2. Historique Appels (Suivi)
        try: 
            suivi_vals = ss.worksheet("Suivi_Commerciaux").get_all_values()
            df_suivi = pd.DataFrame(suivi_vals[1:], columns=suivi_vals[0])
        except: df_suivi = pd.DataFrame(columns=["Nom Entreprise", "Statut"])
            
        # 3. Dossiers Factures
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
        try: 
            sheet = client.open("Data_Prospection_Energie").worksheet("Donnees_Factures")
        except: 
            sheet = client.open("Data_Prospection_Energie").add_worksheet("Donnees_Factures", 1000, 10)
        
        facture_recue = "OUI (PDF)" if a_facture else "NON"
        
        # CORRECTION : Utilisation de "hiv_kwh" et non "hiver_kwh"
        row = [commercial, client_nom, hiv_kwh, ete_kwh, hiv_eur, ete_eur, str(datetime.now()), facture_recue, "En cours"]
        sheet.append_row(row)
        return True
    except Exception as e: 
        print(f"Détail de l'erreur : {e}")
        return False

# --- SESSION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user' not in st.session_state: st.session_state.user = None

# --- LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        with st.container(border=True):
            st.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=60)
            st.markdown("<h2 style='text-align: center;'>ArchiroData CRM</h2>", unsafe_allow_html=True)
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.button("Connexion"):
                if u in USERS and USERS[u] == p:
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
                else: st.error("Accès refusé")
    st.stop()

# --- INTERFACE PRINCIPALE ---
user = st.session_state.user
df_leads, df_suivi, df_factures = load_all_data()

# Préparation des données croisées (Merge)
# On ajoute le "Dernier Statut" à la base des leads pour l'affichage
if not df_leads.empty and not df_suivi.empty:
    # On prend le dernier statut connu pour chaque entreprise
    last_status = df_suivi.drop_duplicates(subset=['Nom Entreprise'], keep='last')[['Nom Entreprise', 'Statut']]
    df_leads = df_leads.merge(last_status, left_on='Nom', right_on='Nom Entreprise', how='left').drop(columns=['Nom Entreprise'])
    df_leads['Statut'] = df_leads['Statut'].fillna('Nouveau') # Si pas d'appel, c'est "Nouveau"

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {user.upper()}")
    
    # Menu Pipeline
    st.write("---")
    menu = st.radio("Pipeline de Vente", [
        "1️⃣ Prospection (Tout)", 
        "2️⃣ À Rappeler (Urgent)", 
        "3️⃣ Dossiers à Remplir", 
        "4️⃣ Dossiers En Cours / Validés"
    ])
    
    st.write("---")
    if st.button("Rafraîchir les données"):
        st.cache_data.clear()
        st.rerun()
    if st.button("Déconnexion"):
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# 1️⃣ PROSPECTION (Tableau Global)
# ==============================================================================
if menu == "1️⃣ Prospection (Tout)":
    st.subheader("📞 Liste Globale de Prospection")
    st.caption("Cliquez sur une ligne pour ouvrir le rapport d'appel.")

    if not df_leads.empty:
        # Filtres
        c1, c2 = st.columns(2)
        filtre_ville = c1.selectbox("Filtrer par Ville", ["Toutes"] + sorted(df_leads['Ville'].unique()))
        filtre_secteur = c2.selectbox("Filtrer par Secteur", ["Tous"] + sorted(df_leads['Secteur'].unique()))
        
        # Application filtres
        df_show = df_leads.copy()
        if filtre_ville != "Toutes": df_show = df_show[df_show['Ville'] == filtre_ville]
        if filtre_secteur != "Tous": df_show = df_show[df_show['Secteur'] == filtre_secteur]
        
        # TABLEAU INTERACTIF
        # on_select="rerun" permet de recharger la page quand on clique, selection_mode="single-row" pour une seule ligne
        event = st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            height=400
        )
        
        # SI UNE LIGNE EST SÉLECTIONNÉE
        if len(event.selection.rows) > 0:
            idx = event.selection.rows[0]
            lead = df_show.iloc[idx]
            
            st.markdown("---")
            st.markdown(f"### 📞 Action : {lead['Nom']}")
            
            col_g, col_d = st.columns([1, 2])
            
            with col_g:
                st.info(f"""
                **Détails:**
                📍 {lead['Adresse']}
                📞 {lead['Téléphone']} / 📱 {lead['Mobile']}
                
                **Statut Actuel:** {lead.get('Statut', 'Nouveau')}
                """)
            
            with col_d:
                with st.form("call_form"):
                    st.write("Rapport d'appel :")
                    new_statut = st.radio("Résultat", ["⏳ En attente", "✅ Positif (Dossier à faire)", "❌ Négatif", "📵 Pas de réponse", "⏰ A rappeler"], horizontal=True)
                    note = st.text_area("Notes", placeholder="Détails de l'échange...")
                    contact = st.text_input("Nom Contact")
                    email = st.text_input("Email Contact")
                    
                    if st.form_submit_button("💾 Enregistrer"):
                        if save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, contact, email):
                            st.success("Enregistré ! Le statut sera mis à jour.")
                            st.cache_data.clear() # Force le rechargement pour voir le nouveau statut
                        else:
                            st.error("Erreur technique")

# ==============================================================================
# 2️⃣ À RAPPELER (Filtre intelligent)
# ==============================================================================
elif menu == "2️⃣ À Rappeler (Urgent)":
    st.subheader("⏰ Liste de Rappel")
    st.caption("Prospects marqués comme 'Pas de réponse' ou 'A rappeler'.")
    
    # On filtre les leads qui ont le statut NRP ou A rappeler
    if not df_leads.empty:
        df_rappel = df_leads[df_leads['Statut'].isin(["📵 Pas de réponse", "⏰ A rappeler", "⏳ En attente"])]
        
        if df_rappel.empty:
            st.success("Rien à rappeler pour le moment ! Bon travail.")
        else:
            event = st.dataframe(
                df_rappel,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            if len(event.selection.rows) > 0:
                idx = event.selection.rows[0]
                lead = df_rappel.iloc[idx]
                
                st.markdown("---")
                st.markdown(f"### 🔁 Rappel : {lead['Nom']}")
                with st.form("rappel_form"):
                    new_statut = st.radio("Nouveau Résultat", ["✅ Positif (Dossier à faire)", "❌ Négatif", "📵 Toujours pas de réponse"], horizontal=True)
                    note = st.text_input("Nouvelle note")
                    if st.form_submit_button("Mettre à jour"):
                        save_interaction(user, lead['Nom'], lead['Ville'], new_statut, note, "", "")
                        st.success("Mis à jour !")
                        st.cache_data.clear()

# ==============================================================================
# 3️⃣ DOSSIERS À REMPLIR (Les Positifs)
# ==============================================================================
elif menu == "3️⃣ Dossiers à Remplir":
    st.subheader("📝 Création de Dossiers (Facturation)")
    st.caption("Liste des prospects 'Positifs' qui n'ont pas encore de dossier complet.")
    
    # Logique : On prend les "Positifs" DANS LE SUIVI, et on enlève ceux qui sont DÉJÀ dans FACTURES
    if not df_suivi.empty:
        # 1. Tous les positifs
        positifs = df_suivi[df_suivi['Statut'].str.contains("Positif", case=False, na=False)]
        
        # 2. On enlève ceux qui sont déjà traités (dans df_factures)
        if not df_factures.empty:
            deja_fait = df_factures['Client'].unique().tolist()
            a_faire = positifs[~positifs['Nom Entreprise'].isin(deja_fait)]
        else:
            a_faire = positifs
            
        # On dédoublonne (si appelé 2 fois positif)
        a_faire = a_faire.drop_duplicates(subset=['Nom Entreprise'])
        
        if a_faire.empty:
            st.info("Aucun prospect positif en attente de dossier.")
        else:
            event = st.dataframe(
                a_faire[['Date', 'Nom Entreprise', 'Ville', 'Note']],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            if len(event.selection.rows) > 0:
                idx = event.selection.rows[0]
                client = a_faire.iloc[idx]
                nom_client = client['Nom Entreprise']
                
                st.markdown("---")
                st.markdown(f"### ⚡ Saisie du dossier : {nom_client}")
                
                with st.form("dossier_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        hiv_kwh = st.text_input("Hiver kWh")
                        hiv_eur = st.text_input("Hiver €")
                    with c2:
                        ete_kwh = st.text_input("Eté kWh")
                        ete_eur = st.text_input("Eté €")
                    
                    uploaded_file = st.file_uploader("Facture PDF (Optionnel)", type=['pdf', 'jpg', 'png'])
                    
                    if st.form_submit_button("✅ Valider le Dossier"):
                        has_file = uploaded_file is not None
                        if save_facture(user, nom_client, hiv_kwh, ete_kwh, hiv_eur, ete_eur, has_file):
                            st.balloons()
                            st.success(f"Dossier {nom_client} envoyé en 'En Cours' !")
                            st.cache_data.clear() # Le client va disparaitre de cette liste et aller dans "En cours"
                        else:
                            st.error("Erreur")

# ==============================================================================
# 4️⃣ DOSSIERS EN COURS / VALIDÉS
# ==============================================================================
elif menu == "4️⃣ Dossiers En Cours / Validés":
    st.subheader("🚀 Suivi des Dossiers")
    
    if not df_factures.empty:
        # Onglets pour séparer En cours / Validé
        tab1, tab2 = st.tabs(["⏳ En Cours", "✅ Validés"])
        
        with tab1:
            encours = df_factures[df_factures['Etat_Dossier'] == "En cours"]
            if encours.empty: st.info("Aucun dossier en attente.")
            else: st.dataframe(encours, use_container_width=True)
            
        with tab2:
            valides = df_factures[df_factures['Etat_Dossier'] == "Validé"] # Tu devras écrire "Validé" manuellement dans le sheet pour qu'ils arrivent ici
            if valides.empty: st.info("Aucun dossier validé pour l'instant.")
            else: st.dataframe(valides, use_container_width=True)
    else:
        st.write("Aucun dossier enregistré.")

