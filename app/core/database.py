from sqlalchemy import create_engine


class DatabaseConnection:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)

    def get_engine(self):
        return self.engine
