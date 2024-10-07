import os
import shutil
from rsync.track_progress import TrackProgress
from rsync.bandwidth_controller import BandwidthController
from rsync.exceptions import RsyncException, ErrorCodeEnum

DEFAULT_BANDWIDTH_KB = 1
ALL_FILES = "*"


def copy_file_attributes(src_file, dst_file):
    shutil.copymode(src_file, dst_file)
    shutil.copystat(src_file, dst_file)

def is_copy_needed(src_file, dst_file):
    if os.path.exists(dst_file):
        src_modified_time = os.path.getmtime(src_file)
        dst_modified_time = os.path.getmtime(dst_file)

        if src_modified_time <= dst_modified_time:
            return False

    return True


def copy_file(src_file, dst_file, track_progress, bandwidth_controller):
    try:
        if is_copy_needed(src_file, dst_file):
            with open(src_file, "rb") as file_to_copy:
                with open(dst_file, "wb") as file_to_write:
                    while True:
                        chunk_size = bandwidth_controller.get_chunk_size()
                        data = file_to_copy.read(chunk_size)
                        if not data:
                            break

                        file_to_write.write(data)
                        track_progress.progress(len(data))
                        bandwidth_controller.update_bytes_copied(len(data))

            copy_file_attributes(src_file, dst_file)

    except Exception as file_copy_error:
        raise RsyncException(src_file, dst_file, ErrorCodeEnum.COPY_FILE_FAILURE, file_copy_error)


def copy_directory_contents(src_path, dst_path, track_progress, bandwidth_controller):
    try:
        os.makedirs(dst_path, exist_ok=True)
        for item in os.listdir(src_path):
            try:
                full_src_path = os.path.join(src_path, item)
                full_dst_path = os.path.join(dst_path, item)
                if os.path.isfile(full_src_path):
                    copy_file(full_src_path, full_dst_path, track_progress, bandwidth_controller)
                elif os.path.isdir(full_src_path):
                    # Copy directory contents (and directory if src_path doesn't include a trailing '/'
                    copy_directory_contents(full_src_path, full_dst_path, track_progress, bandwidth_controller)
            except RsyncException as error:
                print(error)
    except Exception as copy_directory_error:
        raise RsyncException(src_path, dst_path, ErrorCodeEnum.COPY_DIRECTORY_FAILURE, copy_directory_error)


def get_directory_size(directory):
    total_size = 0
    for dir_path, _, filenames in os.walk(directory):
        for filename in filenames:
            total_size += os.path.getsize(os.path.join(dir_path, filename))

    return total_size


def get_updated_destination_path(src_path, dst_path, condition):
    basename = os.path.basename(src_path)
    return dst_path if condition else os.path.join(dst_path, basename)


def execute_copy_command(src_path, dst_path, bandwidth, copy_command, total_size, update_dst_condition):
    updated_dst_path = get_updated_destination_path(src_path, dst_path, update_dst_condition)
    track_progress_obj = TrackProgress(src_path, dst_path, total_size)
    bandwidth_controller_obj = BandwidthController(bandwidth)
    copy_command(src_path, updated_dst_path, track_progress_obj, bandwidth_controller_obj)


def rsync_command(src_path, dst_path, bandwidth=DEFAULT_BANDWIDTH_KB):
    if os.path.exists(src_path):
        if os.path.isfile(src_path):
            # Copy file
            execute_copy_command(src_path, dst_path, bandwidth, copy_file,
                                 os.path.getsize(src_path), not os.path.isdir(dst_path))
        elif os.path.isdir(src_path):
            if not os.path.isfile(dst_path):
                # Copy directory contents (and directory if src_path doesn't include a trailing '/'
                execute_copy_command(src_path, dst_path, bandwidth, copy_directory_contents,
                                     get_directory_size(src_path), src_path.endswith('/'))
            else:
                raise RsyncException(src_path, dst_path, ErrorCodeEnum.FILE_EXIST_INSTEAD_OF_DIRECTORY)
        else:
            raise RsyncException(src_path, dst_path, ErrorCodeEnum.UNSUPPORTED_TYPE)
    else:
        raise RsyncException(src_path, dst_path, ErrorCodeEnum.SOURCE_DOESNT_EXIST)
