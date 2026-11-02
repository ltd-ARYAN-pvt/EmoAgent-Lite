from database import initialize_database, get_session
from models import Base

def main():
    initialize_database()

    session = get_session()

    try:
        print("Database initialized successfully!")
        print("Tables:", list(Base.metadata.tables.keys()))
    finally:
        session.close()


if __name__ == "__main__":
    main()