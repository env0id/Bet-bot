import FireBase


class DBSingleton:
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if DBSingleton.__instance == None:
            DBSingleton()
        return DBSingleton.__instance


    def __init__(self):
        self.db = FireBase.DataBase()

        if DBSingleton.__instance != None:
            raise Exception("DBSingleton EXCEPTION")
        else:
            DBSingleton.__instance = self

    def get_db(self):
        return self.db

