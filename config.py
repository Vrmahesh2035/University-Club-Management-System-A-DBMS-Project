import os

class Config:
    # ── MySQL connection ──────────────────────────────────────────
    MYSQL_HOST     = os.getenv("MYSQL_HOST",     "localhost")
    MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "port"))
    MYSQL_USER     = os.getenv("MYSQL_USER",     "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")          # change to your password
    MYSQL_DB       = os.getenv("MYSQL_DB",       "university_club_db")

    SECRET_KEY     = os.getenv("SECRET_KEY",     "ucms-secret-key-2025")
    DEBUG          = True
