import json
import os
import requests

def load_movies():
   try:

        with open("movies.json", "r") as f:
            return json.load(f)
   except FileNotFoundError:
       print("No movies.json file found")

def paginate(dataset, page, page_size):
    start = (page - 1) * page_size
    end = start + page_size
    return dataset[start:end]

def download_poster(title,poster):
    base_dir = r"C:\Users\DAVID\PyCharmMiscProject\MEDIA LIBRARY PROJECT\posters"


    poster_url = poster
    if poster_url and poster_url != 'N/A':
        try:
            safe_title = title.lower().replace(' ', '_').replace(':', '').replace('\\', '').replace('/',
                                                                                                          '')
            filename = f"{safe_title}.jpg"
            poster_path = os.path.join(base_dir, filename)
            if os.path.exists(poster_path):
                print(f"Poster exists: {filename}")
                return poster_path

            print(f"Downloading poster: {filename}")
            response = requests.get(poster_url, timeout=10)
            response.raise_for_status()

            with open(poster_path, 'wb') as f:
                f.write(response.content)


            return poster_path
        except Exception as e:
            print(f"Poster failed: {e}")
    else:
        print(f"No poster URL for {title}")
        return None