
class TrackProgress(object):

    def __init__(self, src, dst, total_size):
        self._src = src
        self._dst = dst
        self._total_size = total_size
        self._current_size = 0
        print(f'Total bytes to copy {self._total_size}')

    def update_current_size(self, size):
        self._current_size += size

    def progress(self, size):
        self.update_current_size(size)
        percentage = self._current_size / self._total_size * 100

        print(f'Copy source {self._src} to destination {self._dst}: {percentage:.2f}%', end='\r', flush=True)
