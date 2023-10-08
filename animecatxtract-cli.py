from concurrent.futures import ThreadPoolExecutor
import requests
import re
import os

stop_search = False
episode_links = {} 

if os.path.exists('Episodes.txt'):
    os.remove('Episodes.txt')

def reformat_url(input_url):
    url_match_info = re.search(r"https://animecat.net/anime/info/([0-9]+)-([a-z0-9-]+)_(vf|vostfr)", input_url)
    if url_match_info:
        anime_id = url_match_info.group(1)
        anime_name = url_match_info.group(2)
        anime_language = url_match_info.group(3)
        return f"https://animecat.net/anime/episode/{anime_id}-{anime_name}-01_{anime_language}"
    else:
        return input_url

def search_episode(url, episode_number):
    global stop_search
    if stop_search:
        return None
    try:
        response = requests.get(url)
        response.raise_for_status()
        if "<h1>404 Not Found</h1>" in response.text:
            stop_search = True
            return None
        video_link_search = re.search(r"video\[0\] = '(https://fusevideo.io/e/[^']+)';", response.text)
        if video_link_search:
            video_link = video_link_search.group(1)
            episode_links[episode_number] = video_link  
    except requests.RequestException as e:
        if "404 Client Error: Not Found for url:" in str(e):
            stop_search = True

def save_episode():
    global stop_search
    try:
        url = input("Veuillez entrer l'URL de l'épisode à récupérer : ")
        if url.startswith("https://neko-sama.fr/"):
            url = url.replace("https://neko-sama.fr/", "https://animecat.net/")
        url = reformat_url(url)
        url_match = re.search(r"https://animecat.net/anime/episode/([0-9]+)-([a-z0-9-]+)-([0-9]+)_(vf|vostfr)", url)
        if url_match:
            print("Recherche des liens d'épisodes en cours...")
            episode_number = 1
            with ThreadPoolExecutor(max_workers=10) as executor:
                while not stop_search:
                    futures = []
                    for _ in range(10):
                        if stop_search:
                            break
                        new_url = f"https://animecat.net/anime/episode/{url_match.group(1)}-{url_match.group(2)}-{str(episode_number).zfill(2)}_{url_match.group(4)}"
                        futures.append(executor.submit(search_episode, new_url, episode_number))
                        episode_number += 1
                    for future in futures:
                        future.result()
            print("Fin des épisodes trouvés.")
            with open('Episodes.txt', 'a', encoding='utf-8') as f:
                for episode_number in sorted(episode_links.keys()):
                    f.write(f"Episode {episode_number} : {episode_links[episode_number]}\n\n")
        else:
            print("L'URL fournie ne correspond pas au format attendu.")
    except KeyboardInterrupt:
        print("La recherche a été interrompue manuellement.")
        exit()

if __name__ == "__main__":
    save_episode()
