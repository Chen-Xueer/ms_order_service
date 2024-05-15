import os
from microservice_utils.settings import logger
import threading
from dotenv import load_dotenv


if __name__ == "__main__":
    # Get environemnt status
    load_dotenv(".env")
    env = os.getenv("ENV", None)
    if env is None:
        raise ValueError("Environment not set")

    # Load environment variables from the appropriate .env file
    load_dotenv(f".env.{env}")

    logger.info("Starting database session")
    from database_sessions import init_session

    init_session()

    logger.info("Starting kafka connection")
    from kafka_app import app_init

    threading.Thread(target=app_init).start()

    logger.info("Starting Flask server")
    from flask_app.main import app

    FLASK_APP_PORT = int(os.getenv("FLASK_APP_PORT", 5000))
    threading.Thread(
        target=lambda: app.run(
            host="0.0.0.0",
            port=FLASK_APP_PORT,
            debug=True,
            use_reloader=False,
        )
    ).start()
