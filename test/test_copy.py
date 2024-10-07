import time
from unittest.mock import MagicMock
import os
import random
import shutil
from rsync.copy import copy_file, copy_directory_contents, rsync_command, get_updated_destination_path
import filecmp
import pytest
from rsync.exceptions import ErrorCodeEnum, RsyncException

SRC_DIRECTORY_FOR_TESTS = "Src"
DST_DIRECTORY_FOR_TESTS = "Dst"
FILES_IN_ROOT_DIR = ["file1", "file2", "file3"]
SUB_DIR_1 = "Dir1"
SUB_DIR_2 = "Dir2"
FILES_IN_SUB_DIR_1 = ["file4", "file5"]
FILE_IN_SUB_DIR_2 = "file6"
DUMMY_FILE_NAME = "dummy"


@pytest.fixture(scope="function")
def setup_and_teardown():
    print("Setting up the test environment...")

    src_dir = SRC_DIRECTORY_FOR_TESTS
    dst_dir = DST_DIRECTORY_FOR_TESTS

    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(dst_dir, exist_ok=True)

    for filename in FILES_IN_ROOT_DIR:
        create_random_file_with_random_size(os.path.join(src_dir, filename))

    sub_dir_1 = os.path.join(src_dir, SUB_DIR_1)
    os.makedirs(sub_dir_1, exist_ok=True)

    for filename in FILES_IN_SUB_DIR_1:
        create_random_file_with_random_size(os.path.join(sub_dir_1, filename))

    sub_dir_2 = os.path.join(sub_dir_1, SUB_DIR_2)
    os.makedirs(os.path.join(sub_dir_1, SUB_DIR_2), exist_ok=True)
    create_random_file_with_random_size(os.path.join(sub_dir_2, FILE_IN_SUB_DIR_2))

    # Yield control to the test function
    yield

    # Delete the source and destination directories after the test
    if os.path.exists(src_dir):
        shutil.rmtree(src_dir)
    if os.path.exists(dst_dir):
        shutil.rmtree(dst_dir)

def create_random_file_with_random_size(file_path):
    size = random.randint(5 * 1024, 30 * 1024)  # Size between 5KB to 30KB
    with open(file_path, 'wb') as new_file:
        new_file.write(os.urandom(size))

def are_sub_systems_equal(dir1, dir2):
    comparison = filecmp.dircmp(dir1, dir2)

    if comparison.left_only or comparison.right_only or comparison.diff_files or comparison.funny_files:
        return False

    for subdir in comparison.common_dirs:
        if not are_sub_systems_equal(os.path.join(dir1, subdir), os.path.join(dir2, subdir)):
            return False
    return True

def are_files_equal(file1, file2):
    return filecmp.cmp(file1, file2, shallow=False)

def test_copy_file(setup_and_teardown):
    track_progress = MagicMock()
    bandwidth_controller = MagicMock()
    bandwidth_controller.get_chunk_size.return_value = 1024
    bandwidth_controller.update_bytes_copied = MagicMock()

    src_file = os.path.join(SRC_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0])
    dst_file = os.path.join(DST_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0])
    copy_file(src_file, dst_file, track_progress, bandwidth_controller)

    assert are_files_equal(src_file, dst_file)

def test_copy_directory_contents(setup_and_teardown):
    track_progress = MagicMock()
    bandwidth_controller = MagicMock()
    bandwidth_controller.get_chunk_size.return_value = 10
    bandwidth_controller.update_bytes_copied = MagicMock()

    copy_directory_contents(SRC_DIRECTORY_FOR_TESTS, DST_DIRECTORY_FOR_TESTS, track_progress, bandwidth_controller)
    assert are_sub_systems_equal(SRC_DIRECTORY_FOR_TESTS, DST_DIRECTORY_FOR_TESTS)


@pytest.mark.parametrize(
        "src_path, dst_path, condition_lambda, lambda_param, expected",
        [
            (
                    os.path.join(SRC_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0]),
                    DST_DIRECTORY_FOR_TESTS,
                    lambda dst_path: not os.path.isdir(dst_path),
                    DST_DIRECTORY_FOR_TESTS,
                    os.path.join(DST_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0])
            ),
            (
                    os.path.join(SRC_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0]),
                    DUMMY_FILE_NAME,
                    lambda dst_path: not os.path.isdir(dst_path),
                    DUMMY_FILE_NAME,
                    DUMMY_FILE_NAME
            ),
            (
                    SRC_DIRECTORY_FOR_TESTS + '/',
                    DST_DIRECTORY_FOR_TESTS,
                    lambda src_path: src_path.endswith('/'),
                    SRC_DIRECTORY_FOR_TESTS + '/',
                    DST_DIRECTORY_FOR_TESTS
            ),
            (
                    SRC_DIRECTORY_FOR_TESTS,
                    DST_DIRECTORY_FOR_TESTS,
                    lambda src_path: src_path.endswith('/'),
                    SRC_DIRECTORY_FOR_TESTS,
                    os.path.join(DST_DIRECTORY_FOR_TESTS, SRC_DIRECTORY_FOR_TESTS)
            )
        ]
    )
def test_get_updated_destination_path(setup_and_teardown, src_path, dst_path, condition_lambda, lambda_param, expected):
    assert expected == get_updated_destination_path(src_path, dst_path, condition_lambda(lambda_param))

@pytest.mark.parametrize(
        "src_path, dst_path, expected_error_code",
    [
        ("blabla_file", "dummy", ErrorCodeEnum.SOURCE_DOESNT_EXIST),
        (SRC_DIRECTORY_FOR_TESTS, os.path.join(SRC_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0]),
         ErrorCodeEnum.FILE_EXIST_INSTEAD_OF_DIRECTORY)
    ]
)
def test_rsync_command_exceptions(setup_and_teardown, src_path, dst_path, expected_error_code):
    with pytest.raises(RsyncException) as exception_obj:
        rsync_command(src_path, dst_path)

    print(exception_obj.value)
    assert exception_obj.value.error_code == expected_error_code


@pytest.mark.parametrize(
        "src_path, dst_path, comparison_function, expected_destination",
    [
        (
                os.path.join(SRC_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0]),
                DST_DIRECTORY_FOR_TESTS,
                are_files_equal,
                os.path.join(DST_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0])
        ),
        (
                os.path.join(SRC_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[0]),
                os.path.join(DST_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[1]),
                are_files_equal,
                os.path.join(DST_DIRECTORY_FOR_TESTS, FILES_IN_ROOT_DIR[1])
        ),
        (
                SRC_DIRECTORY_FOR_TESTS,
                DST_DIRECTORY_FOR_TESTS,
                are_sub_systems_equal,
                os.path.join(DST_DIRECTORY_FOR_TESTS, SRC_DIRECTORY_FOR_TESTS)
        ),
        (
                SRC_DIRECTORY_FOR_TESTS + '/',
                os.path.join(DST_DIRECTORY_FOR_TESTS, DUMMY_FILE_NAME),
                are_sub_systems_equal,
                os.path.join(DST_DIRECTORY_FOR_TESTS, DUMMY_FILE_NAME)
        )
    ]
)
def test_rsync_command(setup_and_teardown, src_path, dst_path, comparison_function, expected_destination):
    assert not os.path.exists(expected_destination)
    rsync_command(src_path, dst_path, 10 * 1024)
    assert os.path.exists(expected_destination)
    assert comparison_function(src_path, expected_destination)


