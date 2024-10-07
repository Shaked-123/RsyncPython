import time

ONE_SECOND = 1
KB_TO_BYTES = 1024


class BandwidthController(object):

    def __init__(self, bandwidth):
        self._default_chunk_size = bandwidth * KB_TO_BYTES
        self._remained_chunk_size = self._default_chunk_size
        self._start_time = time.time()

    def update_bytes_copied(self, bytes_copied):
        if bytes_copied < self._remained_chunk_size:
            self._remained_chunk_size -= bytes_copied
        else:
            elapsed_time = time.time() - self._start_time
            if elapsed_time < ONE_SECOND:
                time.sleep(ONE_SECOND - elapsed_time)
                self.reset()

    def reset(self):
        self._remained_chunk_size = self._default_chunk_size
        self._start_time = time.time()

    def get_chunk_size(self):
        return self._remained_chunk_size
