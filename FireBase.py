import threading
import config_singleton
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import initialize_app


class DataBase:
    def __init__(self):
        main_path = config_singleton.ConfigSingleton.getInstance().get_config()['paths']['abs_path']
        firebase_keys_path = config_singleton.ConfigSingleton.getInstance().get_config()['paths']['firebase_keys_path']

        cred = credentials.Certificate(main_path + firebase_keys_path)
        initialize_app(cred)
        self.db = firestore.client()
        self.semaphores = {"db_sem": threading.Semaphore(1)}

    def write_data(self, args):
        t1 = threading.Thread(target=self.write_data_run, args=[args])
        t1.start()

    def write_data_run(self, args):
        self.semaphores['db_sem'].acquire()
        path = args[0]  # "wallets/personalWallets/SharonsWallet/openPositions/positionOne/positionOneContent"
        data_dict = args[1]  # {'symbol': 'ASS', 'amount': 69}
        doc_ref = self.db.document(path)
        doc_ref.set(data_dict)
        self.semaphores['db_sem'].release()

    def read_data(self, args):
        self.semaphores['db_sem'].acquire()
        path = args[0]  # "wallets/personalWallets/SharonsWallet/openPositions/positionOne/positionOneContent"
        doc_ref = self.db.document(path)
        data = doc_ref.get().to_dict()
        self.semaphores['db_sem'].release()
        return data

    def get_full_collection(self, collection_path):
        self.semaphores['db_sem'].acquire()
        collection_ref = self.db.collection(collection_path)
        docs = collection_ref.stream()

        data = {}
        for doc in docs:
            data[doc.id] = doc.to_dict()

        self.semaphores['db_sem'].release()
        return data

    def delete_data(self, args):
        self.semaphores['db_sem'].acquire()
        path = args[0]
        doc_ref = self.db.document(path)
        doc_ref.delete()
        self.semaphores['db_sem'].release()