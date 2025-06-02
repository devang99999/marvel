import os

def list_files_excluding_node_modules(start_path):
    for root, dirs, files in os.walk(start_path):
        # Exclude node_modules from directories to be walked
        dirs[:] = [d for d in dirs if d != 'node_modules']
        dirs[:] = [d for d in dirs if d != '.git']

        # Print directory path
        print(root)

        # Print all files in the current directory
        for file in files:
            print(os.path.join(root, file))

if __name__ == "__main__":
    # Change this to the directory you want to start from, or use '.' for current directory
    start_directory = '.'
    list_files_excluding_node_modules(start_directory)
