class Stage:
    def __init__(self):
        pass
        self.variables = {}
        self.commonCS = {}
    
    def ValidateName(self):
        print(stage.variables)
        if stage.variables['Name'] == '10':
            return None
        self.CS = self.commonCS['askName'][:-1] + self.CS
        return "Данного имени нет в бд, Введите другое"

    def execute(self):
        return None
    
    def processChat(self, message):
        res = self.CS[0](message)
        del self.CS[0]
        if res:
            return res


if __name__ == '__main__':
    stage = Stage()
    stage.commonCS['askName'] = [lambda v: "Введите имя", lambda v: stage.variables.update({'Name':v}), lambda v: stage.ValidateName()]
    CS = {
        'begin': stage.commonCS['askName'] + [            
            lambda v: "Введите запрос", lambda v: stage.variables.update({'Query':v}), lambda v: stage.execute()],
        'add':[
            lambda v: "Введите имя", lambda v: stage.variables.update({'Name':v}), lambda v: stage.ValidateName(),
            lambda v: "Введите выражение", lambda v: stage.variables.update({'Query':v}), lambda v: stage.execute()],
    }    
    while True:
        a = input()
        stage.CS=CS[a]
        if a == 'begin':  
            while stage.CS:
                s=stage.processChat(a)
                if type(s) == str:
                    print(s)
                    a = input()
            print(stage.variables)
