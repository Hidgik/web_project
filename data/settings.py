from email.policy import default
from peewee import CharField, Model, IntegerField, SqliteDatabase


db = SqliteDatabase('db/setting.db')


class Settings(Model):
    id = IntegerField()
    default = CharField()
    search_sys = CharField() 
    delim_csv = CharField()
    type_file = CharField()

    class Meta:
        database = db

def init_db():
    db.connect()
    db.create_tables([Settings])

def init_user(id):
    if not Settings.select().where(Settings.id == id):
        setting = Settings(
            id=id, default='Всегда спрашивать', search_sys='Google', delim_csv=':', type_file='csv')
        setting.save(force_insert=True)


class SettingResource:
    def get_info(self, id):
        setting = Settings.get(Settings.id == id)
        return setting
    
    def change_object(self, id, obj):
        setting = Settings.get(Settings.id == id)
        if 'search_sys' in obj.keys():
            setting.search_sys = obj['search_sys']
        elif 'default' in obj.keys():
            setting.default = obj['default']
        elif 'type_file' in obj.keys():
            setting.type_file = obj['type_file']
        elif 'delim_csv' in obj.keys():
            setting.delim_csv = obj['delim_csv']
        setting.save()


init_db()