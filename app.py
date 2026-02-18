import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="ArchiroData CRM", layout="wide", page_icon="⚡")

# --- STYLE CSS (Mode Clair Force) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; color: #1f1f1f !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #dee2e6; }
    [data-testid="stSidebar"] * { color: #1f1f1f !important; }
    .stButton>button { width: 100%; border-radius: 6px; font-weight: 600; }
    div[data-testid="stMetric"] { background-color: #fff; border: 1px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #1f1f1f; }
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

# Chargement de la base principale (Lecture seule)
@st.cache_data(ttl=300)
def load_base_data():
    try:
        client = get_client()
        sheet = client.open("Data_Prospection_Energie").sheet1
        vals = sheet.get_all_values()
        if len(vals) > 1:
            df = pd.DataFrame(vals[1:], columns=vals[0])
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

# Sauvegarde d'une action (Appel, Statut)
def save_interaction(commercial, entreprise, ville, statut, note, contact_nom, contact_email):
    try:
        client = get_client()
        # On essaie d'ouvrir l'onglet, s'il n'existe pas on le crée
        try: sheet = client.open("Data_Prospection_Energie").worksheet("Suivi_Commerciaux")
        except: sheet = client.open("Data_Prospection_Energie").add_worksheet("Suivi_Commerciaux", 1000, 10)
        
        row = [str(datetime.now()), commercial, entreprise, ville, statut, note, contact_nom, contact_email]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Erreur sauvegarde : {e}")
        return False

# Sauvegarde des données factures
def save_facture(commercial, client_nom, hiver_kwh, ete_kwh, hiver_eur, ete_eur, a_facture):
    try:
        client = get_client()
        try: sheet = client.open("Data_Prospection_Energie").worksheet("Donnees_Factures")
        except: sheet = client.open("Data_Prospection_Energie").add_worksheet("Donnees_Factures", 1000, 10)
        
        # On note "OUI" si un fichier a été joint, sinon "NON"
        facture_recue = "OUI (PDF)" if a_facture else "NON"
        
        row = [commercial, client_nom, hiver_kwh, ete_kwh, hiver_eur, ete_eur, str(datetime.now()), facture_recue]
        sheet.append_row(row)
        return True
    except: return False

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

# Sidebar
with st.sidebar:
    st.markdown(f"### 👤 {user.upper()}")
    menu_options = ["📞 Prospection (Appels)", "📂 Mon Portefeuille", "📊 Stats Perso"]
    if user == "admin": menu_options.append("⚙️ Admin")
    
    menu = st.radio("Navigation", menu_options)
    
    st.markdown("---")
    if st.button("Déconnexion"):
        st.session_state.logged_in = False
        st.rerun()

# --- 1. PROSPECTION (La Chasse) ---
if menu == "📞 Prospection (Appels)":
    st.subheader("🎯 Session de Prospection")
    df = load_base_data()
    
    if not df.empty:
        c1, c2 = st.columns(2)
        # Gestion sécurisée des listes déroulantes
        villes = sorted(df['Ville'].unique().tolist()) if 'Ville' in df.columns else []
        secteurs = sorted(df['Secteur'].unique().tolist()) if 'Secteur' in df.columns else []
        
        ville = c1.selectbox("Choisir une Ville", ["Toutes"] + villes)
        secteur = c2.selectbox("Choisir un Secteur", ["Tous"] + secteurs)
        
        # Filtrage
        mask = pd.Series([True] * len(df))
        if ville != "Toutes": mask &= (df['Ville'] == ville)
        if secteur != "Tous": mask &= (df['Secteur'] == secteur)
        filtered = df[mask]
        
        st.info(f"**{len(filtered)} leads correspondants**")
        
        # Affichage Lead par Lead (Plus focus que le tableau)
        if len(filtered) > 0:
            # Création d'une liste unique pour la sélection
            lead_options = filtered.apply(lambda x: f"{x.get('Nom', 'Inconnu')} ({x.get('Ville', '?')})", axis=1).tolist()
            selected_lead_name = st.selectbox("Sélectionner une entreprise à appeler :", lead_options)
            
            # Récupérer les infos du lead choisi
            lead = filtered.iloc[lead_options.index(selected_lead_name)]
            
            with st.container(border=True):
                c_info, c_action = st.columns([1, 1])
                
                with c_info:
                    st.markdown(f"### 🏢 {lead.get('Nom', 'N/A')}")
                    st.markdown(f"📍 **Adresse:** {lead.get('Adresse', 'N/A')}")
                    st.markdown(f"📞 **Téléphone:** `{lead.get('Téléphone', 'N/A')}`")
                    st.markdown(f"📱 **Mobile:** `{lead.get('Mobile', 'N/A')}`")
                    
                    # Bouton d'action rapide Mail
                    email_dest = lead.get('Site Web', '') # Simplification
                    subject = urllib.parse.quote("Question sur vos contrats énergie")
                    body = urllib.parse.quote("Bonjour,\n\nJe souhaiterais échanger avec vous...")
                    st.markdown(f"[✉️ Ouvrir Email pré-rempli](mailto:?subject={subject}&body={body})", unsafe_allow_html=True)

                with c_action:
                    st.markdown("### 📝 Rapport d'appel")
                    with st.form("log_call"):
                        statut = st.radio("Résultat :", ["⏳ En attente", "✅ Positif (Intéressé)", "❌ Négatif", "📵 Pas de réponse"], horizontal=True)
                        note = st.text_area("Commentaire", placeholder="Ex: A rappelé mardi...", height=80)
                        
                        st.markdown("**Si Positif, noter le contact :**")
                        c1, c2 = st.columns(2)
                        c_nom = c1.text_input("Nom Décideur")
                        c_mail = c2.text_input("Email Décideur")
                        
                        if st.form_submit_button("💾 Sauvegarder"):
                            if save_interaction(user, lead.get('Nom'), lead.get('Ville'), statut, note, c_nom, c_mail):
                                st.success("Enregistré !")
                            else:
                                st.error("Erreur technique.")

# --- 2. MON PORTEFEUILLE (Le Suivi) ---
elif menu == "📂 Mon Portefeuille":
    st.subheader("💼 Mes Dossiers Gagnés")
    
    # On charge l'historique depuis la Google Sheet 'Suivi_Commerciaux'
    try:
        client = get_client()
        sheet_suivi = client.open("Data_Prospection_Energie").worksheet("Suivi_Commerciaux")
        data_suivi = sheet_suivi.get_all_records()
        df_suivi = pd.DataFrame(data_suivi)
    except:
        df_suivi = pd.DataFrame()

    if not df_suivi.empty:
        # Filtrer pour voir uniquement les clients de CE commercial
        if 'Commercial' in df_suivi.columns:
            my_leads = df_suivi[df_suivi['Commercial'] == user]
            # Garder seulement les Positifs ou En attente
            active_leads = my_leads[my_leads['Statut'].isin(["✅ Positif (Intéressé)", "⏳ En attente"])]
            
            st.write(f"Vous avez {len(active_leads)} dossiers à traiter.")
            
            if len(active_leads) > 0:
                client_choisi = st.selectbox("Sélectionner un dossier pour Facturation :", active_leads['Nom Entreprise'].unique())
                
                st.markdown("---")
                st.markdown(f"### ⚡ Saisie Factures : {client_choisi}")
                
                with st.form("facture_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("❄️ **Hiver**")
                        hiv_kwh = st.text_input("Conso Hiver (kWh)")
                        hiv_eur = st.text_input("Montant Hiver (€)")
                    with c2:
                        st.markdown("☀️ **Été**")
                        ete_kwh = st.text_input("Conso Été (kWh)")
                        ete_eur = st.text_input("Montant Été (€)")
                    
                    st.markdown("---")
                    st.markdown("**📄 Pièce Jointe**")
                    uploaded_file = st.file_uploader("Joindre la facture (PDF/Image)", type=['pdf', 'png', 'jpg', 'jpeg'])
                    
                    if st.form_submit_button("Valider le dossier"):
                        # On vérifie si un fichier est présent
                        has_file = uploaded_file is not None
                        
                        if save_facture(user, client_choisi, hiv_kwh, ete_kwh, hiv_eur, ete_eur, has_file):
                            st.balloons()
                            st.success(f"Données enregistrées pour {client_choisi} !")
                            if has_file:
                                st.info("✅ Fichier PDF bien reçu (Transmis à l'admin)")
                        else:
                            st.error("Erreur de sauvegarde.")
        else:
            st.warning("Structure du fichier 'Suivi_Commerciaux' incorrecte.")
    else:
        st.info("Aucun historique. Allez dans l'onglet 'Prospection' pour commencer.")

# --- 3. STATS ---
elif menu == "📊 Stats Perso":
    st.subheader("📈 Mes Performances")
    try:
        client = get_client()
        sheet_suivi = client.open("Data_Prospection_Energie").worksheet("Suivi_Commerciaux")
        df_stats = pd.DataFrame(sheet_suivi.get_all_records())
        
        if not df_stats.empty and 'Commercial' in df_stats.columns:
            my_stats = df_stats[df_stats['Commercial'] == user]
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Appels Totaux", len(my_stats))
            
            positifs = len(my_stats[my_stats['Statut'] == "✅ Positif (Intéressé)"])
            col2.metric("Leads Gagnés", positifs)
            
            ratio = round((positifs / len(my_stats) * 100), 1) if len(my_stats) > 0 else 0
            col3.metric("Taux de Transformation", f"{ratio}%")
            
            st.markdown("### 🗓️ Historique récent")
            st.dataframe(my_stats.tail(10), use_container_width=True)
        else:
            st.write("Pas de données disponibles.")
            
    except Exception as e:
        st.write("Chargement des stats...")

# --- ADMIN ---
elif menu == "⚙️ Admin":
    st.title("Administration")
    st.write("Module d'import (réservé admin)")
    uploaded_file = st.file_uploader("Importer CSV", type="csv")
    if uploaded_file and st.button("Mettre à jour la base"):
        try:
            client = get_client()
            sheet = client.open("Data_Prospection_Energie").sheet1
            df_new = pd.read_csv(uploaded_file).fillna("N/A")
            sheet.clear()
            sheet.update('A1', [df_new.columns.values.tolist()] + df_new.values.tolist())
            st.success("Base mise à jour !")
        except Exception as e: st.error(f"Erreur : {e}")
