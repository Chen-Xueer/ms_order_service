import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from flask_app.database_sessions import Database


def test_get_database_url():
    db = Database()
    # Replace with your actual test
    assert db.get_database_url() is not None

def test_create_sessionmaker():
    db = Database()
    # Replace with your actual test
    assert db._create_sessionmaker("postgresql://username:password@localhost:5432/dbname") is not None

def test_init_session():
    db = Database()
    # Replace with your actual test
    assert db.init_session() is not None

def test_rollback_session():
    db = Database()
    # Replace with your actual test
    assert db.rollback_session() is None

def test_remove_session():
    db = Database()
    # Replace with your actual test
    assert db.remove_session() is None