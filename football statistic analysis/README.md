# ⚽ Football Analytics

A Flask web application for exploring football statistics. Load match and player
data from CSV files and get league tables, team form, head-to-head records and
player leaderboards in a clean, responsive dashboard with light and dark themes.
Includes user registration and login to protect the analysis pages.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)
![pandas](https://img.shields.io/badge/pandas-2.x-150458)
![License](https://img.shields.io/badge/License-MIT-green)

<!--
  Add screenshots after running the app, then uncomment:

  ![Dashboard](docs/screenshots/dashboard.png)
  ![League table](docs/screenshots/league.png)
-->

## Features

| Page | Route | What it shows |
|------|-------|---------------|
| **Home** | `/` | Landing page with links to every analysis (public) |
| **Register / Sign in** | `/register`, `/login` | Create an account or sign in with username or email |
| **Dashboard** | `/dashboard` | Totals for matches, teams, leagues and players; home vs away goals; top scorers |
| **League Analysis** | `/league` | Full standings (points, goal difference, GF/GA) with sortable columns and team search |
| **Team Analysis** | `/team` | Record, goals, clean sheets, win rate, last five results, results chart and full match history |
| **Match Analysis** | `/match` | Head-to-head history between two teams plus shots, corners and cards when present in the data |
| **Player Analysis** | `/players` | Goals, assists, appearances and per-90 rates with leaderboard charts and live search |

Other highlights:

- **User accounts**: registration, login, logout, "keep me signed in", password strength meter
- Optional **League** and **Season** filters on every analysis page
- **Light / dark theme** toggle that remembers your choice
- Sortable and searchable tables, interactive [Chart.js](https://www.chartjs.org/) charts
- Fully responsive layout built on [Bootstrap 5](https://getbootstrap.com/)
- Analysis logic is separated from the web layer, so each module can also be run on its own

## Tech Stack

- **Backend:** Python, Flask, pandas
- **Frontend:** Jinja2 templates, Bootstrap 5, Bootstrap Icons, Chart.js, vanilla JavaScript

## Project Structure

```
football-analytics/
├── app.py                  # Flask app and routes
├── auth.py                 # Registration, login, logout, sessions, CSRF
├── check_data.py           # Quick script to inspect data/matches.csv
├── requirements.txt
├── analysis/
│   ├── league_analysis.py  # League table calculation
│   ├── team_analysis.py    # Team summary, form and history
│   ├── match_analysis.py   # Head-to-head and match statistics
│   └── player_analysis.py  # Player statistics and per-90 rates
├── data/
│   ├── matches.csv         # Match results (sample data)
│   └── players.csv         # Player statistics (sample data)
├── templates/
│   ├── base.html           # Shared layout, navbar and footer
│   ├── home.html
│   ├── dashboard.html
│   ├── league.html
│   ├── team.html
│   ├── match.html
│   ├── players.html
│   ├── login.html
│   ├── register.html
│   └── upload.html
├── static/
│   ├── css/style.css       # Theme and component styles
│   └── js/main.js          # Theme toggle, table sorting/search, chart helpers
├── instance/               # Created at first run: users.db + secret key (git-ignored)
└── uploads/
```

## Getting Started

### Prerequisites

- Python 3.10 or newer

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

# 2. (Recommended) create and activate a virtual environment
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the app

```bash
python app.py
```

Then open <http://127.0.0.1:5000> in your browser.

> The pages load Bootstrap, Chart.js and Google Fonts from a CDN, so an internet
> connection is needed the first time they are fetched.

## Authentication

Visitors can create an account at `/register` and sign in at `/login`. The home
page is public; the dashboard and all analysis pages require a signed-in user and
redirect to the login page otherwise.

- Accounts are stored in a local **SQLite** database (`instance/users.db`), created automatically on first run
- Passwords are **hashed** (Werkzeug scrypt) and never stored in plain text
- Forms are protected with **CSRF tokens**; sign-out is a POST request
- Sessions use `HttpOnly` / `SameSite=Lax` cookies; the post-login redirect only allows on-site paths
- No extra dependencies: it uses Flask, Werkzeug and Python's built-in `sqlite3`

**Secret key.** A random key is generated on first run and saved in
`instance/secret_key` (git-ignored). For deployment, set your own instead:

```bash
# macOS / Linux
export FLASK_SECRET_KEY="a-long-random-string"
# Windows (PowerShell)
$env:FLASK_SECRET_KEY="a-long-random-string"
```

**Keep the analysis pages public?** Add `app.config["REQUIRE_LOGIN"] = False`
before the `init_auth(app)` line in `app.py`. Login and registration keep working.

> This is suitable for a personal or demo project. For a production deployment, run
> behind HTTPS (set `SESSION_COOKIE_SECURE = True`), use a production server such as
> Gunicorn instead of `debug=True`, and consider adding rate limiting and email verification.

## Data Format

The app reads two CSV files from the `data/` folder.

### `data/matches.csv`

| Column | Required | Description |
|--------|:--------:|-------------|
| `Date` | ✅ (team & match pages) | Match date, `dd/mm/yyyy` |
| `HomeTeam` | ✅ | Home team name |
| `AwayTeam` | ✅ | Away team name |
| `FTHG` | ✅ | Full-time home goals |
| `FTAG` | ✅ | Full-time away goals |
| `League` | optional | Enables the league filter |
| `Season` | optional | Enables the season filter |
| `HS`/`AS`, `HST`/`AST`, `HC`/`AC`, `HY`/`AY`, `HR`/`AR` | optional | Shots, shots on target, corners, yellow and red cards (home/away) shown on the match page |

Any extra columns (for example betting odds from [football-data.co.uk](https://www.football-data.co.uk/data.php)) are ignored.

### `data/players.csv`

| Column | Required | Description |
|--------|:--------:|-------------|
| `Player` | ✅ | Player name |
| `Team` | ✅ | Team name |
| `Goals` | ✅ | Goals scored |
| `Assists` | ✅ | Assists |
| `League`, `Season` | optional | Enable filters |
| `Position`, `Appearances`, `Minutes`, `YellowCards`, `RedCards` | optional | Extra stats; `Minutes` also enables Goals/90 and Assists/90 |

> The files in `data/` are **sample data** for demonstration. Replace them with
> your own CSVs that follow the format above.

## Running the Analysis Modules Directly

Each analysis module has a small command-line demo:

```bash
python check_data.py                      # inspect matches.csv
python analysis/league_analysis.py        # print a league table
python analysis/match_analysis.py         # print head-to-head output
python analysis/player_analysis.py        # print player stats
```

> Run these from the project root so the relative `data/` paths resolve.

## Contributing

Issues and pull requests are welcome. For larger changes, please open an issue
first to discuss what you would like to change.

## License

Released under the [MIT License](LICENSE).

## Author

**Vishruth** — [GitHub](https://github.com/Vish-beep) · [LinkedIn](https://www.linkedin.com/in/vishruth-i-n-676808327)
