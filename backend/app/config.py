from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # backend/.env 에서 로드(대소문자 무시). 정의 안 한 키는 무시.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # docker-compose.yml의 POSTGRES_USER/PASSWORD/DB와 값 일치.
    # ponytail: psycopg2-binary는 Windows 비영문 로케일에서 libpq 에러메시지가
    # UTF-8로 디코드 안 되는 버그가 있다(모든 연결오류가 UnicodeDecodeError로 뜸).
    # asyncpg도 libpq를 쓰지 않고 PG 와이어 프로토콜을 직접 구현해 같은 버그를
    # 원천 회피한다 — 그래서 async 전환 후에도 그대로 asyncpg를 쓴다.
    database_url: str = (
        "postgresql+asyncpg://exitguard:exitguard@localhost:5433/exitguard"
    )

    @property
    def is_test_db(self) -> bool:
        """DB 이름이 `_test`로 끝나는가 — 테스트가 개발 DB를 잘못 가리키는 사고 차단용 가드."""
        return self.database_url.rsplit("/", 1)[-1].endswith("_test")


settings = Settings()
