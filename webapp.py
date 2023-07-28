import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import psycopg2
import json
import requests

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances
import random

# Spotify app credentials
CLIENT_ID = '082a6c8cea8f48f7bc50c687cef53094'
CLIENT_SECRET = 'edf5b55bb67f40b2be9b00b6b6d57fb8'
REDIRECT_URI =  'http://localhost:8501/'

# Database credentials
DB_HOST = 'localhost'
DB_NAME = 'USERS'
DB_USER = 'MachineMinds'
DB_PASSWORD = 'MachineMinds'

# Create a Spotipy client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope = 'user-library-read playlist-read-private user-read-email user-follow-modify'))

connection = psycopg2.connect(
    host=DB_HOST,
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# Apply the custom theme
st.set_page_config(
    page_title="Music Web App",
    page_icon="🎵",
    layout="wide",  # Optional, choose 'wide' or 'centered'
)

data = pd.read_csv("data/data.csv")

song_info_features = ['name', 'artists', 'id', 'release_date', 'year', 'popularity']
song_features_normalized = ['valence', 'acousticness', 'danceability', 'energy', 'instrumentalness', 'liveness', 'speechiness']
song_features_not_normalized = ['duration_ms', 'key', 'loudness', 'mode', 'tempo']

# Features that will be used for similarity testing
features = song_features_normalized + song_features_not_normalized + ['popularity', 'year']

scaler = StandardScaler()
feature_scaled = scaler.fit_transform(data[features])

final_data = data.copy()
final_data[features] = feature_scaled

id_playlists = []
top_artists_ids = [
    "6qqNVTkY8uBg9cP3Jd7DAH",  # Billie Eilish
    "6eUKZXaKkcviH0Ku9w2n3V",  # Ed Sheeran
    "3TVXtAsR1Inumwj472S9r4",  # Drake
    "66CXWjxzNUsdJxJ2JdwvnR",  # Ariana Grande
    "3Nrfpe0tUJi4K4DXYWgMUX",  # BTS
    "246dkjvS1zLTtiykXe5h60",  # Post Malone
    "06HL4z0CvFAxyc27GXpf02",  # Taylor Swift
    "1Xyo4u8uXC1ZmMpatF05PJ",  # The Weeknd
    "6M2wZ9GZgrQXHCFfjv46we",  # Dua Lipa
    "1uNFoZAHBGtllmzznpCI3s",
]

def follow_artist(artist_id):
    try:
        # Follow the artist using the Spotify API
        sp.user_follow_artists([artist_id])
        return True
    except Exception as e:
        print(f"Error following artist: {e}")
        return False
    
# Functions for the welcome page
def get_new_releases_for_artists(artists, country, limit):
    st.subheader("Top Artists you may like")

# Define the CSS style for centering text
    centered_text_style = "text-align: center; white-space: pre-wrap;"

    # Get the number of artists to display in each row
    num_artists_per_row = 5

    # Iterate through the list of artist IDs and fetch the artist details
    for i in range(0, limit, num_artists_per_row):
        # Create columns for each row
        cols = st.columns(num_artists_per_row)
        
        for j in range(num_artists_per_row):
            if i + j < len(artists):
                artist_info = sp.artist(artists[i + j])
                
                followers = artist_info['followers']['total']
                artist_name = artist_info['name']
                artist_image_url = artist_info['images'][0]['url']
                popularity = artist_info['popularity']
                
                # Display the artist image and details in the current column
                with cols[j]:
                    st.image(artist_image_url, caption="", width=150)
                    st.write(f"**{artist_name}**", style=centered_text_style)
                    st.write(f"Followers: {followers}", style=centered_text_style)
                    st.write(f"Popularity: {popularity}", style=centered_text_style)
                    follow_button_clicked = st.button(f"Follow {artist_name}", key=f"follow_button_{artist_name}")

                # Check if the follow button is clicked and take appropriate action
                    if follow_button_clicked:
                        follow_result = follow_artist(artist_info['id'])
                        if follow_result:
                            st.success(f"You are now following {artist_name}!")
                        else:
                            st.error(f"Failed to follow {artist_name}. Please try again later.")
        
def get_new_releases(country, limit):
    # Use the new_releases endpoint to get new album releases
    new_releases = sp.new_releases(country=country, limit=limit)

# Display the new releases in a horizontal manner
    if new_releases:
        st.subheader("New Releases")
        num_cols = 5  # Number of columns in the horizontal layout
        col_idx = 0
        cols = st.columns(num_cols)

        for album in new_releases['albums']['items']:
            album_name = album['name']
            artist_name = album['artists'][0]['name']
            album_image_url = album['images'][0]['url']
            
            # Display the album image and details in the current column
            with cols[col_idx % num_cols]:
                st.image(album_image_url, caption=f"Album: {album_name}", width=150)
            
            col_idx += 1

def show_user_profile():
    user_data = sp.current_user()
    st.sidebar.subheader("User Profile")
    st.sidebar.write(f"Display Name: {user_data['display_name']}")
    st.sidebar.write(f"User ID: {user_data['id']}")

def show_liked_songs(num_songs_per_page):
    st.subheader("Liked Songs")
    liked_songs = sp.current_user_saved_tracks()
    num_songs = len(liked_songs['items'])
    num_pages = (num_songs + num_songs_per_page - 1) // num_songs_per_page

    current_page = st.session_state.get("current_page", 1)

    start_idx = (current_page - 1) * num_songs_per_page
    end_idx = min(start_idx + num_songs_per_page, num_songs)

    liked_songs_page = liked_songs['items'][start_idx:end_idx]
    col1, col2, col3, col4,col5 = st.columns(num_songs_per_page)

    for idx, item in enumerate(liked_songs_page):
        track = item['track']
        song_id = track['id']  # Get the song's ID to use as a unique key
        with col1 if idx == 0 else col2 if idx == 1 else col3 if idx == 2 else col4 if idx == 3 else col5:
            image_url = track['album']['images'][0]['url']
            caption = track['name']
            if st.image(image_url, caption=caption, width=150, use_column_width='auto'):
                # If the image is clicked, play the audio
                audio_preview_url = track['preview_url']
                if audio_preview_url:
                    st.audio(audio_preview_url, format='audio/mp3', start_time=0)

    if num_pages > 1:
        col1, col2, col3 = st.columns([1, 10, 1])  # Create three columns with different widths
        prev_button_clicked = col2.button("Previous", key="prev_button")  # Place the "Previous" button in the second column
        col3.empty()  # Add an empty spacer in the third column
        next_button_clicked = col3.button("Next", key="next_button")  # Place the "Next" button in the third column

    if prev_button_clicked and current_page > 1:
        current_page -= 1
        st.session_state.current_page = current_page

    if next_button_clicked and current_page < num_pages:
        current_page += 1
        st.session_state.current_page = current_page

def show_user_playlists():
    st.subheader("Playlists")
    playlists = sp.current_user_playlists(limit=5)
    #st.write(playlists)
    for playlist in playlists['items']:
        if playlist['images']:
            st.image(playlist['images'][0]['url'], caption=playlist['name'], width=150)
            id_playlists.append(playlist['id'])
        else:
            st.image("https://via.placeholder.com/150", caption=playlist['name'], width=150)

def get_playlist_items(playlist_id):
    # Retrieve the playlist items using the playlist ID
    results = sp.playlist_tracks(playlist_id)

    # Process the results and extract the track details
    playlist_items = []
    for item in results['items']:
        track = item['track']
        track_id = track['id']
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        album_name = track['album']['name']
        track_image_url = track['album']['images'][0]['url']
        playlist_items.append({
            'track_id': track_id,
            'track_name': track_name,
            'artist_name': artist_name,
            'album_name': album_name,
            'track_image_url': track_image_url
        })

    # Display the playlist items in a horizontal layout
    num_cols = 4  # Number of columns for the horizontal layout
    cols = st.columns(num_cols)
    for idx, item in enumerate(playlist_items, 1):
        with cols[idx % num_cols]:
            st.image(item['track_image_url'], caption=f"Track: {item['track_name']}", width=150)

def get_spotify_track_details(track_id):
    track_info = sp.track(track_id)
    return track_info

# Function to show song recommendations in the web app
def show_song_recommendations(user_id):
    st.header("Discover New Songs")

    st.subheader("Choose an option")
    # Option to enter song manually or select from dropdown
    option = st.radio('Options',("Enter a song manually", "Select from all songs"))
    if option == "Enter a song manually":
        song_name = st.text_input("Enter a song name", "")
        if song_name:
            api_url = "http://localhost:8000/recommend-song/"  # Replace with the correct URL of your FastAPI API
            data = {"song_name": song_name}
            response = requests.post(api_url, json=data)

            if response.status_code == 200:
                recommendations = response.json()
                if recommendations:
                    st.subheader("Song Recommendations")
                    num_cols = 4
                    col_idx = 0
                    for recommendation in recommendations:
                        split_string = recommendation["song_name_year"].split("(")
                        song_name_year = split_string[0].strip()
                        similarity_percentage = recommendation["similarity_percentage"]
                        #st.write(f"{song_name_year} - Similarity Percentage: {similarity_percentage:.2f}%")

                        song_id = recommendation["song_id"]
                        track_info = get_spotify_track_details(song_id)
                        track_image_url = track_info["album"]["images"][0]["url"]
                        audio_preview_url = track_info["preview_url"]

                        if col_idx % num_cols == 0:
                            cols = st.columns(num_cols)

                        # Display the image and song details in the current column
                        with cols[col_idx % num_cols]:
                            st.image(track_image_url, width=200)
                            st.write(f"Song: {song_name_year}")
                            st.write(f"Similarity: {similarity_percentage:.2f}")
                            if audio_preview_url:
                                if st.image(track_image_url, width=50):
                                    st.audio(audio_preview_url, format='audio/mp3', start_time=0)
                            st.write("\n")
                        col_idx += 1
                else:
                    st.error("No song recommendations found for the given song.")
            else:
                st.error("Error retrieving song recommendations from the API.")

    elif option == "Select from all songs":
        # Load all song names from the dataset into a list
        all_song_names = final_data['name'].unique().tolist()
        selected_song = st.selectbox("Select a song", all_song_names)
        if selected_song:
            api_url = "http://localhost:8000/recommend-song/"  # Replace with the correct URL of your FastAPI API
            data = {"song_name": selected_song}
            response = requests.post(api_url, json=data)
            
            if response.status_code == 200:
                recommendations = response.json()
                if recommendations:
                    st.subheader("Song Recommendations")
                    num_cols = 4
                    col_idx = 0
                    for recommendation in recommendations:
                        split_string = recommendation["song_name_year"].split("(")
                        song_name_year = split_string[0].strip()
                        similarity_percentage = recommendation["similarity_percentage"]
                        #st.write(f"{song_name_year} - Similarity Percentage: {similarity_percentage:.2f}%")

                        song_id = recommendation["song_id"]
                        track_info = get_spotify_track_details(song_id)
                        track_image_url = track_info["album"]["images"][0]["url"]
                        audio_preview_url = track_info["preview_url"]

                        if col_idx % num_cols == 0:
                            cols = st.columns(num_cols)

                        # Display the image and song details in the current column
                        with cols[col_idx % num_cols]:
                            st.image(track_image_url, width=200)
                            st.write(f"Song: {song_name_year}")
                            st.write(f"Similarity: {similarity_percentage:.2f}")
                            if audio_preview_url:
                                if st.image(track_image_url, width=50):
                                    st.audio(audio_preview_url, format='audio/mp3', start_time=0)
                            st.write("\n")
                            
                        col_idx += 1
                else:
                    st.error("No song recommendations found for the selected song.")
            else:
                st.error("Error retrieving song recommendations from the API.")

import requests
import random
from googleapiclient.discovery import build

# Function to get YouTube search results for a given song and artist
def youtube_search(song_name, artist_name, api_key, max_results=1):
    youtube = build('youtube', 'v3', developerKey=api_key)
    search_query = f"{song_name} {artist_name}"
    search_response = youtube.search().list(q=search_query, part='id', type='video', maxResults=max_results).execute()
    videos = []

    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append(search_result['id']['videoId'])

    return videos

def artist_recommendations(user_id):
    st.header("Songs you may like")
    # Option to enter song manually or select from dropdown
    # option = st.radio("Choose an option:", ("Enter a song manually", "Select from all songs"))

    uiD = '15415fa2745b344bce958967c346f2a89f792f63'
    if uiD:
        api_url = "http://localhost:8000/recommend-artist/"
        data = {"user_id": uiD}
        response = requests.post(api_url, json=data)

        if response.status_code == 200:
            recommendations = response.json()
            # st.write(response.status_code)
            if recommendations:
                st.subheader("Top 5 Similar Song Recommendations")
                st.subheader("")

                # Separate the top 5 recommendations and 3 random recommendations
                top_5_similar = recommendations[:5]
                random_3_songs = random.sample(recommendations[5:], 3)

                num_cols = 2
                col_idx = 0

                # Display the top 5 similar song recommendations
                for i, song_data in enumerate(top_5_similar, 1):
                    song_id = song_data["song_id"]
                    artist_name = song_data["song_name"]
                    song_name = song_data["artist_name"]
                    predicted_rating = song_data["predicted_rating"]
                    image_url = "image.jpg"

                    # Get YouTube video link for the song
                    youtube_api_key = "AIzaSyATSqsxXw4x16KCaNcz8XYM0Wvq07ubKY8"
                    video_ids = youtube_search(song_name, artist_name, youtube_api_key)
                    youtube_link = f"https://www.youtube.com/watch?v={video_ids[0]}" if video_ids else "N/A"

                    # Create a horizontal layout with the specified number of columns
                    if col_idx % num_cols == 0:
                        cols = st.columns(num_cols)

                    # Display the image and song details in the current column
                    with cols[col_idx % num_cols]:
                        st.image(image_url, width=200)
                        st.write(f"Artist: {artist_name}")
                        st.write(f"Song: {song_name}")
                        st.write(f"Predicted Rating: {predicted_rating:.2f}")
                        st.write(f"YouTube Link: {youtube_link}")

                    col_idx += 1

                # Display the 3 random song recommendations
                st.subheader("3 Random Song Recommendations")
                st.subheader("Discover new genres :)")

                num_cols = 1
                col_idx = 0

                for i, song_data in enumerate(random_3_songs, 1):
                    song_id = song_data["song_id"]
                    artist_name = song_data["song_name"]
                    song_name = song_data["artist_name"]
                    image_url = "image.jpg"

                    # Get YouTube video link for the song
                    youtube_api_key = "AIzaSyATSqsxXw4x16KCaNcz8XYM0Wvq07ubKY8"
                    video_ids = youtube_search(song_name, artist_name, youtube_api_key)
                    youtube_link = f"https://www.youtube.com/watch?v={video_ids[0]}" if video_ids else "N/A"

                    # Create a horizontal layout with the specified number of columns
                    if col_idx % num_cols == 0:
                        cols = st.columns(num_cols)

                    # Display the image and song details in the current column
                    with cols[col_idx % num_cols]:
                        st.image(image_url, width=200)
                        st.write(f"Artist: {artist_name}")
                        st.write(f"Song: {song_name}")
                        st.write(f"YouTube Link: {youtube_link}")

                    col_idx += 1
            else:
                st.error("No song recommendations found for the user.")
        else:
            st.write(response)
            st.error("Error retrieving song recommendations.")
    else:
        st.error("Invalid user ID.")

def get_access_token():
    auth_code = st.experimental_get_query_params().get("code", "")
    if auth_code:
        try:
            sp.auth_manager.get_access_token(auth_code[0], as_dict=False)
            return True
        except Exception as e:
            st.exception(e)
            return False
    else:
        auth_url = sp.auth_manager.get_authorize_url()
        st.write(f"[Click here to authenticate with Spotify]({auth_url})")

def save_user_data(client_id, username, liked_songs, liked_playlists):
    liked_songs_json = json.dumps(liked_songs)
    liked_playlists_json = json.dumps(liked_playlists)

    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO user_info (client_id, username, liked_songs, liked_playlists) "
                "VALUES (%s, %s, %s, %s)",
                (client_id, username, liked_songs_json, liked_playlists_json)
            )

        # Commit the changes to the database
        connection.commit()

# Define the welcome page
def welcome_page():
    st.title("Welcome to Hopify")
    image_path = "Hopify.jpg"  # Replace with the actual path to your image file
    st.image(image_path, use_column_width=True)
    access_token = get_access_token()

    if access_token:
        user_data = sp.current_user()
        client_id = user_data['id']
        username = user_data['display_name']
        liked_songs = sp.current_user_saved_tracks()
        liked_playlists = sp.current_user_playlists()
        # Save user data to the database
        save_user_data(client_id, username, json.dumps(liked_songs), json.dumps(liked_playlists))
        get_new_releases('FR',5)
        show_user_profile()
        show_liked_songs(num_songs_per_page=5)
        show_user_playlists()
        get_new_releases_for_artists(top_artists_ids,'US',5)

    else:
        st.subheader("Authenticate First. Enjoy Next")
        #st.error("Authentication failed. Please check your credentials.")

# Define the main function
def main():
        # Add content for the Home page if needed

        st.sidebar.title("Navigation")
        app_page = st.sidebar.selectbox("Go to", ("Welcome", "Discover new songs","Songs you may like"))

        if app_page == "Welcome":
            welcome_page()
        elif app_page == "Discover new songs":
            access_token = get_access_token()
            if access_token:
                user_data = sp.current_user()
                user_id = user_data['id']
                show_song_recommendations(user_id)
            else:
                st.subheader("Authenticate First. Enjoy Next")
                #st.error("Authentication failed. Please check your credentials.")
        elif app_page == "Songs you may like":
            access_token = get_access_token()
            if access_token:
                user_data = sp.current_user()
                user_id = user_data['id']
                artist_recommendations(user_id)
                
            else:
                st.subheader("Authenticate First. Enjoy Next")
                #st.error("Authentication failed. Please check your credentials.")


if __name__ == "__main__":
    main()
