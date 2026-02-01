
import os

files = ["error.log", "crash_log.txt"]
for f in files:
    if os.path.exists(f):
        print(f"--- CONTENT OF {f} ---")
        try:
            with open(f, 'r', encoding='utf-16') as file:
                print(file.read())
        except Exception as e:
            print(f"Error reading {f} as utf-16: {e}")
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    print(file.read())
            except Exception as e2:
                print(f"Error reading {f} as utf-8: {e2}")
    else:
        print(f"{f} does not exist.")
