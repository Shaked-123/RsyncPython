from concurrent.futures import ThreadPoolExecutor, as_completed
from rsync.rsync_command_functions import rsync_command, DEFAULT_BANDWIDTH_KB
from rsync.track_progress import TrackMultipleCopyProgress


DEFAULT_MAXIMUM_WORKERS = 10


def rsync_parallel(src_dst_pairs, bandwidth=DEFAULT_BANDWIDTH_KB):
    with ThreadPoolExecutor() as executor:
        futures = []
        tracker = TrackMultipleCopyProgress()

        for worker_number, (src, dst) in enumerate(src_dst_pairs):
            future = executor.submit(rsync_command, src, dst, tracker, worker_number, bandwidth)
            futures.append(future)

        for future in futures:
            future.result()
