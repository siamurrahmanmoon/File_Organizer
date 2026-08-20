import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Automatically enforce running inside project's virtual environment (venv)
from utils.venv_utils import ensure_venv
ensure_venv()

from config import get_default_config
from core.engine import AnimeFileOrganizer
from core.profiles_manager import ProfilesManager
from core.rollback_manager import RollbackManager
from core.watch_folder import WatchFolderService


def main():
    parser = argparse.ArgumentParser(
        description="🎬 Smart File Organizer Pro - Enterprise Anime & Media Organizer CLI",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-s", "--source", type=str, help="Source directory containing anime/media files")
    parser.add_argument("-o", "--output", type=str, help="Output destination directory")
    parser.add_argument("-p", "--profile", type=str, help="Load a preset profile (e.g. default, plex_jellyfin, anime_archival)")
    parser.add_argument("-t", "--template", type=str, help="Custom naming template (e.g. '{Title} ({Year}) [{Resolution}] - S{Season}E{Episode}')")
    parser.add_argument("--dry-run", action="store_true", default=None, help="Simulate without moving/renaming files (default: true in safe configs)")
    parser.add_argument("--execute", action="store_true", help="Execute actual file rename/move operations")
    parser.add_argument("--no-subfolders", action="store_true", help="Disable recursive subfolder processing")
    parser.add_argument("--watch", action="store_true", help="Run in continuous watch folder mode")
    parser.add_argument("--rollback", type=str, metavar="SESSION_ID", help="Rollback all operations performed in a specific session ID")
    parser.add_argument("--list-profiles", action="store_true", help="List all available preset configuration profiles")
    parser.add_argument("--list-sessions", action="store_true", help="List recent processing sessions for rollback")

    args = parser.parse_args()

    # If no arguments provided, show help
    if len(sys.argv) == 1:
        print("=" * 60)
        print("  🎬 Anime Organizer Pro - CLI Mode")
        print("=" * 60)
        print()
        parser.print_help()
        print()
        print("=" * 60)
        print("  Quick Examples:")
        print("  • run_cli.bat -s \"R:\\Anime\" -o \"R:\\Organized\"")
        print("  • run_cli.bat -s \"R:\\Anime\" -o \"R:\\Organized\" --execute")
        print("  • run_cli.bat --list-profiles")
        print("=" * 60)
        input("\nPress Enter to exit...")
        return

    profiles_mgr = ProfilesManager()
    rollback_mgr = RollbackManager()

    # 1. List Profiles
    if args.list_profiles:
        profiles = profiles_mgr.list_presets()
        print("📑 Available Configuration Presets:")
        for p in profiles:
            print(f"  • {p}")
        input("\nPress Enter to exit...")
        return

    # 2. List Sessions
    if args.list_sessions:
        sessions = rollback_mgr.list_sessions(limit=10)
        print("🔄 Recent Processing Sessions:")
        for s in sessions:
            print(f"  • ID: {s['session_id']} | Start: {s['start_time']} | Processed: {s['processed_files']} | Status: {s['status']}")
        input("\nPress Enter to exit...")
        return

    # 3. Rollback
    if args.rollback:
        print(f"⏪ Rolling back session: {args.rollback}...")
        success, errors, msgs = rollback_mgr.rollback_session(args.rollback)
        print(f"✅ Successfully restored: {success} files.")
        if errors > 0:
            print(f"❌ Failed to restore {errors} files:")
            for m in msgs:
                print(f"   - {m}")
        input("\nPress Enter to exit...")
        return

    # Load base config
    if args.profile:
        config = profiles_mgr.load_preset(args.profile)
        if not config:
            print(f"❌ Error: Preset profile '{args.profile}' not found.")
            input("\nPress Enter to exit...")
            sys.exit(1)
        print(f"📂 Loaded configuration preset: '{args.profile}'")
    else:
        config = get_default_config()

    # Override CLI flags
    if args.source:
        config.source_path = args.source
    if args.output:
        config.output_path = args.output
    if args.template:
        config.naming_template = args.template
    if args.execute:
        config.dry_run = False
    elif args.dry_run is not None:
        config.dry_run = args.dry_run
    if args.no_subfolders:
        config.process_subfolders = False

    if not config.source_path or not config.output_path:
        print("❌ Error: Both --source (-s) and --output (-o) paths must be specified.")
        parser.print_help()
        input("\nPress Enter to exit...")
        sys.exit(1)

    # 4. Watch Folder Mode
    if args.watch:
        print(f"👀 Starting Watch Folder service on: {config.source_path}")
        organizer = AnimeFileOrganizer(config.source_path, config.output_path, config=config)

        def on_file_ready(file_path: Path):
            target_folder = Path(config.output_path)
            organizer.process_file(file_path, target_folder, dry_run=config.dry_run)

        watcher = WatchFolderService(
            config.source_path,
            process_callback=on_file_ready,
            video_extensions=config.video_extensions,
            poll_interval=config.watch_interval_seconds,
            stability_wait=config.watch_file_stability_wait_seconds
        )
        watcher.start()
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop()
            print("\n⏹️ Watcher stopped by user.")
        return

    # 5. Standard Batch Execution
    organizer = AnimeFileOrganizer(config.source_path, config.output_path, config=config)
    summary = organizer.scan_and_process()
    print("\n" + "=" * 50)
    print("📊 Run Summary:")
    print(f"  • Total Processed: {summary.get('processed', 0)}")
    print(f"  • Total Skipped:   {summary.get('skipped', 0)}")
    print(f"  • Duplicates:      {summary.get('duplicates', 0)}")
    print(f"  • Errors:          {summary.get('errors', 0)}")
    print("=" * 50)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
