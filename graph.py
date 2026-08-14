import pandas as pd
import streamlit as st

# IMPORTANT: set_page_config doit être la toute première commande Streamlit du script
st.set_page_config(page_title="Graphique des actions BRVM",
                    page_icon="📈",
                    layout="centered")
#le titre de la web_app
st.title('Evolution des actions BRVM')







#les grandes lignes
st.markdown(""" les actions les plus couteuses de la  BRVM  """)
les_grandes_capitalisations = pd.DataFrame(
    {
        "Solibra": [41000],
        "Sonatel": [31500],
        "Unilever": [52000],
        "Nsia Bank": [23000],
        "Sitab" : [23405]
    },
    #index=["Solibra", "Sonatel", "Unilever", "Nsia Bank"],
)
st.table(les_grandes_capitalisations)

st.markdown(""" Les actions les moins couteuses de la BRVM""")
low_actions=pd.DataFrame(
    {
        "ETIT" : [75],
        "SEMC" : [1500],
        "UNXC" : [1800],
        "BNBC" : [1985],
        "CFAC" : [1695]
    }
)
st.table(low_actions)




st.logo("BRVM.png",size="large")

# --- Chargement des données ---
data = pd.read_csv('DATA.csv')

data['Date'] = pd.to_datetime(data['Date'])

data["Symbole"] = data["source"]
data["Cours"] = data["Cours Normal"]

# "DATA" est une erreur de saisie dans la source (ne correspond à aucune société) : on l'exclut
data = data[data["Symbole"] != "DATA"]


st.write("""Graphique des actions BRVM""")
st.text("Les graphiques présents sur cette page vous montrent l'évolution "
        "des actions BRVM dans le temps")

# --- Barre latérale de navigation ---
st.sidebar.header("Navigation")

actions = sorted(data['Symbole'].unique())
action_choisie = st.sidebar.selectbox("Choisissez une action BRVM", actions)


#on va afficheé des tableaux
#st.table(data[data['Symbole'] == action_choisie].sort_values('Cours'))

st.image("images.png", caption="Investir c'est aussi une question de temps")



# Filtre par date : on propose les dates disponibles dans le fichier
dates_dispo = sorted(data['Date'].dt.date.unique())
date_min, date_max = dates_dispo[0], dates_dispo[-1]

periode = st.sidebar.date_input(
    "Période à afficher",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

# Ajout d'un tableau pour affiché les donneés
st.table(data[data['Symbole'] == action_choisie].sort_values('Date').head(5))


# Si l'utilisateur n'a sélectionné qu'une seule date pour l'instant,
# on évite une erreur en attendant qu'il choisisse la borne de fin
if isinstance(periode, tuple) and len(periode) == 2:
    date_debut, date_fin = periode
else:
    date_debut, date_fin = date_min, date_max

voir_tout = st.sidebar.checkbox("Afficher le graphique de toutes les actions")

# --- Application du filtre de dates sur les données ---
masque_date = (data['Date'].dt.date >= date_debut) & (data['Date'].dt.date <= date_fin)
data_filtree = data[masque_date]

# 1) Graphique de l'action choisie dans la sidebar
df_action = data_filtree[data_filtree['Symbole'] == action_choisie].sort_values('Date')

st.subheader(f"Cours de {action_choisie}")
#st.line_chart(df_action.set_index('Date')['Cours'])
#st.area_chart(df_action.set_index('Date')['Cours'])

st.area_chart(df_action.set_index('Date')['Cours'],height=400, color=["#0000FF80"])



st.divider()

# 2) Option : afficher automatiquement UN graphique pour CHAQUE action
#    (utile si tu veux tout voir sans re-cliquer dans le selectbox)
if voir_tout:
    for symbole in actions:
        df_sym = data_filtree[data_filtree['Symbole'] == symbole].sort_values('Date')
        st.subheader(symbole)
        st.line_chart(df_sym.set_index('Date')['Cours'])

#iframe pour ajouter des elements exterme
#st.iframe(src="https://docs.streamlit.io")

## Autres outils d'annalyse
## une courbe de prediction des cours
## une analyse basé sur les resultats, du chiffre d'affaire des entreprises

# --- Correspondance entre les noms utilisés dans DATA.csv et les tickers officiels BRVM ---
# DATA.csv contient des noms saisis à la main (ex: "Tractafric", "BOA_SN") qui ne
# correspondent pas aux tickers officiels utilisés dans le fichier Excel (ex: "PRSC", "BOAS").
# Ce dictionnaire fait le lien entre les deux. Clé = valeur dans DATA.csv, valeur = ticker Excel.
CORRESPONDANCE_SYMBOLES = {
    "Vivo energy": "SHEC",
    "AGL": "SDSC",
    "ECOBANK_CI": "ECOC",
    "Filtisac": "FTSC",
    "LNBB": "LNBB",
    "NEI-CEDA": "NEIC",
    "Bernabe": "BNBC",
    "Nestle": "NTLC",
    "ETIT": "ETIT",
    "Total ci": "TTLC",
    "Setao": "STAC",
    "BOA_SN": "BOAS",
    "SGB CI": "SGBC",
    "Sucrivoire": "SCRC",
    "SIBC": "SIBC",
    "BOA_NIGER": "BOAN",
    "Sicable": "CABC",
    "SOGB": "SOGC",
    "Sicor_ci": "SICC",
    "BOA_MALI": "BOAM",
    "Sitab_ci": "STBC",
    "Sonatel": "SNTS",
    "SMBC": "SMBC",
    "BOA_CI": "BOAC",
    "SODE CI": "SDCC",
    "Solibra": "SLBC",
    "BOA_BENIN": "BOAB",
    "BICC": "BICC",
    "Servair": "ABJC",
    "SEMC": "SEMC",
    "NSIA": "NSBC",
    "Uniwax": "UNXC",
    "Onatel bf": "ONTBF",
    "ORAGROUP_TOGO": "ORGT",
    "Unilever": "UNLC",
    "BICB": "BICB",
    "Cfao": "CFAC",
    "CORIS_BANK": "CBIBF",
    "Orange ci": "ORAC",
    "Palm ci": "PALC",
    "SAFCA": "SAFC",
    "CIE CI": "CIEC",
    "Saph": "SPHC",
    "Total senegal": "TTLS",
    "Tractafric": "PRSC",
    "BOA_BF": "BOABF",
    "Erium ci": "SIVC",  # Air Liquide CI
}


def vers_ticker_officiel(nom_action):
    """Traduit un nom d'action tel qu'il apparaît dans DATA.csv vers son ticker officiel BRVM."""
    return CORRESPONDANCE_SYMBOLES.get(nom_action)


# --- Chargement des indicateurs financiers (CA, Résultat net, Dividende) ---
FICHIER_FINANCIER = 'Données CA - RN - DIV 2023-2025.xlsx'


@st.cache_data
def charger_feuille_financiere(nom_feuille):
    """Lit une feuille du classeur financier et normalise ses colonnes.
    Les feuilles ont 2 lignes d'en-tête avant les vraies colonnes,
    d'où header=2. On repasse ensuite les colonnes en noms lisibles.
    """
    feuille = pd.read_excel(FICHIER_FINANCIER, sheet_name=nom_feuille, header=2)
    feuille.columns = ['Symbole', 'Societe', '2023', '2024', '2025']
    feuille = feuille.dropna(subset=['Symbole'])
    return feuille


ca = charger_feuille_financiere('CA')
resultat_net = charger_feuille_financiere('Résultat_net')
dividende = charger_feuille_financiere('Dividende')

st.divider()
st.subheader(f"Indicateurs financiers de {action_choisie}")

ticker = vers_ticker_officiel(action_choisie)

if ticker is None:
    st.warning(
        f"'{action_choisie}' n'a pas de correspondance connue dans le fichier financier. "
        "Cette action est peut-être mal renseignée à la source (DATA.csv)."
    )
else:
    def afficher_indicateur_brut(nom_colonne, libelle_affiche, tableau):
        """Affiche le graphique en barres d'un indicateur brut (CA, RN ou Dividende)."""
        ligne = tableau[tableau['Symbole'] == ticker]

        if ligne.empty:
            st.info(f"Pas de données '{libelle_affiche}' disponibles pour {action_choisie}.")
            return

        # value_name utilise nom_colonne (sans apostrophe ni espace) car Vega-Lite,
        # le moteur derrière st.bar_chart, échoue silencieusement sur certains noms
        # de champs contenant une apostrophe (ex: "Chiffre d'affaires").
        evolution = ligne.melt(
            id_vars=['Symbole', 'Societe'],
            value_vars=['2023', '2024', '2025'],
            var_name='Année',
            value_name=nom_colonne,
        ).dropna(subset=[nom_colonne])

        st.markdown(f"**{libelle_affiche}**")
        if evolution.empty:
            st.info(f"Aucune valeur renseignée pour '{libelle_affiche}'.")
        else:
            st.bar_chart(evolution.set_index('Année')[nom_colonne])

    def calculer_croissance(tableau, ticker):
        """Calcule la variation en % d'une année sur l'autre (2024 vs 2023, 2025 vs 2024)."""
        ligne = tableau[tableau['Symbole'] == ticker]
        if ligne.empty:
            return pd.DataFrame()

        paires_annees = [('2023', '2024'), ('2024', '2025')]
        lignes_croissance = []
        for annee_prec, annee_actuelle in paires_annees:
            valeur_prec = ligne[annee_prec].values[0]
            valeur_actuelle = ligne[annee_actuelle].values[0]
            if pd.notna(valeur_prec) and pd.notna(valeur_actuelle) and valeur_prec != 0:
                taux = ((valeur_actuelle - valeur_prec) / valeur_prec) * 100
                lignes_croissance.append({"Année": annee_actuelle, "croissance": taux})

        return pd.DataFrame(lignes_croissance)

    def afficher_croissance(tableau, libelle_indicateur, legende):
        """Affiche le graphique en barres de la croissance annuelle d'un indicateur."""
        st.markdown(f"**Croissance {libelle_indicateur}**")
        croissance = calculer_croissance(tableau, ticker)
        if croissance.empty:
            st.info(f"Pas assez d'années disponibles pour calculer la croissance {libelle_indicateur} de {action_choisie}.")
        else:
            st.bar_chart(croissance.set_index('Année')['croissance'])
            st.caption(legende)

    # --- 1) Chiffre d'affaires + sa croissance ---
    afficher_indicateur_brut("ca_valeur", "Chiffre d'affaires", ca)
    afficher_croissance(ca, "du chiffre d'affaires", "Croissance du CA en % par rapport à l'année précédente")

    # --- 2) Résultat net + sa croissance ---
    afficher_indicateur_brut("rn_valeur", "Résultat net", resultat_net)
    afficher_croissance(resultat_net, "du résultat net", "Croissance du résultat net en % par rapport à l'année précédente")

    # --- 3) Dividende ---
    afficher_indicateur_brut("div_valeur", "Dividende par action", dividende)

    # --- 4) Marge nette = Résultat net / Chiffre d'affaires ---
    st.markdown("**Marge nette**")

    ligne_ca = ca[ca['Symbole'] == ticker]
    ligne_rn = resultat_net[resultat_net['Symbole'] == ticker]

    if ligne_ca.empty or ligne_rn.empty:
        st.info(f"Pas assez de données pour calculer la marge nette de {action_choisie}.")
    else:
        annees = ['2023', '2024', '2025']
        lignes_marge = []
        for annee in annees:
            valeur_ca = ligne_ca[annee].values[0]
            valeur_rn = ligne_rn[annee].values[0]
            if pd.notna(valeur_ca) and pd.notna(valeur_rn) and valeur_ca != 0:
                marge = (valeur_rn / valeur_ca) * 100
                lignes_marge.append({"Année": annee, "marge_nette": marge})

        if not lignes_marge:
            st.info(f"Aucune année avec CA et Résultat net disponibles pour {action_choisie}.")
        else:
            marge_nette = pd.DataFrame(lignes_marge)
            st.line_chart(marge_nette.set_index('Année')['marge_nette'])
            st.caption("Marge nette en % (Résultat net / Chiffre d'affaires)")

            # Une marge nette hors de cette plage indique presque toujours une erreur
            # de saisie dans le fichier Excel source (CA ou RN mal renseigné), pas un
            # vrai résultat d'entreprise.
            marges_suspectes = marge_nette[
                (marge_nette['marge_nette'] > 100) | (marge_nette['marge_nette'] < -100)
            ]
            if not marges_suspectes.empty:
                annees_suspectes = ", ".join(marges_suspectes['Année'])
                st.warning(
                    f"Marge nette anormale détectée pour {annees_suspectes} "
                    f"({action_choisie}) — vérifie le CA et le Résultat net dans le "
                    "fichier Excel source, une valeur semble mal saisie."
                )