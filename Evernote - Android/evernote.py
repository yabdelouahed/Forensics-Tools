import sqlite3
import os
import shutil
from random import randrange



def normalize_filename(fn):
    valid_chars = "-_.()"
    out = ""
    for c in fn:
        if str.isalpha(c) or str.isdigit(c) or (c in valid_chars):
            out += c
        else:
            out += "_"
    return out


def read_db(table, id=""):
    conn = sqlite3.connect(DATABASE_PATH)
    # create a coursor
    c = conn.cursor()
    # print("Start reading")
    if table == "notebooks":
        c.execute("SELECT guid, name, stack FROM notebooks ORDER BY stack")
    elif table == "notes":
        query = "SELECT guid, title FROM notes WHERE notebook_guid=\'" + id + "\'"
        c.execute(query)
    else:
        c.execute("SELECT guid, name, stack FROM notes")

    return c.fetchall()


def create_folder(parent_dir, dir):
    path = os.path.join(parent_dir, dir)
    if not os.path.exists(path):
        os.mkdir(path)


def copy_files(src, dest, note_title, folder_name):
    # "normalizing" the folder name so that it contains only allowed characters
    new_note_title = normalize_filename(str(note_title))

    # Verhindern das Problem, wenn Notizen der gleiche Titel haben
    while os.path.exists(os.path.join(dest, new_note_title)):
        new_note_title += "_R" + str(randrange(1000))

    # set the new folder name according to the note title
    dest_folder = os.path.join(dest, new_note_title)
    create_folder(dest, new_note_title)

    src_files = os.listdir(src)
    for file_name in src_files:
        full_file_name = os.path.join(src, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, dest_folder)
            extension = os.path.splitext(full_file_name)[1]
            # filter the files according the extension
            if extension == ".enml":
                source = os.path.join(dest_folder, full_file_name.split('\\')[-1])
                destination = os.path.splitext(source)[0] + ".html"
                shutil.move(source, destination)
                #  Editing the content of the HTML File => "en-media hash" to "img src"
                edit_html(destination)
            elif extension == ".dat":
                source = os.path.join(dest_folder, full_file_name.split('\\')[-1])
                destination = os.path.splitext(source)[0]
                shutil.move(source, destination)


# adjust the html file
def edit_html(source_file):
    # open the html file, adjust the substr "en-media hash" to "img src"
    with open(source_file, "rt", encoding="UTF-8") as f:
        new_text = f.read().replace('en-media hash', 'img src')
    # save the changes to the file
    with open(source_file, "wt", encoding="UTF-8") as f:
        f.write(new_text)


# find the note directory with the help of the guid
def find_dir(name, path):
    # ignore the linked folder
    substr = "linked"
    for root, subdirs, files in os.walk(path):
        if substr in root:
            continue
        for d in subdirs:
            if d == name and substr not in d:
                return os.path.join(root, name)


def find_and_extract(dest_folder,notebook_name,notebook_id):
    # create notebook folder
    create_folder(dest_folder, normalize_filename(notebook_name))
    # remember the current notebook path
    notebook_path = os.path.join(dest_folder, normalize_filename(notebook_name))
    # read the database notes and filter the notes after the current notebook_guid
    notes_result = read_db("notes", notebook_id)
    for note in notes_result:
        note_titel = note[1]
        note_id = note[0]
        # with the held of note_id find where the desired note_folder "X" lies
        folder_path = find_dir(note_id, source_path)
        if folder_path is None:
            continue
        copy_files(folder_path, notebook_path, note_titel, note_id)

# Directory
directory = "Evernote"
# the source path
source_path = input("Please enter the source/package path of the evernote: ")
# database path
DATABASE_PATH = input("Please enter the database path(/com.evenote/databases/user...): ")
# Parent Directory path
parent_dir = input("Please enter where you want to save the results: ")

# Create Results folder
create_folder(parent_dir, directory)
path = os.path.join(parent_dir, directory)

# Read the notebook database
results = read_db("notebooks")

# help variables
current_stack = ""
def_path = path
current_path = path

print("Starting the extraction")
# x steht für derzeitige Notebook von der Liste results
for x in results:
    notebook_name = x[1]
    notebook_id = x[0]
    notebook_parent = x[2]

    # incase a notebook "x[2]" did't belong to a certain stack
    if notebook_parent is None:
        find_and_extract(def_path, notebook_name, notebook_id)
        continue

    # organise the stack
    if notebook_parent != current_stack:
        current_stack = normalize_filename(notebook_parent)
        # set the current path to the stack folder path
        current_path = os.path.join(def_path, current_stack)
        # create stack folder
        create_folder(def_path, current_stack)

    find_and_extract(current_path, notebook_name, notebook_id)



input("Done, Press Enter to continue...")