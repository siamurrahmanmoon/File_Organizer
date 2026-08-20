অবশ্যই! আপনার আগের `documents.md` ফাইলটি আপডেট করে দিলাম। এতে **নতুন Advanced UI ফিচারসমূহ**, **আপডেটেড ক্লাস স্ট্রাকচার**, এবং আপনার রিকোয়েস্ট অনুযায়ী **Windows Executable (.exe) বানানোর পূর্ণাঙ্গ গাইড** যোগ করা হয়েছে। 

নিচের পুরো কন্টেন্টটি কপি করে আপনার `documents.md` ফাইলে পেস্ট করে দিন:

```markdown
# 📑 Technical Documentation: Smart File Organizer (v2.0)

This document provides a deep dive into the architecture, logic flow, class structures, and build process of the Advanced Smart File Organizer.

## 1. System Architecture

The application is built using a decoupled architecture, separating the core processing logic from the user interface.

- **Core Engine (`AnimeFileOrganizer`)**: Handles file system traversal, regex matching, renaming logic, and logging. It is driven by a configuration dictionary (`options`) passed from the UI.
- **UI Layer (`AnimeOrganizerGUI`)**: A Tkinter-based wrapper that provides an advanced graphical interface for folder selection, filter toggling, and real-time logging. It instantiates the core engine and runs it in a background thread to prevent UI freezing.

## 2. Core Logic & Decision Tree

The most critical feature of this tool is its **Smart Year Detection**. When processing a file, the engine follows this strict decision tree (controlled by UI filters):

```text
[Start Processing File]
       │
       ▼
[Does FILE name contain a year?] ──(YES)──> [SKIP FILE] (If 'Skip Existing Year' is ON)
       │
      (NO)
       ▼
[Does FOLDER name contain a year?] ──(YES)──> [USE FOLDER YEAR] (If 'Auto Folder Year' is ON)
       │
      (NO)
       ▼
[Ask User for Input] ──(Input)──> [USE USER YEAR] (If 'Ask User Input' is ON)
       │
      (Skip/Quit/Disabled)
       ▼
[SKIP FILE or TERMINATE]
```

## 3. Class Breakdown

### 3.1 `AnimeFileOrganizer`
The main processing class.

- **`__init__(self, source_path: str, output_path: str, options: dict)`**: Initializes paths, counters, logging, and parses the `options` dictionary (e.g., custom extensions).
- **`contains_year(self, text)`**: Uses the regex pattern `\b(19|20)\d{2}\b` to detect 4-digit years.
- **`clean_filename(self, filename)`**: Strips existing years, brackets, and excessive whitespace.
- **`process_folder(self, folder_path, dry_run)`**: 
  - Iterates through video files based on allowed extensions.
  - Implements the decision tree.
  - Uses `shutil.move()` to physically move and rename the file.
- **`scan_and_process(self, dry_run)`**: The entry point that uses `os.walk()` to recursively traverse the source directory.

### 3.2 `AnimeOrganizerGUI`
The graphical user interface class.

- **`setup_ui(self)`**: Constructs the advanced Tkinter widgets (Folder browsers, Checkbuttons for filters, Progressbar, ScrolledText).
- **`get_options(self) -> dict`**: Collects the state of all UI toggles and inputs into a dictionary to pass to the core engine.
- **`run_processing(self)`**: 
  - Creates a custom `logging.Handler` (`GUILogHandler`) for color-coded logs.
  - Spawns a `threading.Thread` to run the `AnimeFileOrganizer`.
- **`browse_source(self)` / `browse_output(self)`**: Opens native Windows directory selection dialogs.

## 4. Advanced UI Features & Filters

The v2.0 UI introduces several powerful toggles to control the organizer's behavior:

| Filter / Option | Description |
| :--- | :--- |
| **🔍 Dry Run** | Simulates the process. Logs what *would* happen without moving/renaming files. |
| **🎯 Auto Folder Year** | Enables automatic extraction of the year from the parent folder name. |
| **⏭️ Skip Existing Year** | If enabled, files that already contain a year in their name are ignored. |
| **❓ Ask User Input** | If enabled, prompts the user via CLI if no year is found in the file or folder. |
| **📂 Process Subfolders** | Enables recursive scanning of all nested directories. |
| **📄 Create Log** | Saves a detailed timestamped log file in the `logs/` directory. |
| **🚪 Auto-close** | Automatically closes the GUI window 2 seconds after successful completion. |
| **Custom Extensions** | Allows users to specify comma-separated file extensions to process (e.g., `.mp4, .mkv`). |

## 5. Regex Patterns

| Pattern | Regex | Purpose |
| :--- | :--- | :--- |
| **Year Detection** | `\b(19\|20)\d{2}\b` | Matches years between 1900 and 2099. |
| **Season/Episode** | `[Ss](\d{1,2})[Ee](\d{1,2})` | (Reserved) Detects standard S01E01 formatting. |

## 6. File & Directory Structure

### Input Structure
```text
R:\Anime [Hindi]\
├── One Piece (2006)\
│   ├── Episode 1.mp4
│   └── Episode 2 (2006).mp4
└── 2026\
    ├── Movie1.mp4
    ── Movie2.mkv
```

### Output Structure
Processed files are moved to the user-defined Output directory, preserving the original folder hierarchy (if 'Process Subfolders' is ON):
```text
R:\Anime [Hindi]_Organized\
├── One Piece (2006)\
│   ├── Episode 1 (2006).mp4
│   └── Episode 2 (2006).mp4
└── 2026\
    ├── Movie1 (2026).mp4
    └── Movie2 (2026).mkv
```

## 7. Logging and Error Handling

- **Logging**: The system uses Python's built-in `logging` module. It writes to both the GUI (color-coded) and a persistent file in the `logs/` directory.
- **Error Handling**: File operations (`shutil.move`) are wrapped in `try-except` blocks. Errors are logged, counters incremented, and processing continues.

## 8. ️ Building the Windows Executable (.exe)

To compile the Python source code into a standalone Windows `.exe` application using PyInstaller, follow these steps:

### 8.1 Prerequisites
Ensure your virtual environment is activated and install PyInstaller:
```bash
pip install pyinstaller
```

### 8.2 Run the Build Command
Execute the following command in your terminal:

```bash
pyinstaller --noconfirm --onefile --windowed --name "AnimeOrganizerPro" --icon=icon.ico organizer.py
```

**Command Breakdown:**
| Flag | Description |
| :--- | :--- |
| `--noconfirm` | Replaces the output directory without asking for confirmation. |
| `--onefile` | Packages everything (Python interpreter + libraries) into a single executable file. |
| **`--windowed`** | **Hides the console window (runs GUI only).** |
| `--name` | Specifies the name of the final `.exe` file. |
| `--icon` | Sets the application icon (remove `--icon=icon.ico` if you don't have an icon file). |

### 8.3 Locate the Executable
Once the build process is complete:
1. Open the newly created **`dist`** folder in your project directory.
2. You will find **`AnimeOrganizerPro.exe`** inside it.
3. This is your standalone application! You can distribute this file to anyone.

### 8.4 Troubleshooting Build Issues
- **Antivirus False Positive**: Windows Defender might flag the unsigned `.exe` as a false positive. Add an exclusion if necessary.
- **Missing Modules**: If the app crashes on startup, ensure all imports are detected. You can add `--hidden-import=tqdm` to the build command if needed.
- **File Size**: The `.exe` size will be around 30MB - 50MB due to the bundled Python environment. This is normal.

## 9. Future Enhancements (Roadmap)

- [ ] **API Integration**: Fetch metadata and correct years automatically using TMDB/AniList APIs.
- [ ] **Subtitle Handling**: Automatically detect and move associated `.srt` or `.ass` subtitle files alongside the video.
- [ ] **Jellyfin/Plex Formatting**: Add a toggle to format filenames strictly according to media server naming conventions.
```

### 🌟 কি কি আপডেট করা হয়েছে:
1. **Section 8 (Building the Windows Executable)**: PyInstaller দিয়ে `.exe` বানানোর পূর্ণাঙ্গ গাইড, কমান্ডের ব্যাখ্যা এবং Troubleshooting টিপস যোগ করা হয়েছে।
2. **Section 4 (Advanced UI Features)**: নতুন UI-এর সব ফিল্টার (Dry Run, Auto Folder Year, Custom Extensions ইত্যাদি) এর টেবিল যোগ করা হয়েছে।
3. **Section 3 (Class Breakdown)**: কোডের নতুন স্ট্রাকচার (`source_path`, `output_path`, `options` dict) অনুযায়ী ক্লাসগুলোর ব্যাখ্যা আপডেট করা হয়েছে।

এখন আপনার ডকুমেন্টেশন একদম প্রফেশনাল এবং কমপ্লিট!