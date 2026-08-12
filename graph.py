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

with st.container():
    st.markdown("Utiliser ce boutton pour charge votre data set")
    st.button("APPUYER ICI")