import os
import os.path
import requests
from bs4 import BeautifulSoup

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

movies = []

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
                movies.append(movie_name)

def get_imdb_id(name):
    params = {
        'q': name,
        's': 'tt',
        'ttype': 'ft',
        'ref_': 'fn_ft',
    }
    r = requests.get("https://www.imdb.com/find", params=params)
    soup = BeautifulSoup(r.text, "html.parser")
    result = str(soup.select_one('td.result_text'))
    id = result[result.index('href="/title/')+len('href="/title/'):result.index('/"')]
    return id


for idx, movie in enumerate(movies):
    imdb = get_imdb_id(movie)
    print(f"{idx}. {movie}: {imdb}")