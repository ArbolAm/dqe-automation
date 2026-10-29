import pytest
from data_dev.config import postgres_config
from src.connectors.file_system.parquet_reader import ParquetReader
from src.connectors.postgres.postgres_connector import PostgresConnectorContextManager
from src.data_quality.data_quality_validation_library import DataQualityLibrary


def pytest_addoption(parser):
    parser.addoption("--db_host", action="store", default=postgres_config.host)
    parser.addoption("--db_port", action="store", type=int, default=postgres_config.port)
    parser.addoption("--db_name", action="store", default=postgres_config.db)
    parser.addoption("--db_user", action="store", default=postgres_config.user)
    parser.addoption("--db_password", action="store", default=postgres_config.password)

def pytest_configure(config):
    required_options = ("db_host", "db_port", "db_name", "db_user", "db_password")
    for option in required_options:
        if not config.getoption(option):
            pytest.fail(f"Missing database configuration value: {option}")

@pytest.fixture(scope='session')
def db_connection(request):
    try:
        with PostgresConnectorContextManager(
            db_user=request.config.getoption("db_user"),
            db_password=request.config.getoption("db_password"),
            db_host=request.config.getoption("db_host"),
            db_name=request.config.getoption("db_name"),
            db_port=request.config.getoption("db_port"),
        ) as db_connector:
            yield db_connector
    except Exception as e:
        pytest.fail(f"Failed to initialize PostgresConnectorContextManager: {e}")

@pytest.fixture(scope='session')
def parquet_reader():
    return ParquetReader()


@pytest.fixture(scope='session')
def data_quality_library():
    return DataQualityLibrary()