import shutil
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.dependencies import get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+psycopg://atlas:atlas_dev_password@localhost:5432/atlas"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)



@pytest.fixture(scope="function")
def db_session():
    # Establish a connection and start a transaction block
    connection = engine.connect()
    transaction = connection.begin()
    
    # Bind the session to the transaction
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session  # This is provided directly to the test function
    
    # Teardown: Close the session and completely roll back changes made by the test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session, tmp_path):
    settings.storage_dir = str(tmp_path)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    app.dependency_overrides.clear()

