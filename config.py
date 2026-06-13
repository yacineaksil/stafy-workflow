import os

class Config:
    # --- API Keys (set via environment variables) ---
    API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
    ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")

    # --- API Base URLs ---
    API_FOOTBALL_BASE = "https://v3.football.api-sports.io"
    MLB_STATS_BASE = "https://statsapi.mlb.com/api/v1"
    BALLDONTLIE_BASE = "https://api.balldontlie.io/v1"
    ODDS_API_BASE = "https://api.the-odds-api.com/v4"

    # --- Betting Strategy ---
    MIN_EV_THRESHOLD = 0.03    # 3% EV minimum pour recommander un pari
    KELLY_FRACTION = 4          # Kelly fractionné (diviser par 4 = plus sûr)
    DEFAULT_BANKROLL = 1000.0  # Bankroll par défaut en €

    # --- Sports Odds API identifiers ---
    ODDS_SPORTS = {
        "football": "soccer_france_ligue1",     # à personnaliser selon ligue
        "mlb": "baseball_mlb",
        "basketball": "basketball_nba",
    }

    # --- Bookmakers cibles (1xBet en priorité) ---
    BOOKMAKER_PRIORITY = ["onexbet", "pinnacle", "betfair_ex_eu", "bet365"]

    # --- Cache ---
    CACHE_DIR = "data/cache"
    CACHE_TTL = 1800  # 30 minutes
