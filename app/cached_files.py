import base64
import os
import logging
import time
from urllib.parse import urljoin, urlparse


class CachedFiles:
    """Class for caching files, managing cache directory and handling operations on it"""

    def __init__(self, logger, cache_dir, proxy_server_base_url, download_endpoint_name):
        """Initialize CachedFiles class

        Args:
            logger (logging.Logger): Logger instance
            cache_dir (str): Cache directory path
        """
        self.logger = logger
        self.cache_dir = self.__normalize_path(cache_dir)
        self.proxy_server_base_url = proxy_server_base_url
        self.download_endpoint_name = download_endpoint_name
        os.makedirs(self.cache_dir, exist_ok=True)
        # self.logger.debug(f"Initialized cache directory: {self.cache_dir}")

    def __normalize_path(self, path):
        """Normalize OS path and return it

        Args:
            path (str): Path to normalize

        Returns:
            str: Normalized path
        """
        # self.logger.debug(f"Normalizing path: {path}")
        return os.path.normpath(path)

    def encode_data_to_base64url(self, data):
        """Encode data to base64 URL-safe format."""
        return base64.urlsafe_b64encode(data.encode()).decode()

    def decode_data_from_base64url(self, encoded_data):
        """Decode data from base64 URL-safe format."""
        return base64.urlsafe_b64decode(encoded_data.encode()).decode()

    def proxify_url(self, remote_url):
        """Create a proxied URL combining a proxy server and the original URL."""
        parsed_url = urlparse(remote_url)
        base64_host = self.encode_data_to_base64url(f"{parsed_url.scheme}://{parsed_url.netloc}")
        file_path = parsed_url.path
        return urljoin(self.proxy_server_base_url, f"{self.download_endpoint_name}/{base64_host}/{file_path}")

    def deproxify_url(self, encoded_url, path):
        """Reconstruct the original URL from the proxied format."""
        scheme_host_port = self.decode_data_from_base64url(encoded_url)
        return f"{scheme_host_port}/{path.lstrip('/')}"

    def get_file_name_from_url(self, url):
        file_name = os.path.basename(url)
        return file_name



    def get_cached_file_info(self, remote_url, file_name=None):
        
        proxified_url = self.proxify_url(
            remote_url
        )
        cached_file_path = self.convert_url_to_file_path(remote_url)
        
        if file_name is None:
            file_name = os.path.basename(cached_file_path)
                
        # gather info about the actual file: exists, size, human size
        file_exists = False
        file_size = None
        human_file_size = ""
        if os.path.exists(cached_file_path):
            file_exists = True
            file_size = os.path.getsize(cached_file_path)
            human_file_size = self.human_readable_size(file_size)
        else:
            cached_file_path = "not cached yet"

        ret_dict = {
                "file_name": file_name,
                "file_exists": file_exists,
                "file_size": file_size,
                "human_file_size": human_file_size,
                "remote_url": remote_url,
                "proxified_url": proxified_url,
                "cached_file_path": cached_file_path,
            }
        
        return ret_dict
        
        
        





    def extract_parent_directory(self, path):
        """Extract parent directory path from the given path and return normalized dir path

        Args:
            path (str): Path from which to extract parent directory

        Returns:
            str: Normalized parent directory path
        """
        # self.logger.debug(f"Extracting parent directory from path: {path}")
        parent_directory = os.path.dirname(self.__normalize_path(path))
        # self.logger.debug(f"Parent directory: {parent_directory}")
        return parent_directory

    def convert_url_to_file_path(self, url):
        """Extract file path from the URL and return normalized path, combined of cache dir and file path

        Args:
            url (str): URL from which to extract file path

        Returns:
            str: Normalized file path
        """
        # self.logger.debug(f"Converting URL to file path: {url}")
        parsed_url = urlparse(url)
        # remove leading slash from the URL path
        url_path = parsed_url.path.lstrip("/").lstrip("\\")
        file_path = self.__normalize_path(os.path.join(self.cache_dir, url_path))
        return file_path

    def convert_urls_to_file_paths(self, urls):
        """Extract file paths from the URLs and return them as list; uses function convert_url_to_file_path

        Args:
            urls (List[str]): List of URLs from which to extract file paths

        Returns:
            List[str]: List of normalized file paths
        """
        # self.logger.debug(f"Converting URLs to file paths: {urls}")
        file_paths = [self.convert_url_to_file_path(url) for url in urls]
        # self.logger.debug(f"File paths: {file_paths}")
        return file_paths

    def delete_files(self, file_paths):
        """Try and delete all given files. Return True if deleted all or False if failed to delete all. If given file absent, it doesn't count as a fail.

        Args:
            file_paths (List[str]): List of file paths to delete

        Returns:
            bool: True if all files are deleted, False otherwise
        """
        # self.logger.debug(f"Deleting files: {file_paths}")
        success = True
        for file_path in file_paths:
            try:
                os.remove(file_path)
                # self.logger.debug(f"Deleted file: {file_path}")
            except FileNotFoundError:
                # self.logger.debug(f"File not found: {file_path}")
                pass
            except Exception as e:
                # self.logger.error(f"Failed to delete file: {file_path}, {e}")
                success = False
        return success

    def get_files_info(self, file_paths):
        """Get file paths and return list of tuples: file path, file name, is_file_exists, file_size in bytes (or None/zero if not exists)

        Args:
            file_paths (List[str]): List of file paths

        Returns:
            List[Tuple[str, str, bool, Union[int, 0]]]: List of tuples with file path, file name, is_file_exists and file_size
        """
        # self.logger.debug(f"Getting files info: {file_paths}")
        file_info = [
            (
                file_path,
                os.path.basename(file_path),
                os.path.exists(file_path),
                os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            )
            for file_path in file_paths
        ]
        # self.logger.debug(f"File info: {file_info}")
        return file_info

    def create_directories(self, dir_paths):
        """Create all given dirs, return True if all dirs are created, False otherwise

        Args:
            dir_paths (List[str]): List of dir paths to create

        Returns:
            bool: True if all dirs are created, False otherwise
        """
        # self.logger.debug(f"Creating directories: {dir_paths}")
        success = True
        for dir_path in dir_paths:
            try:
                os.makedirs(dir_path, exist_ok=True)
                # self.logger.debug(f"Created directory: {dir_path}")
            except Exception as e:
                # self.logger.error(f"Failed to create directory: {dir_path}, {e}")
                success = False
        return success

    def get_temporary_file_name(self, file_path):
        """Returns a file path with a suffix of ".{unix_time}.tmp"

        Args:
            file_path (str): File path

        Returns:
            str: Temp file path
        """
        # self.logger.debug(f"Getting temporary file name: {file_path}")
        unix_time = str(int(time.time()))
        temporary_file_name = f"{file_path.rstrip('/').rstrip('\\')}.{unix_time}.tmp"
        # self.logger.debug(f"Temporary file name: {temporary_file_name}")
        return temporary_file_name

    def prepare_directory_for_file(self, file_path):
        """Create directories as needed for a given file path

        Args:
            file_path (str): File path
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)



    def human_readable_time(self, seconds):
        """Convert a time in seconds to a human-readable format."""
        # TODO all return values except seconds must be integer
        days, seconds =  divmod(seconds, 24 * 3600)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)    
        time_parts = [(days, 'day'), (hours, 'hour'), (minutes, 'minute'), (seconds, 'second')]    
        time_strings = [(value, unit) for value, unit in time_parts if value > 0]    
        return ' '.join(f"{int(value)} {unit}{'s' if value > 1 else ''}" for value, unit in time_strings)


    def human_readable_size(self, size_in_bytes):
        """Convert a size in bytes to a human-readable format."""
        units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
        unit_index = 0
        while size_in_bytes >= 1024 and unit_index < len(units) - 1:
            size_in_bytes /= 1024
            unit_index += 1
        formatted_size = f"{size_in_bytes:.1f}" if unit_index > 0 else f"{size_in_bytes}"
        return f"{formatted_size} {units[unit_index]}"

