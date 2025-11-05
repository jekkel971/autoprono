import streamlit as st
import requests
import pandas as pd

# ---------------------------
# ⚙️ Configuration API
# ---------------------------
API_KEY = "TA_CLE_API_ICI"  # 🔑 Remplace par ta clé TheOddsAPI
REGION = "eu"               # Marché européen
MARKET = "h2h"              # Marché : 1X2 (Head to Head)

# Dictionnaire des championnats disponibles
CHAMPIONNATS = {
    "🇫🇷 Ligue 1": "soccer_france_ligue_one",
    "🏴 Premier League": "soccer_epl",
    "🇪🇸 La Liga": "soccer_spain_la_liga"
}

# ---------------------------
# 🖥️ Interface Streamlit
# ---------------------------
st.set_page_config(page_title="Analyse Multi-Championnats", page_icon="⚽", layout="centered")

st.title("⚽ Analyse automatique des matchs et cotes (multi-championnats)")
st.caption("Les données proviennent de TheOddsAPI. Sélectionne ton championnat et lance l’analyse !")

# Menu déroulant
championnat_nom = st.selectbox("Choisis un championnat :", list(CHAMPIONNATS.keys()))
SPORT = CHAMPIONNATS[championnat_nom]

# ---------------------------
# 🔘 Récupération des données
# ---------------------------
if st.button("Récupérer les matchs et analyser ⚡"):

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions={REGION}&markets={MARKET}"
    response = requests.get(url)

    if response.status_code != 200:
        st.error(f"Erreur API : {response.status_code} - {response.text}")
    else:
        data = response.json()
        matchs = []

        for match in data:
            equipeA = match["home_team"]
            equipeB = match["away_team"]
            toutes_cotes_A = []
            toutes_cotes_B = []

            # Parcourir les bookmakers disponibles
            for bookmaker in match["bookmakers"]:
                try:
                    outcomes = bookmaker["markets"][0]["outcomes"]
                    for outcome in outcomes:
                        if outcome["name"] == equipeA:
                            toutes_cotes_A.append(outcome["price"])
                        elif outcome["name"] == equipeB:
                            toutes_cotes_B.append(outcome["price"])
                except Exception:
                    continue

            if toutes_cotes_A and toutes_cotes_B:
                meilleure_cote_A = max(toutes_cotes_A)
                meilleure_cote_B = max(toutes_cotes_B)
                moyenne_cote_A = sum(toutes_cotes_A) / len(toutes_cotes_A)
                moyenne_cote_B = sum(toutes_cotes_B) / len(toutes_cotes_B)
                nb_bookmakers = len(match["bookmakers"])

                matchs.append({
                    "Equipe": equipeA,
                    "Adversaire": equipeB,
                    "Nb_bookmakers": nb_bookmakers,
                    "Cote_max_A": round(meilleure_cote_A, 2),
                    "Cote_max_B": round(meilleure_cote_B, 2),
                    "Cote_moy_A": round(moyenne_cote_A, 2),
                    "Cote_moy_B": round(moyenne_cote_B, 2)
                })

        if not matchs:
            st.warning(f"Aucun match trouvé pour {championnat_nom}. Essaie un autre championnat.")
        else:
            df = pd.DataFrame(matchs)

            # ---------------------------
            # 📊 Analyse automatique
            # ---------------------------
            df["Probabilité_estimee_A"] = round((1 / df["Cote_moy_A"]) * 100, 1)
            df["Note_confiance_A"] = round(df["Probabilité_estimee_A"] / df["Cote_moy_A"], 1)
            df["Recommandation"] = df["Probabilité_estimee_A"].apply(lambda x: "✅ Oui" if x >= 70 else "❌ Non")

            df = df.sort_values(by="Note_confiance_A", ascending=False)
            df["Classement"] = range(1, len(df)+1)

            # ---------------------------
            # 🎨 Affichage
            # ---------------------------
            st.success(f"✅ Analyse terminée pour {championnat_nom} ! Voici les matchs les plus sûrs :")

            def color_rows(row):
                return ['background-color: #b6f0b6' if row["Recommandation"] == "✅ Oui" else 'background-color: #f4b6b6']*len(row)

            st.dataframe(df[[
                "Classement","Equipe","Adversaire","Nb_bookmakers",
                "Cote_max_A","Cote_moy_A","Probabilité_estimee_A","Note_confiance_A","Recommandation"
            ]].style.apply(color_rows, axis=1), use_container_width=True)

            # ---------------------------
            # 💾 Export CSV
            # ---------------------------
            st.download_button(
                "📥 Télécharger les résultats en CSV",
                df.to_csv(index=False).encode("utf-8"),
                f"classement_{championnat_nom.replace(' ', '_')}.csv",
                "text/csv"
            )

            st.caption("Analyse basée sur la moyenne et la meilleure cote disponible parmi les bookmakers.")
