"""
File Synchronization Project

This script provides functionality for synchronizing files between different storage locations,
including FTP servers, zip archives, and local folders. It supports automatic synchronization
of added, deleted, and modified files, as well as periodic monitoring of FTP and folder changes.

Modules:
- FTPLocation: Interacts with an FTP server for file operations.
- ZipLocation: Interacts with zip archives for file operations.
- FolderLocation: Interacts with local file systems for file operations.
- sync_files: Synchronizes files between two locations.
- monitor_ftp_changes: Periodically monitors an FTP server for changes and syncs them.
- monitor_folder: Monitors local folders or FTP servers for changes.
- create_location: Creates the appropriate location object based on a given string.
- calculate_checksum: Calculates the MD5 checksum of a file to detect modifications.
- MyHandler: A custom handler for monitoring file system events.

Dependencies:
- ftplib: For FTP interaction.
- zipfile: For zip file handling.
- os: For file and directory manipulation.
- hashlib: For checksum calculation.
- watchdog: For monitoring file system events.
"""
from abc import ABC, abstractmethod
import os
import zipfile
import ftplib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from urllib.parse import urlparse
import time
import hashlib
import sys


class Location(ABC):
    """
        Abstract base class for different storage locations (FTP, Zip, Folder).

        Methods:
            list_files: Lists all files in the location.
            read_file: Reads a file's content.
            write_file: Writes content to a file.
            delete_file: Deletes a file.
            get_file_mod_time: Returns the modification time of a file.
        """

    @abstractmethod
    def list_files(self):
        """
        Lists all files in the storage location.

        Returns:
            List of filenames in the location.
        """
        pass

    @abstractmethod
    def read_file(self, file_name):
        """
        Reads the content of a file.

        Args:
            file_name (str): The name of the file to read.

        Returns:
            bytes: The content of the file.
        """
        pass

    @abstractmethod
    def write_file(self, file_name, content):
        """
        Writes content to a file.

        Args:
            file_name (str): The name of the file to write to.
            content (bytes): The content to write to the file.
        """
        pass

    @abstractmethod
    def delete_file(self, file_name):
        """
        Deletes a file.

        Args:
            file_name (str): The name of the file to delete.
        """
        pass

    @abstractmethod
    def get_file_mod_time(self, file_name):
        """
        Gets the modification time of a file.

        Args:
            file_name (str): The name of the file.

        Returns:
            float: The modification time as a Unix timestamp.
        """
        pass


class FTPLocation(Location):
    """
        Represents an FTP server location for file synchronization.

        Args:
            ftp_url (str): The FTP server URL.
            username (str): The username for FTP login.
            password (str): The password for FTP login.
            folder_path (str, optional): The path to a specific folder on the FTP server.

        Methods:
            list_files: Lists files on the FTP server.
            read_file: Reads a file from the FTP server.
            write_file: Writes a file to the FTP server.
            delete_file: Deletes a file from the FTP server.
            get_file_mod_time: Gets the modification time of a file on the FTP server.
    """
    def __init__(self, ftp_url, username, password, folder_path=None):
        """
        Initializes the FTPLocation with FTP server credentials and optional folder path.

        Args:
            ftp_url (str): The FTP server URL.
            username (str): The username for FTP login.
            password (str): The password for FTP login.
            folder_path (str, optional): The folder path to access on the FTP server.
        """
        self.ftp_url = ftp_url
        self.username = username
        self.password = password
        self.folder_path = folder_path
        self.ftp = ftplib.FTP(self.ftp_url)
        self.ftp.login(self.username, self.password)

        if self.folder_path:
            self.ftp.cwd(self.folder_path)  # Navigate to the specified folder

    def list_files(self):
        """
        Lists all files in the current directory on the FTP server.

        Returns:
            list: A list of filenames in the current directory on the FTP server.
        """
        return self.ftp.nlst()  # List all files in the current directory on FTP

    def read_file(self, file_name):
        """
        Reads the content of a file from the FTP server.

        Args:
            file_name (str): The name of the file to read.

        Returns:
            bytes: The content of the file.
        """
        content = bytearray()
        self.ftp.retrbinary(f"RETR {file_name}", content.extend)
        return bytes(content)

    def write_file(self, file_name, content):
        """
        Writes content to a file on the FTP server.

        Args:
            file_name (str): The name of the file to write to.
            content (bytes): The content to write to the file.
        """
        with open("tempfile", "wb") as temp:
            temp.write(content)
        with open("tempfile", "rb") as temp:
            self.ftp.storbinary(f"STOR {file_name}", temp)
        os.remove("tempfile")

    def delete_file(self, file_name):
        """
        Deletes a file from the FTP server.

        Args:
            file_name (str): The name of the file to delete.
        """
        try:
            self.ftp.delete(file_name)
            print(f"Deleted {file_name} from FTP")
        except ftplib.error_perm as e:
            print(f"Error deleting file {file_name}: {e}")

    def get_file_mod_time(self, file_name):
        """
        Gets the modification time of a file on the FTP server.

        Args:
            file_name (str): The name of the file.

        Returns:
            float: The modification time as a Unix timestamp.
        """
        try:
            mod_time = self.ftp.sendcmd(f"MDTM {file_name}")
            return time.mktime(time.strptime(mod_time[4:], "%Y%m%d%H%M%S"))
        except ftplib.error_perm as e:
            print(f"Error getting modification time for {file_name}: {e}")
            return 0


class ZipLocation(Location):
    """
        Represents a zip archive location for file synchronization.

        Args:
            zip_path (str): The path to the zip archive.

        Methods:
            list_files: Lists files in the zip archive.
            read_file: Reads a file from the zip archive.
            write_file: Writes content to a file in the zip archive.
            delete_file: Deletes a file from the zip archive.
            get_file_mod_time: Gets the modification time of a file in the zip archive.
    """
    def __init__(self, zip_path):
        """
            Initializes the ZipLocation with the path to the zip archive.

            Args:
                zip_path (str): The path to the zip archive.
        """
        self.zip_path = zip_path

    def list_files(self):
        """
            Lists all files in the zip archive.

            Returns:
                list: A list of filenames in the zip archive.
        """
        with zipfile.ZipFile(self.zip_path, 'r') as zipf:
            return zipf.namelist()

    def read_file(self, file_name):
        """
            Reads the content of a file from the zip archive.

            Args:
                file_name (str): The name of the file to read.

            Returns:
                bytes: The content of the file.
        """
        with zipfile.ZipFile(self.zip_path, 'r') as zipf:
            return zipf.read(file_name)

    def write_file(self, file_name, content):
        """
            Writes content to a file in the zip archive.

            Args:
                file_name (str): The name of the file to write to.
                content (bytes): The content to write to the file.
        """
        temp_zip_path = self.zip_path + ".tmp"
        with zipfile.ZipFile(self.zip_path, 'r') as zipf:
            with zipfile.ZipFile(temp_zip_path, 'w') as temp_zip:
                for item in zipf.infolist():
                    if item.filename != file_name:
                        temp_zip.writestr(item, zipf.read(item.filename))
        # Adaugă fișierul nou
        with zipfile.ZipFile(temp_zip_path, 'a') as temp_zip:
            temp_zip.writestr(file_name, content)
        # Înlocuiește arhiva originală cu cea temporară
        os.replace(temp_zip_path, self.zip_path)

    def delete_file(self, file_name):
        """
            Deletes a file from the zip archive.

            Args:
                file_name (str): The name of the file to delete.
        """
        temp_path = self.zip_path + "_temp"
        with zipfile.ZipFile(self.zip_path, 'r') as zipf:
            with zipfile.ZipFile(temp_path, 'w') as temp_zip:
                for item in zipf.infolist():
                    if item.filename != file_name:
                        temp_zip.writestr(item.filename, zipf.read(item.filename))
        os.replace(temp_path, self.zip_path)

    def get_file_mod_time(self, file_name):
        """
            Gets the modification time of a file in the zip archive.

            Args:
                file_name (str): The name of the file.

            Returns:
                float: The modification time as a Unix timestamp.
        """
        with zipfile.ZipFile(self.zip_path, 'r') as zipf:
            info = zipf.getinfo(file_name)
            return time.mktime(info.date_time + (0, 0, -1))


class FolderLocation(Location):
    """
        Represents a local folder location for file synchronization.

        Args:
            folder_path (str): The path to the folder.

        Methods:
            list_files: Lists files in the local folder.
            read_file: Reads a file from the local folder.
            write_file: Writes content to a file in the local folder.
            delete_file: Deletes a file from the local folder.
            get_file_mod_time: Gets the modification time of a file in the local folder.
    """
    def __init__(self, folder_path):
        """
            Initializes the FolderLocation with the path to the local folder.

            Args:
                folder_path (str): The path to the folder.
        """
        self.folder_path = folder_path

    def list_files(self):
        """
            Lists all files in the local folder.

            Returns:
                list: A list of filenames in the local folder.
        """
        return [f for f in os.listdir(self.folder_path) if os.path.isfile(os.path.join(self.folder_path, f))]

    def read_file(self, file_name):
        """
            Reads the content of a file from the local folder.

            Args:
                file_name (str): The name of the file to read.

            Returns:
                bytes: The content of the file.
        """
        with open(os.path.join(self.folder_path, file_name), 'rb') as f:
            return f.read()

    def write_file(self, file_name, content):
        """
            Writes content to a file in the local folder.

            Args:
                file_name (str): The name of the file to write to.
                content (bytes): The content to write to the file.
        """
        with open(os.path.join(self.folder_path, file_name), 'wb') as f:
            f.write(content)

    def delete_file(self, file_name):
        """
            Deletes a file from the local folder.

            Args:
                file_name (str): The name of the file to delete.
        """
        os.remove(os.path.join(self.folder_path, file_name))

    def get_file_mod_time(self, file_name):
        """
            Gets the modification time of a file in the local folder.

            Args:
                file_name (str): The name of the file.

            Returns:
                float: The modification time as a Unix timestamp.
        """
        return os.path.getmtime(os.path.join(self.folder_path, file_name))


def sync_files(loc1, loc2):
    """
        Synchronizes files between two locations.

        Args:
            loc1 (Location): The first storage location.
            loc2 (Location): The second storage location.
    """
    files1 = set(loc1.list_files())
    files2 = set(loc2.list_files())

    all_files = files1.union(files2)

    for file in all_files:
        in_loc1 = file in files1
        in_loc2 = file in files2

        if in_loc1 and in_loc2:
            mod_time1 = loc1.get_file_mod_time(file)
            mod_time2 = loc2.get_file_mod_time(file)

            if mod_time1 > mod_time2:
                content = loc1.read_file(file)
                loc2.write_file(file, content)
            elif mod_time2 > mod_time1:
                content = loc2.read_file(file)
                loc1.write_file(file, content)

        if in_loc1 and not in_loc2:
            content = loc1.read_file(file)
            loc2.write_file(file, content)

        if in_loc2 and not in_loc1:
            content = loc2.read_file(file)
            loc1.write_file(file, content)


class MyHandler(FileSystemEventHandler):
    """
        Custom event handler for monitoring file system changes.

        Args:
            loc1 (Location): The first location to synchronize.
            loc2 (Location): The second location to synchronize.

        Methods:
            on_created: Handles file creation events.
            on_deleted: Handles file deletion events.
            on_modified: Handles file modification events.
    """
    def __init__(self, loc1, loc2):
        """
            Initializes the event handler with two locations.

            Args:
                loc1 (Location): The first location to synchronize.
                loc2 (Location): The second location to synchronize.
        """
        self.loc1 = loc1
        self.loc2 = loc2

    def on_created(self, event):
        """
            Handles file creation events.

            Args:
                event (FileSystemEvent): The event object containing event details.
        """
        if event.is_directory:
            return
        print(f"File created: {event.src_path}")
        sync_files(self.loc1, self.loc2)

    def on_deleted(self, event):
        """
            Handles file deletion events.

            Args:
                event (FileSystemEvent): The event object containing event details.
        """
        if event.is_directory:
            return
        print(f"File deleted: {event.src_path}")
        file_name = os.path.basename(event.src_path)
        if file_name in self.loc1.list_files():
            self.loc1.delete_file(file_name)
        if file_name in self.loc2.list_files():
            self.loc2.delete_file(file_name)

    def on_modified(self, event):
        """
            Handles file modification events.

            Args:
                event (FileSystemEvent): The event object containing event details.
        """
        if event.is_directory:
            return
        print(f"File modified: {event.src_path}")
        sync_files(self.loc1, self.loc2)


def calculate_checksum(file_content):
    """
    Calculates the MD5 checksum of a file content.

    Args:
        file_content (bytes): The content of the file.

    Returns:
        str: The MD5 checksum of the file content.
    """
    return hashlib.md5(file_content).hexdigest()


def monitor_ftp_changes(ftp_loc, other_loc, poll_interval=10):
    """
    Monitors FTP for changes and synchronizes with the other location.

    Args:
        ftp_loc (FTPLocation): The FTP location to monitor.
        other_loc (Location): The location to synchronize with.
        poll_interval (int): The polling interval in seconds.
    """
    print("Monitoring FTP for changes...")
    previous_files = set(ftp_loc.list_files())

    try:
        while True:
            time.sleep(poll_interval)
            current_files = set(ftp_loc.list_files())

            # Detect added files
            added_files = current_files - previous_files
            for file in added_files:
                print(f"New file detected on FTP: {file}")
                content = ftp_loc.read_file(file)
                other_loc.write_file(file, content)

            # Detect deleted files
            deleted_files = previous_files - current_files
            for file in deleted_files:
                print(f"File deleted from FTP: {file}")
                other_loc.delete_file(file)

            # Detect modified files by comparing checksums
            for file in current_files & previous_files:
                # Fetch the file contents and calculate checksums
                ftp_content = ftp_loc.read_file(file)
                other_content = other_loc.read_file(file)

                ftp_checksum = calculate_checksum(ftp_content)
                other_checksum = calculate_checksum(other_content)

                if ftp_checksum != other_checksum:
                    print(f"File modified on FTP: {file}")
                    other_loc.write_file(file, ftp_content)
                elif ftp_checksum != other_checksum:
                    print(f"File modified locally: {file}")
                    ftp_loc.write_file(file, other_content)

            previous_files = current_files
    except KeyboardInterrupt:
        print("Stopped monitoring FTP for changes.")


def monitor_folder(loc1, loc2):
    """
    Monitors changes in local folders or FTP servers and synchronizes them.

    Args:
        loc1 (Location): The first location to monitor.
        loc2 (Location): The second location to monitor.
    """
    if isinstance(loc1, FTPLocation):
        monitor_ftp_changes(loc1, loc2)
    elif isinstance(loc2, FTPLocation):
        monitor_ftp_changes(loc2, loc1)
    else:
        # Use filesystem event monitoring for local folders
        event_handler = MyHandler(loc1, loc2)
        observer = Observer()

        if isinstance(loc1, FolderLocation):
            observer.schedule(event_handler, loc1.folder_path, recursive=True)
        if isinstance(loc2, FolderLocation):
            observer.schedule(event_handler, loc2.folder_path, recursive=True)

        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


def create_location(location_str):
    """
        Creates a location object based on a string representation.

        Args:
            location_str (str): The location string (e.g., "ftp://...").

        Returns:
            Location: The corresponding location object (FTPLocation, ZipLocation, or FolderLocation).

        Raises:
            ValueError: If the location string is not valid.
    """
    if location_str.startswith("ftp:"):
        ftp_url = location_str[4:]
        parsed_url = urlparse(f"ftp://{ftp_url}")

        user = parsed_url.username
        password = parsed_url.password
        host = parsed_url.hostname
        path = parsed_url.path.lstrip("/")  # folderul de pe FTP

        if user and password and host:
            return FTPLocation(host, user, password, path)
        else:
            raise ValueError("URL-ul FTP trebuie să conțină utilizator, parolă și host.")
    elif location_str.startswith("zip:"):
        return ZipLocation(location_str[4:])
    elif location_str.startswith("folder:"):
        return FolderLocation(location_str[7:])
    else:
        raise ValueError("Unknown location type")


if __name__ == "__main__":
    """
        Main entry point for the script. Synchronizes files between two specified locations.

        Command-line usage:
            python main.py <location_1> <location_2>
    """
    if len(sys.argv) != 3:
        print("Usage: main.py <location_1> <location_2>")
        sys.exit(1)

    loc1 = create_location(sys.argv[1])
    loc2 = create_location(sys.argv[2])

    sync_files(loc1, loc2)
    monitor_folder(loc1, loc2)
