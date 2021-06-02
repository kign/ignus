import re, logging
from time import time
from google.cloud import firestore
from datetime import datetime, timedelta, date as Date

# https://cloud.google.com/firestore/docs/query-data/get-data

re_shid = re.compile(r'^[a-z0-9]{1,10}$', re.I)
class Backend :
    URL = 'url'
    USER = 'user'
    VISITS = 'visits'

    def __init__ (self) :
        self.db = firestore.Client()

    def register(self, user):
        doc_ref = self.db.collection(self.USER).document(user['uid'])
        doc = doc_ref.get()
        if doc.exists :
            user['created'] = doc.get('created')
            user['hits'] = doc.get('hits') + 1
            doc_ref.update({'hits' : user['hits'], 'last': Date.today().strftime("%Y-%m-%d")})
        else :
            user['created'] = Date.today().strftime("%Y-%m-%d")
            user['hits'] = 0
            doc_ref.set(user)

    def is_owner(self, uid, shid):
        logging.debug("is_owner(%r,%s)", uid, shid)
        doc = self.db.collection(self.URL).document(shid).get()
        if not doc.exists :
            logging.debug("Not exists")
        elif doc.get('uid') != uid :
            logging.debug("Expected owner %r, not %r", doc.get('uid'), uid)
        else :
            logging.debug("OK matched")

        return doc.exists and doc.get('uid') == uid

    def get_user_urls(self, uid):
        return self.db.collection(self.URL).where('uid', '==', uid)

    def verify_shid(self, shid) :
        if not re_shid.match(shid) :
            return False
        doc_ref = self.db.collection(self.URL).document(shid)
        return not doc_ref.get().exists

    def url_add(self, uid, shid , url, expire):
        doc_ref = self.db.collection(self.URL).document(shid)
        doc_ref.set({'uid' : uid,
                     'url' : url,
                     'expire' : expire.strftime("%Y-%m-%d") if expire else None,
                     # 'created' : Date.today().strftime("%Y-%m-%d"),
                     'created' : int(time()),
                     'last' : None,
                     'hits' : 0})

    def shid_update_expire(self, shid, expire):
        doc_ref = self.db.collection(self.URL).document(shid)
        doc_ref.update({'expire': expire.strftime("%Y-%m-%d") if expire else None})

    def redirect(self,shid, headers):
        doc_ref = self.db.collection(self.URL).document(shid)
        doc = doc_ref.get()
        ts = time()
        if not doc.exists :
            return None
        if doc.get('expire') is not None and \
                Date.today() > datetime.strptime(doc.get('expire'),"%Y-%m-%d").date() :
            return False
        hits = doc.get('hits')
        doc_ref.update({'hits': hits + 1, 'last': time()})

        visit_ref = doc_ref.collection(self.VISITS).document(f"{ts:0.3f}")
        visit_ref.set(headers)

        return doc.get('url')

    def shid_log(self,shid):
        return self.db.collection(self.URL).document(shid).collection(self.VISITS)

    @staticmethod
    def _delete_collection(coll_ref, batch_size):
        tdel = 0
        while True :
            docs = coll_ref.limit(batch_size).stream()
            deleted = 0

            for doc in docs:
                print(f'Deleting doc {doc.id} => {doc.to_dict()}')
                doc.reference.delete()
                deleted = deleted + 1

            tdel += deleted
            if deleted < batch_size:
                break
        return tdel

    def shid_delete(self,shid):
        doc_ref = self.db.collection(self.URL).document(shid)
        tdel = self._delete_collection(doc_ref.collection(self.VISITS), 100)
        doc_ref.delete()

        return tdel





