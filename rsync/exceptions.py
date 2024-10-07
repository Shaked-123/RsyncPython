from enum import Enum, auto


class ErrorCodeEnum(Enum):
    SUCCESS = (0, "Successfully copied")
    FILE_EXIST_INSTEAD_OF_DIRECTORY = (1, "there is a file with the destination name")
    UNSUPPORTED_TYPE = (2, "unsupported source type")
    SOURCE_DOESNT_EXIST = (3, "source doesn't exist")
    COPY_FILE_FAILURE = (4, "Cannot copy file")
    COPY_DIRECTORY_FAILURE = (5, "Cannot copy directory")
    UNKNOWN_ERROR = (auto(), "undefined error")

class RsyncException(Exception):
    def __init__(self, src_path, dst_path, error_enum, external_error=""):
        super().__init__()
        self.src_path = src_path
        self.dst_path = dst_path
        self.error_code = error_enum
        self.external_error = external_error

    def __str__(self):
        return (f'Rsync error from "{self.src_path}" to destination "{self.dst_path}": '
                f' {self.error_code.value[0]} - {self.error_code.value[1]} {self.external_error}')
