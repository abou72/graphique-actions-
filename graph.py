import pandas as pd
import streamlit as st

# IMPORTANT: set_page_config doit être la toute première commande Streamlit du script
st.set_page_config(page_title="Graphique des actions BRVM",
                    page_icon="📈",
                    layout="wide")

st.title('Outils de visualisation des actions BRVM et des indicateurs financier')

st.markdown("""
La BRVM regroupe 47 sociétés cotées réparties dans plusieurs secteurs
d'activité — banques, télécoms, agro-industrie, distribution — au sein
de l'espace UEMOA. Les cours présentés dans cette application couvrent
l'ensemble de ces valeurs et vous permettent de suivre leur évolution
dans le temps, ainsi que leurs principaux indicateurs financiers
(chiffre d'affaires, résultat net, dividende).
""")

st.logo("BRVM.png", size="large")


# =====================================================================
# CHARGEMENT DES DONNÉES
# =====================================================================

@st.cache_data
def charger_cours():
    """Charge et prépare le fichier des cours boursiers."""
    donnees = pd.read_csv('DATA.csv')
    donnees['Date'] = pd.to_datetime(donnees['Date'])
    donnees["Symbole"] = donnees["source"]
    donnees["Cours"] = donnees["Cours Normal"]
    # "DATA" est une erreur de saisie dans la source (ne correspond à aucune société) : on l'exclut
    donnees = donnees[donnees["Symbole"] != "DATA"]
    return donnees


try:
    data = charger_cours()
except FileNotFoundError:
    st.error(
        "Fichier 'DATA.csv' introuvable. Vérifie qu'il se trouve bien dans le même "
        "dossier que graph.py avant de relancer l'application."
    )
    st.stop()
except KeyError as erreur:
    st.error(
        f"Colonne manquante dans DATA.csv ({erreur}). Vérifie que le fichier contient "
        "bien les colonnes 'Date', 'source' et 'Cours Normal'."
    )
    st.stop()

actions = sorted(data['Symbole'].unique())

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


try:
    ca = charger_feuille_financiere('CA')
    resultat_net = charger_feuille_financiere('Résultat_net')
    dividende = charger_feuille_financiere('Dividende')
except FileNotFoundError:
    st.error(
        f"Fichier '{FICHIER_FINANCIER}' introuvable. Vérifie qu'il se trouve bien dans "
        "le même dossier que graph.py avant de relancer l'application."
    )
    st.stop()


# =====================================================================
# FONCTIONS PARTAGÉES
# =====================================================================

def afficher_indicateur_brut(nom_colonne, libelle_affiche, tableau, ticker, action_choisie, diviseur=1, unite=""):
    """Affiche le graphique en barres d'un indicateur brut (CA, RN ou Dividende).
    diviseur/unite permettent d'afficher de grands montants en Md FCFA plutôt
    qu'en valeur brute illisible (ex: 82623385000 -> 82.62 Md FCFA).
    """
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

    libelle_complet = f"{libelle_affiche} ({unite})" if unite else libelle_affiche
    st.markdown(f"**{libelle_complet}**")
    if evolution.empty:
        st.info(f"Aucune valeur renseignée pour '{libelle_affiche}'.")
    else:
        if diviseur != 1:
            evolution[nom_colonne] = (evolution[nom_colonne] / diviseur).round(2)
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


def afficher_croissance(tableau, ticker, action_choisie, libelle_indicateur, legende):
    """Affiche le graphique en barres de la croissance annuelle d'un indicateur."""
    st.markdown(f"**Croissance {libelle_indicateur}**")
    croissance = calculer_croissance(tableau, ticker)
    if croissance.empty:
        st.info(f"Pas assez d'années disponibles pour calculer la croissance {libelle_indicateur} de {action_choisie}.")
    else:
        st.bar_chart(croissance.set_index('Année')['croissance'])
        st.caption(legende)
        # Commentaire basé sur la croissance de la dernière année disponible
        derniere_annee = croissance.iloc[-1]
        commentaire = commenter_croissance(derniere_annee['croissance'], libelle_indicateur)
        if commentaire:
            st.markdown(f"_{commentaire}_")


def valeur_annee(tableau, ticker, annee):
    """Retourne la valeur d'un indicateur pour un ticker et une année donnés, ou None."""
    ligne = tableau[tableau['Symbole'] == ticker]
    if ligne.empty:
        return None
    valeur = ligne[annee].values[0]
    return valeur if pd.notna(valeur) else None


def calculer_marge_nette_annee(ticker, annee):
    """Calcule la marge nette (RN/CA en %) pour un ticker et une année donnés."""
    valeur_ca = valeur_annee(ca, ticker, annee)
    valeur_rn = valeur_annee(resultat_net, ticker, annee)
    if valeur_ca is None or valeur_rn is None or valeur_ca == 0:
        return None
    return (valeur_rn / valeur_ca) * 100


def calculer_croissance_annee(tableau, ticker, annee):
    """Calcule la croissance en % d'un indicateur pour l'année donnée par rapport à l'année précédente."""
    annee_prec = str(int(annee) - 1)
    if annee_prec not in ['2023', '2024', '2025']:
        return None
    valeur_prec = valeur_annee(tableau, ticker, annee_prec)
    valeur_actuelle = valeur_annee(tableau, ticker, annee)
    if valeur_prec is None or valeur_actuelle is None or valeur_prec == 0:
        return None
    return ((valeur_actuelle - valeur_prec) / valeur_prec) * 100


def commenter_croissance(taux, libelle_indicateur):
    """Génère un commentaire textuel qualifiant un taux de croissance selon des seuils simples."""
    if taux is None:
        return None
    if taux > 20:
        return f"Forte croissance {libelle_indicateur} ({taux:.1f}%)."
    elif taux > 5:
        return f"Croissance solide {libelle_indicateur} ({taux:.1f}%)."
    elif taux > 0:
        return f"Croissance modérée {libelle_indicateur} ({taux:.1f}%)."
    elif taux > -5:
        return f"Légère baisse {libelle_indicateur} ({taux:.1f}%)."
    else:
        return f"Baisse marquée {libelle_indicateur} ({taux:.1f}%)."


def commenter_marge_nette(marge):
    """Génère un commentaire textuel qualifiant une marge nette selon des seuils simples."""
    if marge is None:
        return None
    if marge < 0:
        return f"L'entreprise est en perte sur cette période (marge nette de {marge:.1f}%)."
    elif marge < 5:
        return f"Marge nette faible ({marge:.1f}%)."
    elif marge < 10:
        return f"Marge nette correcte ({marge:.1f}%)."
    elif marge < 20:
        return f"Marge nette confortable ({marge:.1f}%)."
    else:
        return f"Marge nette très élevée ({marge:.1f}%)."


# =====================================================================
# BARRE LATÉRALE — sélection commune aux onglets 1 et 2
# =====================================================================

st.sidebar.header("Navigation")
action_choisie = st.sidebar.selectbox("Choisissez une action BRVM", actions)

dates_dispo = sorted(data['Date'].dt.date.unique())
date_min, date_max = dates_dispo[0], dates_dispo[-1]

periode = st.sidebar.date_input(
    "Période à afficher",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

if isinstance(periode, tuple) and len(periode) == 2:
    date_debut, date_fin = periode
else:
    date_debut, date_fin = date_min, date_max

masque_date = (data['Date'].dt.date >= date_debut) & (data['Date'].dt.date <= date_fin)
data_filtree = data[masque_date]

ticker_selectionne = vers_ticker_officiel(action_choisie)


# =====================================================================
# LES 3 GRANDS ESPACES
# =====================================================================

onglet_boursier, onglet_financier, onglet_comparateur = st.tabs([
    "📈 Analyse boursière",
    "💰 Analyse financière",
    "🔍 Comparateur",
])


# --- 1) ANALYSE BOURSIÈRE ---------------------------------------------
with onglet_boursier:
    st.header(f"Cours de {action_choisie}")

    df_action = data_filtree[data_filtree['Symbole'] == action_choisie].sort_values('Date')

    st.subheader("Évolution historique")
    st.area_chart(df_action.set_index('Date')['Cours'], height=400, color=["#0000FF80"])

    st.download_button(
        label=f"Exporter les cours de {action_choisie} (CSV)",
        data=df_action.to_csv(index=False).encode('utf-8'),
        file_name=f"cours_{action_choisie}.csv",
        mime="text/csv",
    )

    voir_tout = st.checkbox("Afficher le graphique de toutes les actions")
    if voir_tout:
        for symbole in actions:
            df_sym = data_filtree[data_filtree['Symbole'] == symbole].sort_values('Date')
            st.subheader(symbole)
            st.line_chart(df_sym.set_index('Date')['Cours'])

    st.divider()

    st.subheader("Comparaison des cours")
    st.markdown("Pour effectuer une comparaison entre les cours, veillez choisir des actions du même secteur d'activité.")
    actions_a_comparer = st.multiselect(
        "Choisissez 2 à 5 actions à comparer",
        actions,
        default=[action_choisie],
        max_selections=5,
    )

    if len(actions_a_comparer) >= 2:
        data_comparaison = data_filtree[data_filtree['Symbole'].isin(actions_a_comparer)]
        tableau_comparaison = data_comparaison.pivot_table(
            index='Date', columns='Symbole', values='Cours'
        )
        st.line_chart(tableau_comparaison)
    elif len(actions_a_comparer) == 1:
        st.info("Sélectionne au moins une deuxième action pour afficher une comparaison.")


# --- 2) ANALYSE FINANCIÈRE ---------------------------------------------
with onglet_financier:
    st.header(f"Indicateurs financiers de {action_choisie}")

    if ticker_selectionne is None:
        st.warning(
            f"'{action_choisie}' n'a pas de correspondance connue dans le fichier financier. "
            "Cette action est peut-être mal renseignée à la source (DATA.csv)."
        )
    else:
        # --- Chiffre d'affaires + sa croissance ---
        afficher_indicateur_brut("ca_valeur", "Chiffre d'affaires", ca, ticker_selectionne, action_choisie,
                                  diviseur=1_000_000_000, unite="Md FCFA")
        afficher_croissance(ca, ticker_selectionne, action_choisie, "du chiffre d'affaires",
                             "Croissance du CA en % par rapport à l'année précédente")

        # --- Résultat net + sa croissance ---
        afficher_indicateur_brut("rn_valeur", "Résultat net", resultat_net, ticker_selectionne, action_choisie,
                                  diviseur=1_000_000_000, unite="Md FCFA")
        afficher_croissance(resultat_net, ticker_selectionne, action_choisie, "du résultat net",
                             "Croissance du résultat net en % par rapport à l'année précédente")

        # --- Dividende ---
        afficher_indicateur_brut("div_valeur", "Dividende par action", dividende, ticker_selectionne,
                                  action_choisie, unite="FCFA")

        # --- Marge nette ---
        st.markdown("**Marge nette**")
        annees = ['2023', '2024', '2025']
        lignes_marge = []
        for annee in annees:
            marge = calculer_marge_nette_annee(ticker_selectionne, annee)
            if marge is not None:
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
            else:
                # Commentaire basé sur la marge nette de la dernière année disponible
                derniere_marge = marge_nette.iloc[-1]['marge_nette']
                commentaire_marge = commenter_marge_nette(derniere_marge)
                if commentaire_marge:
                    st.markdown(f"_{commentaire_marge}_")

        # --- Export ---
        tableau_export = pd.DataFrame({'Année': annees})
        tableau_export["Chiffre d'affaires"] = [valeur_annee(ca, ticker_selectionne, a) for a in annees]
        tableau_export["Résultat net"] = [valeur_annee(resultat_net, ticker_selectionne, a) for a in annees]
        tableau_export["Dividende par action"] = [valeur_annee(dividende, ticker_selectionne, a) for a in annees]

        st.download_button(
            label=f"Exporter les indicateurs financiers de {action_choisie} (CSV)",
            data=tableau_export.to_csv(index=False).encode('utf-8'),
            file_name=f"indicateurs_{action_choisie}.csv",
            mime="text/csv",
        )


# --- 3) COMPARATEUR ---------------------------------------------------
with onglet_comparateur:
    st.header("Comparateur d'entreprises")

    entreprises_comparees = st.multiselect(
        "Sélectionnez 2 à 5 entreprises à comparer",
        actions,
        max_selections=5,
        key="comparateur_entreprises",
    )
    annee_comparee = st.selectbox("Choisissez une année", ['2023', '2024', '2025'], key="comparateur_annee")

    if len(entreprises_comparees) < 2:
        st.info("Sélectionne au moins 2 entreprises pour lancer une comparaison.")
    else:
        lignes_comparateur = []
        entreprises_sans_correspondance = []

        for nom_entreprise in entreprises_comparees:
            ticker_entreprise = vers_ticker_officiel(nom_entreprise)
            if ticker_entreprise is None:
                entreprises_sans_correspondance.append(nom_entreprise)
                continue

            valeur_ca_entreprise = valeur_annee(ca, ticker_entreprise, annee_comparee)
            valeur_rn_entreprise = valeur_annee(resultat_net, ticker_entreprise, annee_comparee)
            valeur_marge = calculer_marge_nette_annee(ticker_entreprise, annee_comparee)
            valeur_croissance_ca = calculer_croissance_annee(ca, ticker_entreprise, annee_comparee)
            valeur_croissance_rn = calculer_croissance_annee(resultat_net, ticker_entreprise, annee_comparee)
            valeur_div = valeur_annee(dividende, ticker_entreprise, annee_comparee)

            lignes_comparateur.append({
                "Entreprise": nom_entreprise,
                "Chiffre d'affaires (Md FCFA)": round(valeur_ca_entreprise / 1_000_000_000, 2) if valeur_ca_entreprise is not None else None,
                "Résultat net (Md FCFA)": round(valeur_rn_entreprise / 1_000_000_000, 2) if valeur_rn_entreprise is not None else None,
                "Marge nette (%)": round(valeur_marge, 2) if valeur_marge is not None else None,
                "Croissance CA (%)": round(valeur_croissance_ca, 2) if valeur_croissance_ca is not None else None,
                "Croissance RN (%)": round(valeur_croissance_rn, 2) if valeur_croissance_rn is not None else None,
                "Dividende par action (FCFA)": valeur_div,
            })

        if entreprises_sans_correspondance:
            st.warning(
                "Pas de correspondance financière connue pour : "
                + ", ".join(entreprises_sans_correspondance)
            )

        if not lignes_comparateur:
            st.info("Aucune des entreprises sélectionnées n'a de données financières disponibles.")
        else:
            tableau_comparateur = pd.DataFrame(lignes_comparateur).set_index("Entreprise")

            st.subheader(f"Tableau comparatif — {annee_comparee}")
            st.dataframe(tableau_comparateur, use_container_width=True)

            colonne_gauche, colonne_droite = st.columns(2)

            with colonne_gauche:
                st.markdown("**Chiffre d'affaires (Md FCFA)**")
                st.bar_chart(tableau_comparateur["Chiffre d'affaires (Md FCFA)"])

                st.markdown("**Marge nette (%)**")
                st.bar_chart(tableau_comparateur["Marge nette (%)"])

                st.markdown("**Croissance CA (%)**")
                st.bar_chart(tableau_comparateur["Croissance CA (%)"])

            with colonne_droite:
                st.markdown("**Résultat net (Md FCFA)**")
                st.bar_chart(tableau_comparateur["Résultat net (Md FCFA)"])

                st.markdown("**Dividende par action (FCFA)**")
                st.bar_chart(tableau_comparateur["Dividende par action (FCFA)"])

                st.markdown("**Croissance RN (%)**")
                st.bar_chart(tableau_comparateur["Croissance RN (%)"])

            st.download_button(
                label=f"Exporter le comparatif {annee_comparee} (CSV)",
                data=tableau_comparateur.to_csv().encode('utf-8'),
                file_name=f"comparateur_{annee_comparee}.csv",
                mime="text/csv",
            )