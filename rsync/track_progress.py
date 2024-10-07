import os
import threading


class TrackCopyProgress(object):
    def __init__(self, src, dst, total_size):
        self._src = src
        self._dst = dst
        self._total_size = total_size
        self._current_size = 0

    def progress(self, size):
        self._current_size += size

    def __str__(self):
        percentage = self._current_size / self._total_size * 100
        return f'Copy source {self._src} to destination {self._dst}: {percentage:.2f}%'


class TrackMultipleCopyProgress:
    def __init__(self):
        self.trackers = {}
        self.lock = threading.Lock()
        self.running = True

    def add_track_progress(self, worker_number, src_path, dst_path, total_size):
        with self.lock:
            self.trackers[worker_number] = TrackCopyProgress(src_path, dst_path, total_size)

    def update_track_progress(self, worker_number, size):
        with self.lock:
            self.trackers[worker_number].progress(size)
            self.display_progress()

    def display_progress(self):
        # Clear the screen for a fresh output
        os.system('clear')
        for worker_number, tracker in self.trackers.items():
            print(tracker)

    def stop(self):
        self.running = False