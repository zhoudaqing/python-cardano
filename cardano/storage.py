'''
* Use rocksdb as cardano-sl did.
* Store each epoch in seperate db.
    hash -> raw block
* Main database:
  * 'b' + hash -> BlockHeader
  * 'c' + tip -> hash

Sync
----

* get headers from storage current tip to network tip.
* download blocks and save to db.

'''
import os

import rocksdb
import cbor

class Storage(object):
    def __init__(self, root_path):
        self._root_path = root_path
        self.db = rocksdb.DB(os.path.join(self._root_path, 'db'), rocksdb.Options(create_if_missing=True))

    def epoch_db_path(self, epoch):
        return os.path.join(self._root_path, 'epoch%d'%epoch)

    def open_epoch_db(self, epoch, readonly=False):
        return rocksdb.DB(self.epoch_db_path(epoch), rocksdb.Options(create_if_missing=True), readonly)

    def tip(self):
        return self.db.get(b'c/tip')

    def set_tip(self, s):
        return self.db.put(b'c/tip', s)

    def blockheader(self, hash):
        return cbor.loads(self.db.get(b'b/'+hash))

    #def block(self, hash):
    #    hdr = self.blockheader(hash)
    #    epoch, _ = hdr.slot()
    #    db = self.open_epoch_db(epoch, readonly=True)
    #    return cbor.loads(db.get(hash))

    def append_block(self, block):
        hdr = block.header()

        # check prev_hash
        tip = self.tip()
        if tip:
            assert hdr.prev_header() == tip, 'invalid block.'

        hash = hdr.hash()
        self.db.put(b'b/' + hash, hdr.raw())
        self.db.put(b'c/tip', hash)