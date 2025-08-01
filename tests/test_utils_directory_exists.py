# Generated by CodiumAI

import os
import pytest
from utilities import Utils


class TestUtilsDirectoryExists:

    # Returns True if the directory exists, and raises an error if the path is not a directory.
    def test_absolute_path_exists_is_directory(self, tmp_path):
        # Arrange
        utils = Utils()
        directory = tmp_path / "existing_directory"
        directory.mkdir()

        # Act
        exists = utils.directory_exists(str(directory))

        # Assert
        assert exists

        # Cleanup
        directory.rmdir()

    # Raises NotADirectoryError if the specified path exists and is not a directory.
    def test_absolute_path_directory_exists_is_not_directory_error(self, tmp_path):
        # Arrange
        utils = Utils()
        temp_file = os.path.join(tmp_path, "file.txt")
        with open(temp_file, "w", encoding="UTF=8") as f:
            f.write("content")

        # Act
        with pytest.raises(NotADirectoryError) as exc_info:
            utils.directory_exists(temp_file)

        # Assert
        assert (
            str(exc_info.value)
            == f"The specified path '{temp_file}' exists but is not a directory."
        )
        # Cleanup
        os.remove(temp_file)

    # Test if the method correctly identifies a non-existent directory and raises an appropriate error.
    def test_absolute_directory_does_not_exist(self, tmp_path):
        # Arrange
        utils = Utils()
        directory = tmp_path / "existing_directory"

        # Act
        exists = utils.directory_exists(directory)

        # Assert
        assert not exists
