from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # backend/.env 에서 로드(대소문자 무시). 정의 안 한 키는 무시.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # docker-compose.yml의 POSTGRES_USER/PASSWORD/DB와 값 일치.
    # ponytail: psycopg2-binary는 Windows 비영문 로케일에서 libpq 에러메시지가
    # UTF-8로 디코드 안 되는 버그가 있어(모든 연결오류가 UnicodeDecodeError로 뜸) pg8000(순수
    # Python 드라이버)으로 우회. 리눅스 배포 시엔 psycopg2로 되돌려도 무방.
    database_url: str = "postgresql+pg8000://exitguard:exitguard@localhost:5433/exitguard"


settings = Settings()
