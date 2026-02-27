# 🔄 File Synchronization System

> An automated, bidirectional file synchronization engine built in Python, supporting local directories, ZIP archives, and remote FTP servers.

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![OOP](https://img.shields.io/badge/Architecture-OOP-blue?style=for-the-badge)
![Automation](https://img.shields.io/badge/Automation-Watchdog-success?style=for-the-badge)

## 📖 Overview
[cite_start]This project provides a highly modular system for synchronizing files between diverse storage locations[cite: 448]. By utilizing **Object-Oriented Programming (OOP)** and **Abstract Base Classes (ABC)**, the system is designed to be easily extensible. [cite_start]It automatically handles the creation, modification, and deletion of files across different environments in real-time[cite: 449].

## 🏗️ Architecture
The core of the system relies on an Abstract Base Class called `Location`, which defines the contract for any storage medium. 
Currently, the system implements three concrete storage locations:
* [cite_start]**`FolderLocation`**: Interacts with local file systems[cite: 451].
* [cite_start]**`ZipLocation`**: Interacts directly with ZIP archives, allowing real-time injection and extraction of files[cite: 450].
* [cite_start]**`FTPLocation`**: Interacts with remote FTP servers for off-site backups or remote syncs[cite: 450].

## ✨ Key Features
* [cite_start]**Real-time Monitoring:** Uses the `watchdog` library to actively listen for file system events (creation, deletion, modification) in local folders[cite: 458].
* [cite_start]**Automated FTP Polling:** Periodically polls FTP servers to detect remote changes and sync them locally[cite: 452].
* [cite_start]**Integrity Validation:** Calculates **MD5 checksums** (`hashlib`) to accurately detect modified files, avoiding unnecessary transfers[cite: 455].
* **Bidirectional Sync:** Ensures that changes in `Location A` reflect in `Location B`, and vice-versa.
* [cite_start]**Factory Pattern:** Dynamically parses connection strings (e.g., `ftp://...`, `folder:...`) to instantiate the correct storage classes[cite: 454].

## 🛠️ Tech Stack
* **Language:** Python 3.x
* [cite_start]**Core Libraries:** `os`, `hashlib` (MD5 Checksums), `ftplib` (FTP interaction), `zipfile` (Archive handling)[cite: 457, 458].
* [cite_start]**External Dependencies:** `watchdog` (for file system event monitoring)[cite: 458].

## 🚀 Getting Started

### Prerequisites
Make sure you have Python installed, then install the required dependencies:
```bash
pip install watchdog
### Usage
The script runs from the command line and requires two target locations. The locations are specified using prefixes (`folder:`, `zip:`, `ftp:`).

**Basic Syntax:**
```bash
python main.py <location_1> <location_2>
```

**Examples:**

1. **Sync two local folders:**
```bash
python main.py folder:./source_dir folder:./backup_dir
```

2. **Sync a local folder with a ZIP archive (Live Backup):**
```bash
python main.py folder:./my_project zip:./project_backup.zip
```

3. **Sync a local folder with a remote FTP server:**
```bash
python main.py folder:./website ftp://username:password@ftp.myserver.com/public_html
```

Once started, the script will perform an initial synchronization and then begin actively monitoring both locations for any future changes.

---
**Developed by Iustin Istrate** - *Software Engineering Student*
