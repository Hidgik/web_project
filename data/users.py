from peewee import CharField, Model, IntegerField, SqliteDatabase


db = SqliteDatabase('db/users.db')

class Users(Model):
    id = IntegerField()
    query = CharField()
    regular = CharField()

    class Meta:
        database = db

db.connect()
db.create_tables([Users])

# regular = RegularResource()
# regulars = RegularsResource()
# print(regulars.get_all_regulars())
# print(regular.get_one_regular('Телефоны'))