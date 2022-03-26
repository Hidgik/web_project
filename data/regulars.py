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


def abort_if_not_found(name):
    if not Expressions.select().where(Expressions.name == name):
        return False
    return True


def is_author(name, id, b):
    if not Expressions.select().where(Expressions.name == name):
        return b
    regular = Expressions.get(Expressions.name == name)
    if regular.author_id == id:
        return True
    return False


class RegularResource:
    def get_one_regular(self, name):
        if abort_if_not_found(name):
            regular = Expressions.get(Expressions.name == name)
            return regular.expression

    def add_regular(self, name, expression, author_id):
        if abort_if_not_found(name):
            regular = Expressions.get(Expressions.name == name)
            if regular.author_id == author_id:
                regular = Expressions.get(Expressions.name == name)
                regular.delete_instance()
                regular = Expressions(name=name, expression=expression, author_id=author_id)
                regular.save()
                return True
            else:
                return False
        else:
            regular = Expressions(name=name, expression=expression, author_id=author_id)
            regular.save()
            return True
    
    def del_regular(self, name):
        regular = Expressions.get(Expressions.name == name)
        regular.delete_instance()

class RegularsResource:
    def get_all_regulars(self):
        a = []
        for regular in Expressions:
            a.append(f'{regular.name}: {regular.expression}')
        return a

init_db()
