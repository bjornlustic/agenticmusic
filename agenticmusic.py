import os
import shutil
import sys

# Define SOUNDS_DIR relative to the script's location
try:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
except NameError:  # Fallback if __file__ is not defined (e.g. interactive)
    SCRIPT_DIR = os.getcwd()
SOUNDS_DIR = os.path.join(SCRIPT_DIR, "sounds")

APP_SOUND_PATHS = {
    "cursor": "/Applications/Cursor.app/Contents/Resources/app/out/vs/platform/accessibilitySignal/browser/media/",
    "windsurf": "/Applications/Windsurf.app/Contents/Resources/app/out/vs/platform/accessibilitySignal/browser/media/",
    "vscode": "/Applications/Visual Studio Code.app/Contents/Resources/app/out/vs/platform/accessibilitySignal/browser/media/"
}

def ensure_sounds_dir_exists():
    """Checks if the 'sounds' directory exists in the script's CWD, creates it if not."""
    if not os.path.isdir(SOUNDS_DIR):
        print(f"'{SOUNDS_DIR}' directory not found. Please create it and add your custom sound files there.")
        # Optionally, create it:
        # print(f"Creating '{SOUNDS_DIR}' directory...")
        # os.makedirs(SOUNDS_DIR)
        # print(f"Please add your custom sound files to the '{SOUNDS_DIR}' directory and re-run.")
        return False
    return True

def get_custom_sounds():
    """Returns a list of sound files in the SOUNDS_DIR."""
    if not os.path.isdir(SOUNDS_DIR):
        return []
    return [f for f in os.listdir(SOUNDS_DIR) if os.path.isfile(os.path.join(SOUNDS_DIR, f)) and not f.startswith('.')]

def install_sounds():
    print("\nSelect an application to replace sounds for:")
    print("1. Cursor")
    print("2. Windsurf")
    print("3. Visual Studio Code")
    print("4. Cancel")

    choice = input("Enter your choice (1-4): ")
    app_key = None
    app_name = None

    if choice == '1':
        app_key = "cursor"
        app_name = "Cursor"
    elif choice == '2':
        app_key = "windsurf"
        app_name = "Windsurf"
    elif choice == '3':
        app_key = "vscode"
        app_name = "Visual Studio Code"
    elif choice == '4':
        print("Installation cancelled.")
        return
    else:
        print("Invalid choice. Please try again.")
        return

    app_media_path = APP_SOUND_PATHS.get(app_key)
    if not app_media_path:
        print(f"Error: Application path for {app_name} not found.")
        return

    if not os.path.isdir(app_media_path):
        print(f"Error: The sound media directory for {app_name} was not found at:")
        print(app_media_path)
        print("Please ensure the application is installed correctly.")
        return

    if not ensure_sounds_dir_exists():
        return
        
    custom_sounds = get_custom_sounds()
    if not custom_sounds:
        print(f"No sound files found in the local '{SOUNDS_DIR}' directory.")
        print("Please add your .wav, .mp3, etc. files to this directory.")
        return

    print(f"\nAttempting to replace sounds for {app_name}...")
    print(f"Application sound directory: {app_media_path}")
    print(f"Custom sounds directory: {os.path.abspath(SOUNDS_DIR)}")

    replaced_count = 0
    permission_error_count = 0

    # Get list of sound files from the application's media directory
    try:
        app_sound_files = [f for f in os.listdir(app_media_path) if os.path.isfile(os.path.join(app_media_path, f))]
    except OSError as e:
        print(f"Error: Could not read application sound directory: {app_media_path}")
        print(f"Details: {e}")
        print("This might be a permissions issue. Try running the script with sudo.")
        return

    for sound_file_name in app_sound_files:
        if sound_file_name in custom_sounds:
            original_app_sound_path = os.path.join(app_media_path, sound_file_name)
            custom_sound_path_source = os.path.join(os.path.abspath(SOUNDS_DIR), sound_file_name) # Source for the symlink

            print(f"  Processing '{sound_file_name}':")
            
            # Check if custom sound source actually exists
            if not os.path.exists(custom_sound_path_source):
                print(f"    - Custom sound '{sound_file_name}' not found in '{SOUNDS_DIR}'. Skipping.")
                continue

            backup_path = original_app_sound_path + ".bak"

            try:
                # 1. Handle existing file/symlink at original_app_sound_path and backup
                if os.path.islink(original_app_sound_path):
                    # If it's already a symlink (e.g., from a previous run)
                    link_target = os.readlink(original_app_sound_path)
                    if link_target == custom_sound_path_source:
                        print(f"    - Already symlinked to the correct custom sound. Skipping.")
                        continue
                    else:
                        print(f"    - Removing existing symlink: {original_app_sound_path} (pointed to {link_target})")
                        os.remove(original_app_sound_path)
                elif os.path.exists(original_app_sound_path):
                    # If it's a regular file, back it up
                    if os.path.exists(backup_path):
                        print(f"    - Backup '{backup_path}' already exists. Assuming it's the correct backup.")
                    else:
                        print(f"    - Backing up original sound to '{backup_path}'")
                        shutil.move(original_app_sound_path, backup_path)
                
                # 2. Create the symlink
                print(f"    - Symlinking '{original_app_sound_path}' -> '{custom_sound_path_source}'")
                os.symlink(custom_sound_path_source, original_app_sound_path)
                replaced_count += 1

            except OSError as e:
                print(f"    - Error processing '{sound_file_name}': {e}")
                if "Operation not permitted" in str(e):
                    permission_error_count += 1
                print(f"      Failed to symlink. Original file (if backed up): {backup_path}")
                # Attempt to restore backup if symlink failed and backup exists
                if os.path.exists(backup_path) and not os.path.exists(original_app_sound_path) and not os.path.islink(original_app_sound_path):
                    try:
                        shutil.move(backup_path, original_app_sound_path)
                        print(f"      Restored original file from backup: {original_app_sound_path}")
                    except Exception as restore_e:
                        print(f"      Could not restore backup for {original_app_sound_path}: {restore_e}")


    if replaced_count > 0:
        print(f"\nSuccessfully replaced and symlinked {replaced_count} sound file(s).")
        print(f"Please restart {app_name} for the changes to take effect.")
    else:
        print("\nNo sound files were replaced. This could be because:")
        print("  - No matching sound files were found between your 'sounds' folder and the app's sound folder.")
        print(f"  - Or, all matching sounds were already correctly symlinked.")

    if permission_error_count > 0:
        print(f"\nWARNING: Encountered {permission_error_count} permission error(s).")
        print("You might need to run this script with administrator privileges (e.g., using 'sudo')")
        print("to modify files in the application directory.")

def revert_sounds():
    print("\nSelect an application to revert sounds for:")
    print("1. Cursor")
    print("2. Windsurf")
    print("3. Visual Studio Code")
    print("4. Revert for ALL listed applications")
    print("5. Cancel")

    choice = input("Enter your choice (1-5): ")
    apps_to_revert = []
    app_names_for_message = []

    if choice == '1':
        apps_to_revert.append("cursor")
        app_names_for_message.append("Cursor")
    elif choice == '2':
        apps_to_revert.append("windsurf")
        app_names_for_message.append("Windsurf")
    elif choice == '3':
        apps_to_revert.append("vscode")
        app_names_for_message.append("Visual Studio Code")
    elif choice == '4':
        apps_to_revert = list(APP_SOUND_PATHS.keys())
        app_names_for_message = ["Cursor", "Windsurf", "Visual Studio Code"]
    elif choice == '5':
        print("Revert operation cancelled.")
        return
    else:
        print("Invalid choice. Please try again.")
        return

    if not apps_to_revert:
        print("No application selected for revert.")
        return

    reverted_total_count = 0
    permission_error_total_count = 0

    for app_key in apps_to_revert:
        app_name = app_key.capitalize() # Simple capitalization, adjust if app names are different
        if app_key == "vscode": app_name = "Visual Studio Code"
        
        app_media_path = APP_SOUND_PATHS.get(app_key)
        if not app_media_path or not os.path.isdir(app_media_path):
            print(f"\nSkipping {app_name}: Sound media directory not found or not accessible ({app_media_path}).")
            continue
        
        print(f"\nAttempting to revert sounds for {app_name}...")
        print(f"Application sound directory: {app_media_path}")

        reverted_app_count = 0
        permission_error_app_count = 0
        
        try:
            all_items_in_app_dir = os.listdir(app_media_path)
        except OSError as e:
            print(f"  Error: Could not read application sound directory: {app_media_path}")
            print(f"  Details: {e}")
            if "Permission denied" in str(e) or "Operation not permitted" in str(e):
                 permission_error_total_count +=1
            continue

        processed_during_bak_restore = set()

        # Pass 1: Restore from .bak files
        print(f"  Pass 1: Restoring from backups for {app_name}...")
        for item_name in all_items_in_app_dir:
            if item_name.endswith(".bak"):
                backup_file_path = os.path.join(app_media_path, item_name)
                original_sound_name = item_name[:-4] #e.g., clear.mp3 from clear.mp3.bak
                original_sound_path = os.path.join(app_media_path, original_sound_name)

                print(f"    Found backup: '{item_name}'. Attempting to restore '{original_sound_name}'.")
                try:
                    # Remove existing original file/symlink if it exists
                    if os.path.lexists(original_sound_path):
                        print(f"      Removing existing '{original_sound_name}' (file or symlink).")
                        os.remove(original_sound_path)
                    
                    shutil.move(backup_file_path, original_sound_path)
                    print(f"      Successfully restored '{original_sound_name}' from '{item_name}'.")
                    reverted_app_count += 1
                    processed_during_bak_restore.add(original_sound_name)
                except OSError as e:
                    print(f"      Error restoring '{original_sound_name}' from backup '{item_name}': {e}")
                    if "Operation not permitted" in str(e) or "Permission denied" in str(e):
                        permission_error_app_count += 1
        
        if not processed_during_bak_restore and not any(f.endswith(".bak") for f in all_items_in_app_dir):
            print("    No .bak files found to restore.")
        elif not processed_during_bak_restore and any(f.endswith(".bak") for f in all_items_in_app_dir):
            print("    Found .bak files, but no corresponding restorations were made (check errors above).")


        # Pass 2: Clean up symlinks made by this script that weren't restored from a .bak
        print(f"  Pass 2: Cleaning up remaining script-made symlinks for {app_name}...")
        cleaned_symlinks_pass2 = 0
        for item_name in all_items_in_app_dir:
            # Skip .bak files themselves, and skip files that were already handled by .bak restoration in Pass 1
            if item_name.endswith(".bak") or item_name in processed_during_bak_restore:
                continue

            current_item_path = os.path.join(app_media_path, item_name)
            if os.path.islink(current_item_path):
                try:
                    link_target_path = os.readlink(current_item_path)
                    # SOUNDS_DIR is now absolute and canonical thanks to the earlier fix
                    if os.path.dirname(link_target_path) == SOUNDS_DIR:
                        print(f"    Found script-made symlink '{item_name}' (target: {link_target_path}).")
                        print(f"    This symlink was not restored from a .bak file. Removing it.")
                        try:
                            os.remove(current_item_path)
                            print(f"      Removed symlink '{item_name}'.")
                            reverted_app_count += 1 # Counting this as a revert action
                            cleaned_symlinks_pass2 +=1
                        except OSError as e:
                            print(f"      Error removing symlink '{item_name}': {e}")
                            if "Operation not permitted" in str(e) or "Permission denied" in str(e):
                                permission_error_app_count += 1
                    # else: # Optional: print if it's a symlink but not ours
                        # print(f"    Skipping symlink '{item_name}' (not pointing to script's sound directory: {os.path.dirname(link_target_path)} vs {SOUNDS_DIR}).")

                except OSError as e: # Error reading link, e.g. broken symlink
                    print(f"    Could not read link '{item_name}', possibly broken: {e}")
        
        if cleaned_symlinks_pass2 == 0 and not any(os.path.islink(os.path.join(app_media_path, i)) for i in all_items_in_app_dir if not i.endswith(".bak") and i not in processed_during_bak_restore):
             print("    No script-made symlinks found to clean up in this pass.")

        if reverted_app_count > 0:
            print(f"  Successfully reverted {reverted_app_count} sound file(s) for {app_name}.")
        else:
            print(f"  No sounds found to revert for {app_name} (or all were already in original state).")
        
        if permission_error_app_count > 0:
            print(f"  Encountered {permission_error_app_count} permission error(s) for {app_name}.")
        
        reverted_total_count += reverted_app_count
        permission_error_total_count += permission_error_app_count


    if reverted_total_count > 0:
        target_app_names_str = ", ".join(app_names_for_message)
        print(f"\nSuccessfully reverted {reverted_total_count} sound file(s) across selected applications.")
        print(f"Please restart {target_app_names_str} for the changes to take full effect.")
    else:
        print("\nNo sound files were reverted for the selected application(s).")

    if permission_error_total_count > 0:
        print(f"\nWARNING: Encountered {permission_error_total_count} permission error(s) in total.")
        print("You might need to run this script with administrator privileges (e.g., using 'sudo')")
        print("to modify files in the application directories.")


def main():
    if not sys.platform == "darwin":
        print("This script is intended for macOS due to specific application paths.")
        # return # Allow to run for testing, but paths will likely fail

    print("Welcome to Agentic Music!")
    while True:
        print("\nMain Menu:")
        print("1. Install/Replace Sounds")
        print("2. Revert Sounds to Original")
        print("3. Exit")
        
        main_choice = input("Enter your choice (1-3): ")

        if main_choice == '1':
            install_sounds()
        elif main_choice == '2':
            revert_sounds()
        elif main_choice == '3':
            print("Exiting Agentic Music. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 3.")

if __name__ == "__main__":
    main() 