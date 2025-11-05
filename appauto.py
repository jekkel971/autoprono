import streamlit as st
import requests
import pandas as pd

# ---------------------------
# ⚙️ Configuration API
# ---------------------------
API_KEY = "94ab52893fe364d9bf5362dc7b752213"  # 🔑 Remplace par ta clé TheOddsAPI
REGION = "eu"
MARKET = "h2h"

# Dictionnaire des championnats
CHAMPIONNATS = {
    "🇫🇷 Ligue 1": "soccer_france_ligue_one",
    "🏴 Premier League": "soccer_epl",
    "🇪🇸 La Liga": "soccer_spain_la_liga"
}

# ---------------------------
# 🖥️ Interface Streamlit
# ---------------------------
st.set_page_config(page_title="Analyse Cotes 1.4 - 1.6", page_icon="⚽", layout="centered")

st.title("⚽ Analyse automatique des matchs (cotes entre 1.4 et 1.6)")
st.caption("Les données proviennent de TheOddsAPI. Sélectionne ton championnat et lance l’analyse !")

# Menu déroulant
championnat_nom = st.selectbox("Choisis un championnat :", list(CHAMPIONNATS.keys()))
SPORT = CHAMPIONNATS[championnat_nom]

# ---------------------------
# 🔘 Récupération des données
# ---------------------------
if st.button("Récupérer et analyser ⚡"):

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
                moyenne_cote_A = sum(toutes_cotes_A) / len(toutes_cotes_A)
                moyenne_cote_B = sum(toutes_cotes_B) / len(toutes_cotes_B)

                # 👉 Filtrer les cotes comprises entre 1.4 et 1.6
                if 1.4 <= moyenne_cote_A <= 1.6 or 1.4 <= moyenne_cote_B <= 1.6:
                    matchs.append({
                        "Equipe": equipeA,
                        "Adversaire": equipeB,
                        "Cote_moy_A": round(moyenne_cote_A, 2),
                        "Cote_moy_B": round(moyenne_cote_B, 2),
                        "Nb_bookmakers": len(match["bookmakers"])
                    })

        if not matchs:
            st.warning("⚠️ Aucun match trouvé avec des cotes entre 1.4 et 1.6.")
        else:
            df = pd.DataFrame(matchs)

            # ---------------------------
            # 📊 Analyse automatique
            # ---------------------------
            df["Probabilité_estimee_A"] = round((1 / df["Cote_moy_A"]) * 100, 1)
            df["Note_confiance"] = round(df["Probabilité_estimee_A"] / df["Cote_moy_A"], 1)
            df = df.sort_values(by="Note_confiance", ascending=False)
            df["Classement"] = range(1, len(df) + 1)

            # ---------------------------
            # 🎨 Affichage
            # ---------------------------
            st.success(f"✅ {len(df)} matchs trouvés avec des cotes entre 1.4 et 1.6 ({championnat_nom})")

            def color_rows(row):
                return ['background-color: #b6f0b6' if 1.4 <= row["Cote_moy_A"] <= 1.6 else 'background-color: #f4b6b6'] * len(row)

            st.dataframe(df[[
                "Classement","Equipe","Adversaire","Nb_bookmakers","Cote_moy_A","Cote_moy_B",
                "Probabilité_estimee_A","Note_confiance"
            ]].style.apply(color_rows, axis=1), use_container_width=True)

            # ---------------------------
            # 💾 Export CSV
            # ---------------------------
            st.download_button(
                "📥 Télécharger le tableau (CSV)",
                df.to_csv(index=False).encode("utf-8"),
                f"matchs_cotes_1_4_1_6_{championnat_nom.replace(' ', '_')}.csv",
                "text/csv"
            )



