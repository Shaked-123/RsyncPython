from concurrent.futures import ThreadPoolExecutor, as_completed
from rsync.rsync_command_functions import RsyncCommand, DEFAULT_BANDWIDTH_KB
from rsync.track_progress import TrackMultipleCopyProgress


DEFAULT_MAXIMUM_WORKERS = 10


def rsync_parallel(src_dst_pairs, bandwidth=DEFAULT_BANDWIDTH_KB):
    with ThreadPoolExecutor() as executor:
        futures = []
        tracker = TrackMultipleCopyProgress()

        for worker_number, (src, dst) in enumerate(src_dst_pairs):
            rsync_command_obj = RsyncCommand(src, dst, tracker, worker_number, bandwidth)
            future = executor.submit(rsync_command_obj.run)
            futures.append(future)

        for future in futures:
            future.result()
