from peewee import *

database = SqliteDatabase('db_books.db', **{})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

class Bookmark(BaseModel):
    folder = CharField()
    name = CharField()
    url = CharField()

    class Meta:
        db_table = 'bookmark'

class Bookmarksfin(BaseModel):
    _auto_pk = PrimaryKeyField()
    folder = UnknownField()  # 
    name = UnknownField()  # 
    url = UnknownField()  # 

    class Meta:
        db_table = 'bookmarksfin'

