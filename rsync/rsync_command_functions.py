import os
import shutil
from rsync.track_progress import TrackMultipleCopyProgress
from rsync.bandwidth_controller import BandwidthController
from rsync.exceptions import RsyncException, ErrorCodeEnum

DEFAULT_BANDWIDTH_KB = 10
ALL_FILES = "*"
DEFAULT_WORKER_NUMBER = 1


class RsyncCommand(object):
    def __init__(self, src_path, dst_path, global_progress_tracker,
                 worker_number=DEFAULT_WORKER_NUMBER, bandwidth=DEFAULT_BANDWIDTH_KB):
        self.src_path = src_path
        self.dst_path = dst_path
        self.global_progress_tracker = global_progress_tracker
        self.worker_number = worker_number
        self.bandwidth = bandwidth
        self.bandwidth_controller = BandwidthController(bandwidth)

    @staticmethod
    def copy_file_attributes(src_file, dst_file):
        shutil.copymode(src_file, dst_file)
        shutil.copystat(src_file, dst_file)

    @staticmethod
    def is_copy_needed(src_file, dst_file):
        """
        Copy is needed if the destination isn't exist or the modified time of the source is greater
        than the modified time of the destination
        :param src_file: str
        :param dst_file: str
        :return: bool
        """
        if os.path.exists(dst_file):
            src_modified_time = os.path.getmtime(src_file)
            dst_modified_time = os.path.getmtime(dst_file)

            if src_modified_time <= dst_modified_time:
                return False

        return True

    def copy_file(self, src_file, dst_file):
        try:
            if RsyncCommand.is_copy_needed(src_file, dst_file):
                with open(src_file, "rb") as file_to_copy:
                    with open(dst_file, "wb") as file_to_write:
                        while True:
                            chunk_size = self.bandwidth_controller.get_chunk_size()
                            data = file_to_copy.read(chunk_size)
                            if not data:
                                break

                            file_to_write.write(data)
                            self.global_progress_tracker.update_track_progress(self.worker_number, len(data))
                            self.bandwidth_controller.update_bytes_copied(len(data))

                RsyncCommand.copy_file_attributes(src_file, dst_file)

        except Exception as file_copy_error:
            raise RsyncException(src_file, dst_file, ErrorCodeEnum.COPY_FILE_FAILURE, file_copy_error)

    def copy_directory_contents(self, src_path, dst_path):
        try:
            os.makedirs(dst_path, exist_ok=True)
            for item in os.listdir(src_path):
                try:
                    full_src_path = os.path.join(src_path, item)
                    full_dst_path = os.path.join(dst_path, item)
                    if os.path.isfile(full_src_path):
                        self.copy_file(full_src_path, full_dst_path)
                    elif os.path.isdir(full_src_path):
                        # Copy directory contents (and directory if src_path doesn't include a trailing '/')
                        self.copy_directory_contents(full_src_path, full_dst_path)
                except RsyncException as error:
                    print(error)
        except Exception as copy_directory_error:
            raise RsyncException(src_path, dst_path, ErrorCodeEnum.COPY_DIRECTORY_FAILURE, copy_directory_error)

    @staticmethod
    def get_directory_size(directory):
        """
        Calculate directory size recursively and returns it
        :param directory: str
        :return: the size of the directory
        """
        total_size = 0
        for dir_path, _, filenames in os.walk(directory):
            for filename in filenames:
                total_size += os.path.getsize(os.path.join(dir_path, filename))

        return total_size

    @staticmethod
    def get_updated_destination_path(src_path, dst_path, condition):
        basename = os.path.basename(src_path)
        return dst_path if condition else os.path.join(dst_path, basename)

    def execute_copy_command(self, copy_command, total_size, update_dst_condition):
        updated_dst_path = self.get_updated_destination_path(self.src_path, self.dst_path, update_dst_condition)
        self.global_progress_tracker.add_track_progress(self.worker_number, self.src_path, self.dst_path, total_size)
        copy_command(self.src_path, updated_dst_path)

    def run(self):
        if os.path.exists(self.src_path):
            if os.path.isfile(self.src_path):
                # Copy file
                self.execute_copy_command(self.copy_file, os.path.getsize(self.src_path),
                                          not os.path.isdir(self.dst_path))
            elif os.path.isdir(self.src_path):
                if not os.path.isfile(self.dst_path):
                    # Copy directory contents (and directory if src_path doesn't include a trailing '/'
                    self.execute_copy_command(self.copy_directory_contents,
                                              RsyncCommand.get_directory_size(self.src_path),
                                              self.src_path.endswith('/'))
                else:
                    raise RsyncException(self.src_path, self.dst_path, ErrorCodeEnum.FILE_EXIST_INSTEAD_OF_DIRECTORY)
            else:
                raise RsyncException(self.src_path, self.dst_path, ErrorCodeEnum.UNSUPPORTED_TYPE)
        else:
            raise RsyncException(self.src_path, self.dst_path, ErrorCodeEnum.SOURCE_DOESNT_EXIST)
