from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):

    """ Application Settings """

    app_name: str = "Zonecam"
    app_url:  str = "http://localhost:5173"
    db_name: str = "ZonecamDB"
    db_url: str = "mongodb://localhost:4000"
    debug:  bool = True

    # SECURITY
    allowed_origins: list = ["http://localhost:5173",
                             "https://zonecam.vercel.app"]
    code_duration:  int = 5 * 60
    code_length: int = 6
    password_salt: str = "*&^%&^#(*HD(*#&))"
    jwt_exp: int = 24
    jwt_secret: str = "$@^&@*(@*^&*HSIHW**^*(^*(^&*Y@*&Y()"
    key1: str = "key1"
    key2: str = "key2"

    # EMAIL SETUP CONFIG

    support_email: str = "landove@Landove.xyz"
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_port: int = 465
    mail_server:  str = ""
    mail_starttls: bool = False
    mail_ssl_tls:  bool = True
    mail_display_name: str = ""
    mail_domain:  str = ""
    mail_domain_username:  str = ""

    ml_model_path  :  str = ""

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings():
    return Settings()
