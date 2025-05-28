import os
import shutil

def clear_folder(path):
    if os.path.exists(path) and os.path.isdir(path):
        try:
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            print(f" Cleared contents of folder: {path}")
        except Exception as e:
            print(f"Failed to clear folder: {e}")
