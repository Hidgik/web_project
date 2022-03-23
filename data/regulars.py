from peewee import CharField, Model, IntegerField, SqliteDatabase


db = SqliteDatabase('db/regular.db')

class Expressions(Model):
    name = CharField()
    expression = CharField()
    author_id = IntegerField()

    class Meta:
        database = db


def init_db():
    db.connect()
    db.create_tables([Expressions])
    if not Expressions.select().where(Expressions.name == 'Телефоны'):
        telephone_number = Expressions(name='Телефоны', expression=r"(8|\+7)(\-?)((\(\d{3}\))|(\d{3}(\-?)))((\d{7})|(\d{3}\-\d{2}\-\d{2}))", author_id=-7)
        telephone_number.save()

        ip = Expressions(name='IP адрес', expression=r"\b(?:(?:2(?:[0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9])\.){3}(?:(?:2([0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9]))\b", author_id=-7)
        ip.save()

        email = Expressions(name='email', expression=r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", author_id=-7)
        email.save()


def abort_if_not_found(name, text):
    if not Expressions.select().where(Expressions.name == name):
        print(text)
        return False
    return True


class RegularResource:
    def get_one_regular(self, name):
        if abort_if_not_found(name, 'Введённое имя отсутствует в бд'):
            regular = Expressions.get(Expressions.name == name)
            return regular.expression

    def add_regular(self, name, expression, author_id):
        if not Expressions.select().where(Expressions.name == name) or regular.author_id == author_id:
            regular = Expressions(name=name, expression=expression, author_id=author_id)
            regular.save()
        else:
            print('Вы не можете изменить чужое выражение (имя уже занято)')
    
    def del_regular(self, name, author_id):
        if abort_if_not_found(name, 'Введённое имя отсутствует в бд'):
            regular = Expressions.get(Expressions.name == name)
            if regular.author_id == author_id:
                regular.delete_instance()
            else:
                print('Вы не можете удалить чужое выражение')

class RegularsResource:
    def get_all_regulars(self):
        for regular in Expressions:
            print(f'{regular.name}: {regular.expression}')

init_db()
# regular = RegularResource()
# regulars = RegularsResource()
# print(regulars.get_all_regulars())
# print(regular.get_one_regular('Телефоны'))