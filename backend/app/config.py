import os


class Settings:
    database_url: str = os.environ.get(
        "DATABASE_URL", "postgresql://oktoberfest:oktoberfest@db:5432/oktoberfest"
    )
    session_secret: str = os.environ.get("SESSION_SECRET", "change-me-in-production")


settings = Settings()
