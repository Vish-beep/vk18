
from flask import Flask, render_template, request
import pandas as pd

from analysis.league_analysis import calculate_league_table
from analysis.team_analysis import analyze_team
from analysis.match_analysis import analyze_match
from analysis.player_analysis import analyze_players
from auth import init_auth

app = Flask(__name__)
init_auth(app)  # login / register / logout + page protection

DATA_PATH = "data/matches.csv"
PLAYER_DATA_PATH = "data/players.csv"


# ==========================================
# HOME PAGE
# ==========================================
@app.route("/")
def home():
    return render_template("home.html")


# ==========================================
# LEAGUE ANALYSIS
# ==========================================
@app.route("/league")
def league():
    try:
        selected_league = request.args.get("league", "").strip()
        selected_season = request.args.get("season", "").strip()

        df = pd.read_csv(DATA_PATH)

        leagues = (
            sorted(df["League"].dropna().astype(str).unique().tolist())
            if "League" in df.columns else []
        )
        seasons = (
            sorted(df["Season"].dropna().astype(str).unique().tolist(),
                   reverse=True)
            if "Season" in df.columns else []
        )

        if selected_league and "League" not in df.columns:
            raise ValueError("Match CSV has no League column.")
        if selected_season and "Season" not in df.columns:
            raise ValueError("Match CSV has no Season column.")

        table = calculate_league_table(
            DATA_PATH,
            league=selected_league or None,
            season=selected_season or None
        )

        return render_template(
            "league.html",
            table=table.to_dict(orient="records"),
            leagues=leagues,
            seasons=seasons,
            selected_league=selected_league,
            selected_season=selected_season
        )

    except FileNotFoundError:
        return "Match CSV not found: data/matches.csv", 404
    except ValueError as error:
        return f"League analysis error: {error}", 400


# ==========================================
# TEAM ANALYSIS
# ==========================================
@app.route("/team")
def team_page():
    try:
        selected_team = request.args.get("team", "").strip()
        selected_league = request.args.get("league", "").strip()
        selected_season = request.args.get("season", "").strip()

        df = pd.read_csv(DATA_PATH)

        required = ["HomeTeam", "AwayTeam"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing match CSV columns: {missing}")

        teams = sorted(
            set(df["HomeTeam"].dropna().astype(str))
            | set(df["AwayTeam"].dropna().astype(str))
        )
        leagues = (
            sorted(df["League"].dropna().astype(str).unique().tolist())
            if "League" in df.columns else []
        )
        seasons = (
            sorted(df["Season"].dropna().astype(str).unique().tolist(),
                   reverse=True)
            if "Season" in df.columns else []
        )

        if selected_league and "League" not in df.columns:
            raise ValueError("Match CSV has no League column.")
        if selected_season and "Season" not in df.columns:
            raise ValueError("Match CSV has no Season column.")

        summary = None
        matches = []
        recent_matches = []

        if selected_team:
            if selected_team not in teams:
                raise ValueError("Selected team was not found in the CSV.")

            result = analyze_team(
                DATA_PATH,
                selected_team,
                league=selected_league or None,
                season=selected_season or None
            )
            summary = result["summary"]
            matches = result["matches"]
            recent_matches = result["recent_matches"]

        return render_template(
            "team.html",
            teams=teams,
            leagues=leagues,
            seasons=seasons,
            selected_team=selected_team,
            selected_league=selected_league,
            selected_season=selected_season,
            summary=summary,
            matches=matches,
            recent_matches=recent_matches
        )

    except FileNotFoundError:
        return "Match CSV not found: data/matches.csv", 404
    except ValueError as error:
        return f"Team analysis error: {error}", 400


# ==========================================
# MATCH ANALYSIS
# ==========================================
@app.route("/match")
def match_page():
    try:
        selected_home = request.args.get("home", "").strip()
        selected_away = request.args.get("away", "").strip()
        selected_league = request.args.get("league", "").strip()
        selected_season = request.args.get("season", "").strip()

        df = pd.read_csv(DATA_PATH)

        required = ["HomeTeam", "AwayTeam"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing match CSV columns: {missing}")

        teams = sorted(
            set(df["HomeTeam"].dropna().astype(str))
            | set(df["AwayTeam"].dropna().astype(str))
        )
        leagues = (
            sorted(df["League"].dropna().astype(str).unique().tolist())
            if "League" in df.columns else []
        )
        seasons = (
            sorted(df["Season"].dropna().astype(str).unique().tolist(),
                   reverse=True)
            if "Season" in df.columns else []
        )

        if selected_league and "League" not in df.columns:
            raise ValueError("Match CSV has no League column.")
        if selected_season and "Season" not in df.columns:
            raise ValueError("Match CSV has no Season column.")

        history = []
        match_details = []
        searched = bool(selected_home and selected_away)

        if searched:
            if selected_home not in teams or selected_away not in teams:
                raise ValueError("One or both selected teams were not found.")
            if selected_home == selected_away:
                raise ValueError("Choose two different teams.")

            result = analyze_match(
                DATA_PATH,
                selected_home,
                selected_away,
                league=selected_league or None,
                season=selected_season or None
            )
            history = result["history"]
            match_details = result["match_details"]

        return render_template(
            "match.html",
            teams=teams,
            leagues=leagues,
            seasons=seasons,
            selected_home=selected_home,
            selected_away=selected_away,
            selected_league=selected_league,
            selected_season=selected_season,
            history=history,
            match_details=match_details,
            searched=searched
        )

    except FileNotFoundError:
        return "Match CSV not found: data/matches.csv", 404
    except ValueError as error:
        return f"Match analysis error: {error}", 400


# ==========================================
# PLAYER ANALYSIS
# ==========================================
@app.route("/players")
def players_page():
    try:
        selected_league = request.args.get("league", "").strip()
        selected_season = request.args.get("season", "").strip()
        selected_team = request.args.get("team", "").strip()

        df = pd.read_csv(PLAYER_DATA_PATH)

        required = ["Player", "Team", "Goals", "Assists"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing player CSV columns: {missing}")

        teams = sorted(df["Team"].dropna().astype(str).unique().tolist())
        leagues = (
            sorted(df["League"].dropna().astype(str).unique().tolist())
            if "League" in df.columns else []
        )
        seasons = (
            sorted(df["Season"].dropna().astype(str).unique().tolist(),
                   reverse=True)
            if "Season" in df.columns else []
        )

        if selected_league and "League" not in df.columns:
            raise ValueError("Player CSV has no League column.")
        if selected_season and "Season" not in df.columns:
            raise ValueError("Player CSV has no Season column.")
        if selected_team and selected_team not in teams:
            raise ValueError("Selected team was not found in the player CSV.")

        players_df = analyze_players(
            PLAYER_DATA_PATH,
            league=selected_league or None,
            season=selected_season or None,
            team=selected_team or None
        )

        columns = players_df.columns.tolist()

        # Make missing numeric values JSON-safe for Chart.js.
        players_df = players_df.astype(object).where(
            pd.notna(players_df), None
        )
        player_records = players_df.to_dict(orient="records")

        return render_template(
            "players.html",
            players=player_records,
            columns=columns,
            teams=teams,
            leagues=leagues,
            seasons=seasons,
            selected_team=selected_team,
            selected_league=selected_league,
            selected_season=selected_season
        )

    except FileNotFoundError:
        return "Player CSV not found: data/players.csv", 404
    except ValueError as error:
        return f"Player analysis error: {error}", 400


# ==========================================
# DASHBOARD
# ==========================================
@app.route("/dashboard")
def dashboard():
    try:
        df = pd.read_csv(DATA_PATH)

        required = ["HomeTeam", "AwayTeam", "FTHG", "FTAG"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing match CSV columns: {missing}")

        df["FTHG"] = pd.to_numeric(df["FTHG"], errors="coerce")
        df["FTAG"] = pd.to_numeric(df["FTAG"], errors="coerce")

        valid = df.dropna(
            subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"]
        ).copy()

        valid = valid[
            (valid["FTHG"] >= 0)
            & (valid["FTAG"] >= 0)
            & (valid["FTHG"] % 1 == 0)
            & (valid["FTAG"] % 1 == 0)
        ]

        total_matches = len(valid)

        total_teams = len(
            set(valid["HomeTeam"].astype(str))
            | set(valid["AwayTeam"].astype(str))
        )

        total_leagues = (
            df["League"].nunique()
            if "League" in df.columns else 0
        )

        home_goals = int(valid["FTHG"].sum())
        away_goals = int(valid["FTAG"].sum())

        # Player statistics come from the separate player-level CSV.
        try:
            player_df = pd.read_csv(PLAYER_DATA_PATH)

            if "Player" not in player_df.columns:
                raise ValueError("Player CSV must contain a Player column.")

            total_players = player_df["Player"].nunique()

            if "Goals" in player_df.columns:
                player_df["Goals"] = pd.to_numeric(
                    player_df["Goals"], errors="coerce"
                )

                top_players = (
                    player_df.dropna(subset=["Player", "Goals"])
                    .groupby("Player", as_index=False)["Goals"]
                    .sum()
                    .sort_values(
                        ["Goals", "Player"],
                        ascending=[False, True]
                    )
                    .head(10)
                )

                player_names = top_players["Player"].tolist()
                player_goals = top_players["Goals"].tolist()
            else:
                player_names = []
                player_goals = []

        except FileNotFoundError:
            total_players = 0
            player_names = []
            player_goals = []

        return render_template(
            "dashboard.html",
            total_matches=total_matches,
            total_teams=total_teams,
            total_leagues=total_leagues,
            total_players=total_players,
            home_goals=home_goals,
            away_goals=away_goals,
            player_names=player_names,
            player_goals=player_goals
        )

    except FileNotFoundError:
        return "Match CSV not found: data/matches.csv", 404
    except ValueError as error:
        return f"Dashboard error: {error}", 400


# ==========================================
# RUN APPLICATION
# ==========================================
if __name__ == "__main__":
    app.run(debug=True)
