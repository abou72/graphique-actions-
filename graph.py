import io
from datetime import datetime

import pandas as pd
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,
)

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
    donnees = pd.read_excel('DATA.xlsx', sheet_name='Sheet1')
    donnees['Date'] = pd.to_datetime(donnees['Date'])
    donnees["Cours"] = donnees["Cours Normal"]
    return donnees


try:
    data = charger_cours()
except FileNotFoundError:
    st.error(
        "Fichier 'DATA.xlsx' introuvable. Vérifie qu'il se trouve bien dans le même "
        "dossier que graph.py avant de relancer l'application."
    )
    st.stop()
except KeyError as erreur:
    st.error(
        f"Colonne manquante dans DATA.xlsx ({erreur}). Vérifie que le fichier contient "
        "bien les colonnes 'Date', 'Symbole' et 'Cours Normal'."
    )
    st.stop()

actions = sorted(data['Symbole'].unique())

# --- Correspondance entre les codes utilisés dans DATA.xlsx et les tickers officiels BRVM ---
# DATA.xlsx contient ses propres codes (ex: "TRACTAFRIC", "BOABC") qui ne correspondent
# pas aux tickers officiels utilisés dans le fichier Excel financier (ex: "PRSC", "BOAC").
# Ce dictionnaire fait le lien entre les deux. Clé = valeur dans DATA.xlsx, valeur = ticker Excel.
CORRESPONDANCE_SYMBOLES = {
    "AGL": "SDSC",
    "BERNABE_CI": "BNBC",
    "BICB": "BICB",
    "BICC": "BICC",
    "BOAB": "BOAB",
    "BOA_CI": "BOAC",
    "BOABF": "BOABF",
    "BOAM": "BOAM",
    "BOAN": "BOAN",
    "BOAS": "BOAS",
    "CFAO": "CFAC",
    "CIE": "CIEC",
    "CORIS_BANK": "CBIBF",
    "ECOBANK_CI": "ECOC",
    "ERIUM_CI": "SIVC",  # Air Liquide CI
    "ETIT": "ETIT",
    "FILTISAC": "FTSC",
    "LNBB": "LNBB",
    "NEICEDA": "NEIC",
    "NESTLE_CI": "NTLC",
    "NSIA": "NSBC",
    "ONATEL": "ONTBF",
    "ORAGROUP_TOGO": "ORGT",
    "ORANGE": "ORAC",
    "PALM_CI": "PALC",
    "SAFCA": "SAFC",
    "SAPH_CI": "SPHC",
    "SEMC": "SEMC",
    "SERVAIR": "ABJC",
    "SETAO": "STAC",
    "SGB_CI": "SGBC",
    "SIBC": "SIBC",
    "SICABLE": "CABC",
    "SICOR": "SICC",
    "SITAB_CI": "STBC",
    "SMBC": "SMBC",
    "SODECI": "SDCC",
    "SOGCB_CI": "SOGC",
    "SOLIBRA_CI": "SLBC",
    "SONATEL": "SNTS",
    "SURCRIVOIRE": "SCRC",
    "TOTAL_CI": "TTLC",
    "TOTAL_SN": "TTLS",
    "TRACTAFRIC": "PRSC",
    "UNILEVER_CI": "UNLC",
    "UNIWAX": "UNXC",
    "VIVO": "SHEC",
}


def vers_ticker_officiel(nom_action):
    """Traduit un code d'action tel qu'il apparaît dans DATA.xlsx vers son ticker officiel BRVM."""
    return CORRESPONDANCE_SYMBOLES.get(nom_action)


FICHIER_FINANCIER = 'Données CA - RN - DIV 2023-2025.xlsx'


def nettoyer_valeur_numerique(valeur):
    """Convertit une valeur en nombre, même si elle a été saisie comme texte avec des
    espaces comme séparateurs de milliers (espace normal ou espace fine insécable Unicode).
    Retourne NaN si la conversion échoue.
    """
    if isinstance(valeur, str):
        valeur_nettoyee = valeur.replace('\u202f', '').replace('\xa0', '').replace(' ', '')
        try:
            return float(valeur_nettoyee)
        except ValueError:
            return pd.NA
    return valeur


@st.cache_data
def charger_feuille_financiere(nom_feuille):
    """Lit une feuille du classeur financier et normalise ses colonnes.
    Les feuilles ont 2 lignes d'en-tête avant les vraies colonnes,
    d'où header=2. On repasse ensuite les colonnes en noms lisibles.
    """
    feuille = pd.read_excel(FICHIER_FINANCIER, sheet_name=nom_feuille, header=2)
    feuille.columns = ['Symbole', 'Societe', '2023', '2024', '2025']
    feuille = feuille.dropna(subset=['Symbole'])
    # Certaines valeurs sont saisies avec des espaces comme séparateurs de milliers
    # (ex: "257 218 000 000"), ce qui les fait lire comme du texte plutôt que des
    # nombres — on les convertit ici pour éviter les erreurs de calcul en aval.
    for colonne_annee in ['2023', '2024', '2025']:
        feuille[colonne_annee] = feuille[colonne_annee].apply(nettoyer_valeur_numerique)
        feuille[colonne_annee] = pd.to_numeric(feuille[colonne_annee], errors='coerce')
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


def generer_graphique_barres(annees, valeurs, titre, ylabel, type_graphique='bar'):
    """Génère un petit graphique (barres ou ligne) en image PNG pour l'insérer dans le PDF.
    Ignore les années sans valeur. Retourne None si aucune donnée n'est disponible.
    """
    donnees = [(a, v) for a, v in zip(annees, valeurs) if v is not None]
    if not donnees:
        return None

    annees_valides, valeurs_valides = zip(*donnees)

    fig, ax = plt.subplots(figsize=(7, 4))
    couleurs_barres = ["#c0392b" if v < 0 else "#0b3d2e" for v in valeurs_valides]
    if type_graphique == 'bar':
        ax.bar(annees_valides, valeurs_valides, color=couleurs_barres)
    else:
        ax.plot(annees_valides, valeurs_valides, color="#0b3d2e", marker='o', linewidth=2)
    ax.axhline(0, color="#999999", linewidth=0.8)
    ax.set_title(titre, fontsize=11)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(alpha=0.3, axis='y')

    tampon = io.BytesIO()
    fig.savefig(tampon, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    tampon.seek(0)
    return tampon


def generer_graphique_cours(df_action, action_choisie):
    """Génère un graphique des cours en image PNG (en mémoire) pour l'insérer dans le PDF."""
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.plot(df_action['Date'], df_action['Cours'], color="#0b3d2e", linewidth=1.5)
    ax.fill_between(df_action['Date'], df_action['Cours'], color="#0b3d2e", alpha=0.15)
    ax.set_title(f"Cours de {action_choisie}")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cours (FCFA)")
    ax.grid(alpha=0.3)
    fig.autofmt_xdate()

    tampon = io.BytesIO()
    fig.savefig(tampon, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    tampon.seek(0)
    return tampon


def generer_rapport_pdf(action_choisie, ticker, df_action):
    """Compile cours, indicateurs financiers et commentaires d'une action en un rapport PDF."""
    tampon_pdf = io.BytesIO()
    document = SimpleDocTemplate(
        tampon_pdf, pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle('TitreBRVM', parent=styles['Title'], textColor=colors.HexColor("#0b3d2e"))
    style_section = ParagraphStyle('SectionBRVM', parent=styles['Heading2'], textColor=colors.HexColor("#0b3d2e"))
    style_normal = styles['Normal']
    style_italique = ParagraphStyle('CommentaireBRVM', parent=styles['Italic'])

    elements = []

    # --- En-tête ---
    elements.append(Paragraph(f"Rapport BRVM — {action_choisie}", style_titre))
    date_generation = datetime.now().strftime("%d/%m/%Y à %H:%M")
    elements.append(Paragraph(f"Généré le {date_generation}", style_normal))
    elements.append(Spacer(1, 0.6 * cm))

    # --- Section cours ---
    elements.append(Paragraph("Évolution du cours", style_section))
    if not df_action.empty:
        dernier_cours = df_action.sort_values('Date').iloc[-1]
        elements.append(Paragraph(
            f"Dernier cours connu : {dernier_cours['Cours']:.0f} FCFA "
            f"({dernier_cours['Date'].strftime('%d/%m/%Y')})",
            style_normal,
        ))
        elements.append(Spacer(1, 0.3 * cm))
        graphique_cours = generer_graphique_cours(df_action, action_choisie)
        elements.append(Image(graphique_cours, width=16 * cm, height=6 * cm))
    else:
        elements.append(Paragraph("Aucune donnée de cours disponible pour la période sélectionnée.", style_normal))
    elements.append(Spacer(1, 0.6 * cm))

    # --- Section indicateurs financiers ---
    elements.append(Paragraph("Indicateurs financiers", style_section))

    if ticker is None:
        elements.append(Paragraph(
            f"'{action_choisie}' n'a pas de correspondance connue dans le fichier financier.",
            style_normal,
        ))
    else:
        annees = ['2023', '2024', '2025']
        donnees_tableau = [["Indicateur"] + annees]
        donnees_tableau.append(["Chiffre d'affaires (Md FCFA)"] + [
            f"{v / 1_000_000_000:.2f}" if (v := valeur_annee(ca, ticker, a)) is not None else "—" for a in annees
        ])
        donnees_tableau.append(["Résultat net (Md FCFA)"] + [
            f"{v / 1_000_000_000:.2f}" if (v := valeur_annee(resultat_net, ticker, a)) is not None else "—" for a in annees
        ])
        donnees_tableau.append(["Dividende par action (FCFA)"] + [
            f"{v:.0f}" if (v := valeur_annee(dividende, ticker, a)) is not None else "—" for a in annees
        ])
        donnees_tableau.append(["Marge nette (%)"] + [
            f"{v:.1f}" if (v := calculer_marge_nette_annee(ticker, a)) is not None else "—" for a in annees
        ])

        tableau = Table(donnees_tableau, hAlign='LEFT')
        tableau.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0b3d2e")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6f8")]),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(tableau)
        elements.append(Spacer(1, 0.5 * cm))

        # --- Graphiques des indicateurs ---
        valeurs_ca = [valeur_annee(ca, ticker, a) for a in annees]
        valeurs_ca_md = [v / 1_000_000_000 if v is not None else None for v in valeurs_ca]
        valeurs_rn = [valeur_annee(resultat_net, ticker, a) for a in annees]
        valeurs_rn_md = [v / 1_000_000_000 if v is not None else None for v in valeurs_rn]
        valeurs_marge = [calculer_marge_nette_annee(ticker, a) for a in annees]

        croissance_ca_df = calculer_croissance(ca, ticker)
        croissance_rn_df = calculer_croissance(resultat_net, ticker)
        annees_croissance = ['2024', '2025']
        valeurs_croissance_ca = [
            croissance_ca_df.set_index('Année')['croissance'].get(a) for a in annees_croissance
        ]
        valeurs_croissance_rn = [
            croissance_rn_df.set_index('Année')['croissance'].get(a) for a in annees_croissance
        ]

        graphiques = [
            (generer_graphique_barres(annees, valeurs_ca_md, "Chiffre d'affaires", "Md FCFA"), "CA"),
            (generer_graphique_barres(annees, valeurs_rn_md, "Résultat net", "Md FCFA"), "RN"),
            (generer_graphique_barres(annees_croissance, valeurs_croissance_ca, "Croissance du CA", "%"), "Croissance CA"),
            (generer_graphique_barres(annees_croissance, valeurs_croissance_rn, "Croissance du résultat net", "%"), "Croissance RN"),
            (generer_graphique_barres(annees, valeurs_marge, "Marge nette", "%", type_graphique='line'), "Marge nette"),
        ]
        graphiques = [(img, libelle) for img, libelle in graphiques if img is not None]

        # Disposition en grille de 2 colonnes via une Table (chaque cellule = une image)
        largeur_image, hauteur_image = 8 * cm, 4.6 * cm
        lignes_grille = []
        for i in range(0, len(graphiques), 2):
            paire = graphiques[i:i + 2]
            ligne_images = [Image(img, width=largeur_image, height=hauteur_image) for img, _ in paire]
            if len(ligne_images) == 1:
                ligne_images.append("")
            lignes_grille.append(ligne_images)

        if lignes_grille:
            grille = Table(lignes_grille, colWidths=[largeur_image + 0.3 * cm] * 2)
            grille.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(grille)
            elements.append(Spacer(1, 0.4 * cm))

        # --- Commentaires interprétatifs ---
        elements.append(Paragraph("Commentaires", style_section))
        croissance_ca = calculer_croissance(ca, ticker)
        if not croissance_ca.empty:
            commentaire = commenter_croissance(croissance_ca.iloc[-1]['croissance'], "du chiffre d'affaires")
            if commentaire:
                elements.append(Paragraph(commentaire, style_italique))

        croissance_rn = calculer_croissance(resultat_net, ticker)
        if not croissance_rn.empty:
            commentaire = commenter_croissance(croissance_rn.iloc[-1]['croissance'], "du résultat net")
            if commentaire:
                elements.append(Paragraph(commentaire, style_italique))

        derniere_marge = calculer_marge_nette_annee(ticker, '2025') or calculer_marge_nette_annee(ticker, '2024')
        commentaire_marge = commenter_marge_nette(derniere_marge)
        if commentaire_marge and derniere_marge is not None and -100 <= derniere_marge <= 100:
            elements.append(Paragraph(commentaire_marge, style_italique))

    document.build(elements)
    tampon_pdf.seek(0)
    return tampon_pdf


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
            "Cette action est peut-être mal renseignée à la source (DATA.xlsx)."
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

        # --- Rapport PDF ---
        st.divider()
        st.subheader("Rapport PDF")
        if st.button(f"Générer le rapport PDF de {action_choisie}"):
            with st.spinner("Génération du rapport en cours..."):
                pdf = generer_rapport_pdf(action_choisie, ticker_selectionne, df_action)
            st.download_button(
                label=f"Télécharger le rapport de {action_choisie} (PDF)",
                data=pdf,
                file_name=f"rapport_{action_choisie}.pdf",
                mime="application/pdf",
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