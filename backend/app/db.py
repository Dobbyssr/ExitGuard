from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def init_db() -> None:
    """앱 startup에서 호출. 지금은 도메인 모델이 없어 빈 메타데이터로 create_all만 배선."""
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
