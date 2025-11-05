import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------
# ⚙️ Config API
# ---------------------------
API_KEY = "94ab52893fe364d9bf5362dc7b752213"  # Remplace par ta clé TheOddsAPI
REGION = "eu"
MARKET = "h2h"

CHAMPIONNATS = {
    "🇫🇷 Ligue 1": "soccer_france_ligue_one",
    "🏴 Premier League": "soccer_epl",
    "🇪🇸 La Liga": "soccer_spain_la_liga"
}

# ---------------------------
# 🖥️ Interface
# ---------------------------
st.set_page_config(page_title="Top matchs safe du week-end", page_icon="⚽", layout="centered")
st.title("⚽ Analyse automatique : matchs safe du week-end")
st.caption("Basée sur TheOddsAPI — Ligue 1, Premier League, La Liga")

# ---------------------------
# 🔘 Lancer l'analyse
# ---------------------------
if st.button("Analyser les 3 championnats ⚡"):

    matchs_total = []
    weekend_start = datetime.now()
    weekend_end = weekend_start + timedelta(days=7)

    for nom, sport in CHAMPIONNATS.items():
        st.info(f"🔎 Analyse de {nom}...")
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={API_KEY}&regions={REGION}&markets={MARKET}"
        response = requests.get(url)

        if response.status_code != 200:
            st.warning(f"Erreur API pour {nom} ({response.status_code})")
            continue

        data = response.json()

        for match in data:
            try:
                # Vérifie si le match est dans les 7 prochains jours
                match_time = datetime.fromisoformat(match["commence_at"].replace("Z", "+00:00"))
                if not (weekend_start <= match_time <= weekend_end):
                    continue

                equipeA = match["home_team"]
                equipeB = match["away_team"]
                cotes = {}

                for bookmaker in match["bookmakers"]:
                    for outcome in bookmaker["markets"][0]["outcomes"]:
                        cotes[outcome["name"]] = cotes.get(outcome["name"], []) + [outcome["price"]]

                if equipeA in cotes and equipeB in cotes:
                    coteA = sum(cotes[equipeA]) / len(cotes[equipeA])
                    coteB = sum(cotes[equipeB]) / len(cotes[equipeB])

                    # Filtrage cotes entre 1.4 et 1.6
                    if 1.4 <= coteA <= 1.6 or 1.4 <= coteB <= 1.6:
                        winner = equipeA if coteA < coteB else equipeB
                        cote_winner = min(coteA, coteB)
                        prob = round((1 / cote_winner) * 100, 1)
                        confiance = round(prob / cote_winner, 1)

                        matchs_total.append({
                            "Championnat": nom,
                            "Match": f"{equipeA} vs {equipeB}",
                            "Winner": winner,
                            "Cote": round(cote_winner, 2),
                            "Probabilité": prob,
                            "Confiance": confiance,
                            "Date": match_time.strftime("%d/%m %Hh")
                        })
            except Exception:
                continue

    # ---------------------------
    # 📊 Résultats globaux
    # ---------------------------
    if not matchs_total:
        st.warning("Aucun match trouvé avec cotes entre 1.4 et 1.6 pour le week-end à venir.")
    else:
        df = pd.DataFrame(matchs_total)
        df = df.sort_values(by="Confiance", ascending=False)
        top_df = df.head(4)

        st.success("✅ Voici les matchs les plus safe du week-end :")
        st.dataframe(top_df, use_container_width=True)

        st.download_button(
            "📥 Télécharger les résultats (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            "matchs_safe_weekend.csv",
            "text/csv"
        )
