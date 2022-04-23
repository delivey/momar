import os
import os.path

def is_integer(str):
    try:
        int(str)
        return True
    except ValueError:
        return False

def cap_sentence(s):
  return ' '.join(w[:1].upper() + w[1:] for w in s.split(' ')) 

# TODO: make more complete
def is_show(name):
    name = name.upper()
    for idx, letter in enumerate(name):
        if letter == "S":
            season_string = name[idx:idx+6]
            digits = len([ch for ch in season_string if ch.isdigit()])
            if "E" in season_string and digits == 4:
                return True
    return False


directory = "D:\Torrents"
extensions = [".mp4", ".mkv"]

for dirpath, dirnames, filenames in os.walk(directory):
    for filename in [f for f in filenames]:
        if filename[-4:] in extensions and not is_show(filename):
            filename = filename.replace(" ", ".")
            movie_name_parts = filename.split(".")
            movie_name = ""
            for idx, i in enumerate(movie_name_parts):
                if i.isdigit() and len(i) == 4:
                    movie_name = cap_sentence(" ".join(movie_name_parts[:idx])) + f" {i}"
                    break
            if movie_name:
                print(movie_name + ":                          " + filename) 