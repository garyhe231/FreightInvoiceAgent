from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./freight_invoice.db"
    CLAUDE_API_KEY: str = ""
    COMPANY_NAME: str = "Pacific Freight Solutions Inc."
    COMPANY_ADDRESS: str = "1200 Harbor Blvd, Suite 300, Long Beach, CA 90802"
    COMPANY_PHONE: str = "+1 (562) 555-0188"
    COMPANY_EMAIL: str = "billing@pacificfreight.com"

    class Config:
        env_file = ".env"


settings = Settings()
