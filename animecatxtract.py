from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox, filedialog, ttk
import tkinter as tk
import httpx
import re

icon_path = "animecat.ico"

stop_search = False
episode_links = {} 

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
    try:
        with httpx.Client() as client:
            response = client.get(url)
        if response.status_code == 404 or "<h1>404 Not Found</h1>" in response.text:
            stop_search = True
            return None
        video_link_search = re.search(r"video\[0\] = '(https://fusevideo.io/e/[^']+)';", response.text)
        if video_link_search:
            video_link = video_link_search.group(1)
            episode_links[episode_number] = video_link
    except httpx.RequestError as e:
        if "404 Client Error: Not Found for url:" in str(e):
            stop_search = True

def save_episode(url):
    global stop_search
    url = reformat_url(url)
    url_match = re.search(r"https://animecat.net/anime/episode/([0-9]+)-([a-z0-9-]+)-([0-9]+)_(vf|vostfr)", url)
    if url_match:
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
        # Créez une variable pour stocker le texte qui sera inséré dans le widget tk.Text
        text_to_insert = ""
        for episode_number in sorted(episode_links.keys()):
            text_to_insert += f"Episode {episode_number} : {episode_links[episode_number]}\n\n"
        # Insérez le texte dans le widget tk.Text
        url_text.delete(1.0, tk.END)
        url_text.insert(tk.END, text_to_insert)

def normalize_url(url):
    for prefix in ["https://neko-sama.fr/", "https://www.neko-sama.fr/", "https://www.animecat.net/"]:
        if url.startswith(prefix):
            return url.replace(prefix, "https://animecat.net/")
    return url

def on_submit():
    global episode_links, stop_search
    episode_links.clear()
    stop_search = False
    url_text.delete(1.0, tk.END)
    url = url_entry.get()
    url = normalize_url(url)
    if not url.startswith("https://animecat.net/"):
        messagebox.showerror("Erreur", "L'URL doit commencer par 'https://animecat.net/'.")
        return
    save_episode(url)

# Fonction pour enregistrer le fichier
def save_to_file():
    text_to_save = url_text.get("1.0", tk.END)
    if text_to_save.strip():  # vérifie si le texte n'est pas vide
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_to_save)

# Fonction pour clear [Thx Sukuna]
def clear_entry():
    url_entry.delete(0, tk.END)
    url_text.delete(1.0, tk.END)

window = tk.Tk()
window.title("AnimecatXtract")
try:
    window.iconbitmap(default=icon_path)
except tk.TclError:
    pass
window.resizable(0, 0)
window.configure(background="#F5F5F5")
url_label = tk.Label(window, text="Entrez l'URL de départ :", font=("Helvetica", 14), fg="#333333", bg="#F5F5F5")
url_label.grid(row=0, column=0, padx=5, pady=5)
url_entry = ttk.Entry(window, width=30, font=("Helvetica", 14))
url_entry.grid(row=0, column=1, padx=5, pady=5)
# Bouton Extraire les liens
submit_button = tk.Button(window, text="Extract", font=("Helvetica", 14), bg="#333333", fg="#FFFFFF", command=on_submit)
submit_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
# Bouton Enregistrer
save_button = tk.Button(window, text="Save", font=("Helvetica", 14), bg="#333333", fg="#FFFFFF", command=save_to_file)
save_button.grid(row=1, column=1, padx=8, pady=5) 
# Bouton Clear [Thx Sukuna]
clear_button = tk.Button(window, text="Clear", font=("Helvetica", 14), bg="#333333", fg="#FFFFFF", command=clear_entry)
clear_button.grid(row=1, column=1, padx=(200,5), pady=5)
# Sortie des liens
url_text = tk.Text(window, width=50, height=20, font=("Helvetica", 14))
url_text.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
# Vouton Infos
def show_info():
    tk.messagebox.showinfo("Infos", "Version: 1.0\nContact: Showzur#0001")
info_button = tk.Button(window, text="i", font=("Helvetica", 14), fg="#333333", bg="#F5F5F5", bd=0, command=show_info)
info_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

window.mainloop()
