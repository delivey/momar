import os
import os.path
import requests
from bs4 import BeautifulSoup
import json
from colorama import init, Fore
from os import system, name
import difflib
import subprocess
init(autoreset=True)

# Developer
LOAD_CACHED_ON_STARTUP = True

# User
DISCARD_PARTIAL_DATA = True
YELLOW_RATING_THRESHOLD = 6
GREEN_RATING_THRESHOLD = 8
DATA_FILENAME = "data.json"
DIRECTORY = "D:\Torrents"

class MovieManager:
    def __init__(self, directory, data_filename):
        self.directory = directory
        self.extensions = [".mp4", ".mkv"]
        self.movies = []
        self.movies_paths = []
        self.discarded = []
        self.first_time = True

        self.genre = "All"
        self.sort = "rating"
        self.sortway = "desc"

        datafile = open(data_filename)
        self.data = json.load(datafile)

    def is_integer(self, str):
        try:
            int(str)
            return True
        except ValueError:
            return False

    def cap_sentence(self, s):
        return ' '.join(w[:1].upper() + w[1:] for w in s.split(' '))

    # TODO: make more complete
    def is_show(self, name):
        name = name.upper()
        for idx, letter in enumerate(name):
            if letter == "S":
                season_string = name[idx:idx+6]
                digits = len([ch for ch in season_string if ch.isdigit()])
                if "E" in season_string and digits == 4:
                    return True
        return False

    def save_data(self):
        with open(DATA_FILENAME, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)

    def get_movie_names(self):
        for dirpath, dirnames, filenames in os.walk(self.directory):
            for filename in [f for f in filenames]:
                if filename[-4:] in self.extensions and not self.is_show(filename):
                    filename = filename.replace(" ", ".")
                    movie_name_parts = filename.split(".")
                    movie_name = ""
                    for idx, i in enumerate(movie_name_parts):
                        if i.isdigit() and len(i) == 4:
                            movie_name = self.cap_sentence(
                                " ".join(movie_name_parts[:idx])) + f" {i}"
                            break
                    if movie_name:
                        full_path = f"{dirpath}\\{filename}"
                        self.movies_paths.append(full_path)
                        self.movies.append(movie_name)

    def get_movie_data(self):
        for idx, movie in enumerate(self.movies):
            imdb = self.get_imdb_id(movie, idx)
            self.get_imdb_data(imdb, movie, idx)
        return self.data

    def get_movies(self):
        self.get_movie_names()
        self.get_movie_data()
        self.save_data()
        if self.first_time: self.first_time = False
        return self.data

    def get_imdb_data(self, id, name, idx):
        try:
            return self.data[name]["data"]
        except KeyError:
            url = f"https://www.imdb.com/title/{id}/"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            djson = json.loads(soup.find('script', type='application/json', id='__NEXT_DATA__').string)

            try:
                length = djson["props"]["pageProps"]["aboveTheFoldData"]["runtime"]["seconds"]
            except TypeError:
                if DISCARD_PARTIAL_DATA:
                    del self.data[name]
                    self.discarded.append(name)
                    return False
                length = 0

            rating = djson["props"]["pageProps"]["aboveTheFoldData"]["ratingsSummary"]["aggregateRating"]
            genres = djson["props"]["pageProps"]["aboveTheFoldData"]["genres"]["genres"]
            genres = [genre["text"] for genre in genres]

            if rating == None:
                self.discarded.append(name)
                del self.data[name]
                return False

            simplified = {
                "length": length,
                "rating": rating,
                "genres": genres,
                "path": self.movies_paths[idx]
            }

            self.data[name]["data"] = simplified
            return simplified

    def get_imdb_id(self, name, idx):
        try:
            return self.data[name]["id"]
        except KeyError:
            params = {
                'q': name,
                's': 'tt',
                'ttype': 'ft',
                'ref_': 'fn_ft',
            }
            r = requests.get("https://www.imdb.com/find", params=params)
            soup = BeautifulSoup(r.text, "html.parser")
            result = str(soup.select_one('td.result_text'))
            id = result[result.index('href="/title/') + len('href="/title/'):result.index('/"')]

            self.data[name] = {"id": id, "idx": idx}

            return id

    def show_movies(self, predefined_data=False):
        if self.first_time and not LOAD_CACHED_ON_STARTUP:
            movies = self.get_movies()
        else:
            movies = self.data

        reverse = self.sortway == "desc"
        if self.sort == "rating":
            sorted_movies = dict(sorted(movies.items(), key=lambda item: item[1]["data"]["rating"], reverse=reverse))
        elif self.sort == "year":
            sorted_movies = dict(sorted(movies.items(), key=lambda item: int(item[0].split(" ")[-1]), reverse=reverse))

        idx = 0
        for name, mdata in sorted_movies.items():
            ddata = mdata
            mdata = mdata["data"]
            idx+=1

            correct_genre = (self.genre == "All")
            if not correct_genre and 'genres' in mdata:
                for genre in mdata["genres"]:
                    if genre == self.genre: correct_genre = True

            if correct_genre:
                if mdata["rating"] >= GREEN_RATING_THRESHOLD: color = Fore.GREEN
                elif mdata["rating"] >= YELLOW_RATING_THRESHOLD: color = Fore.YELLOW
                else: color = Fore.RED

                if predefined_data:
                    if name in predefined_data:
                        print(color + f"{ddata['idx']}. ({mdata['rating']}) {name}: {', '.join(mdata['genres'])}. ")
                else:
                    print(color + f"{ddata['idx']}. ({mdata['rating']}) {name}: {', '.join(mdata['genres'])}. ")

class CommandManager:
    def __init__(self, manager):
        self.validCommands = ["discarded", "movies", "genre", "clear", "sort", "search", "open"]
        self.parameterCommands = ["genre", "sort", "search", "open"]

    def validCommand(self, command):
        valid = False
        if command in self.validCommands: valid = True
        if any(map(command.startswith, self.parameterCommands)): valid = True
        return valid

    def showDiscarded(self):
        print(Fore.GREEN + ", ".join(manager.discarded))

    def sortMovies(self, command):
        sort_ways = ["rating", "year"]
        sortway_ways = ["desc", "asc"]
        command_length = len(command.split(" "))

        if command_length >= 2:
            sort = command.split(" ")[1].lower()
            if not sort in sort_ways:
                print(Fore.RED + "No such sorting method.")
            manager.sort = sort
            if command_length == 3:
                sortway = command.split(" ")[2].lower()
                if not sortway in sortway_ways:
                    print(Fore.RED + "No such sorting way.")
                manager.sortway = sortway
            else:
                print(Fore.RED + "Too many arguments supplied.")

        elif command_length == 1:
            print(Fore.GREEN + manager.sort)

    def showGenre(self, command):
        command_length = len(command.split(" "))
        if command_length == 2:
            genre = command.split(" ")[1].capitalize()
            manager.genre = genre
        elif command_length == 1:
            print(Fore.GREEN + manager.genre)

    def getMoviePath(self, id):
        for key, value in manager.data.items():
            if id == value["idx"]:
                return value["data"]["path"]

    def clearScreen(self):
        if name == 'nt': system('cls')
        else: system('clear')

    def searchMovies(self, command): # TODO Implement more robust algorithm, make it possible to have more than 1 result
        splitc = command.split(" ")
        movie = " ".join(splitc[1:])
       
        movies = list(manager.data)
        found = difflib.get_close_matches(movie, movies)
        
        if found: manager.show_movies(found)

    def openMovie(self, command): 
        splitc = command.split(" ")
        movie_id = int(splitc[1])
        path = self.getMoviePath(movie_id)
        subprocess.Popen(f'explorer /select,{path}')

    def doCommand(self, com):
        comdict = {
            "discarded": self.showDiscarded,
            "movies": manager.show_movies,
            "genre": self.showGenre,
            "clear": self.clearScreen,
            "sort": self.sortMovies,
            "search": self.searchMovies,
            "open": self.openMovie
        }
        first = com.split(" ")[0]
        if not first in self.parameterCommands:
            comdict[com]()
        else:
            comdict[first](com)
        return True

    def askCommand(self):
        print(Fore.CYAN + ": ", end="")
        com = input()
        valid = self.validCommand(com)
        if valid:
            self.doCommand(com)
            return True
        else:
            print(Fore.RED + "X")
            return False


manager = MovieManager(DIRECTORY, DATA_FILENAME)
manager.show_movies()

command = CommandManager(manager)
while True:
    try:
        command.askCommand()
    except KeyboardInterrupt:
        break