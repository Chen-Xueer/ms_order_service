from sqlalchemy import (
    QueuePool,
    create_engine,
    Engine,
    make_url,
    URL,
    exc,
)
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from typing import Dict, Optional
import boto3
import json
from dotenv import load_dotenv
import os
from microservice_utils.settings import logger

load_dotenv(".env", override=True)
      
master_sessionmakers: Dict[str, scoped_session[Session]] = {}

class Database:
    def __init__(self):
        #self.local_postgres = os.getenv('LOCAL_POSTGRES')
        self.region = os.getenv('AWS_REGION', "ap-southeast-1")
        #self.master_db_secret_name = os.getenv('MASTER_DB_SECRET_NAME')
        self.master_db_proxy = os.getenv('MASTER_DB_PROXY')
        self.master_db_name = os.getenv('MASTER_DB_NAME')
        self.secrets_client = boto3.client("secretsmanager", region_name=self.region)

    def _get_db_secrets(self):
        secret_response = self.secrets_client.get_secret_value(SecretId=self.master_db_secret_name)
        secrets = json.loads(secret_response["SecretString"])
        return secrets

    def get_database_url(self) -> URL:
            db_proxy_endpoint = self.master_db_proxy
            db_name = self.master_db_name
            db_url: URL = make_url(f"postgresql://***:***@{db_proxy_endpoint}:5432/{db_name}?sslmode=require")

            #secrets = self._get_db_secrets()
            #db_url = db_url._replace(
            #        username=secrets["username"],
            #        password=secrets["password"],
            #        port=secrets["port"],
            #    )
            
            db_url = db_url._replace(
                    username=os.getenv('MASTER_DB_USERNAME'),
                    password=os.getenv('MASTER_DB_PASSWORD'),
                    port=os.getenv('MASTER_DB_PORT'),
            )

            return db_url.render_as_string(hide_password=False)

    def _create_sessionmaker(self,db_url: URL) -> scoped_session[Session]:
        engine: Engine = create_engine(
            db_url,
            poolclass=QueuePool,
            echo=False,
            pool_size=20,
            max_overflow=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            pool_use_lifo=True
        )

        _sessionmaker = scoped_session(sessionmaker(bind=engine, expire_on_commit=True))
        return _sessionmaker

    def init_session(self) -> Session:
        global master_sessionmakers

        try:
            #_sessionmaker = self._create_sessionmaker(self.local_postgres)
            _sessionmaker = self._create_sessionmaker(self.get_database_url())
            master_sessionmakers[self.master_db_name] = _sessionmaker
            return master_sessionmakers[self.master_db_name]
        except exc.OperationalError as e:
            logger.error(f"Error connecting to database: {e}")
            raise
        except exc.ProgrammingError as e:
            logger.error(f"Database schema error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in init_session: {e}")
            raise

    def rollback_session(self) -> None:
        global master_sessionmakers
        
        session = master_sessionmakers[self.master_db_name]()
        session.rollback()

    def remove_session(self) -> None:
        global master_sessionmakers
        
        master_sessionmakers[self.master_db_name].remove()