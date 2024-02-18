from .database import Database
from .models import (
    Generated,
    Image,
    Prompt
)


def create_tables(drop=False):
    tables = [
        Generated,
        Image,
        Prompt
    ]
    if drop:
        Database.db.drop_tables(tables)
    Database.db.create_tables(tables)
