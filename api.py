from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from surprise import Dataset, Reader
from surprise.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances
from surprise.dump import load

# Load data for song recommendations
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

# Case-insensitive search
final_data['name'] = final_data['name'].str.upper()

# Pydantic model for song recommendation request
class SongRecommendationRequest(BaseModel):
    song_name: str

# Pydantic model for song recommendation response
class SongRecommendationResponse(BaseModel):
    song_id: str  # Add song_id field to the response model
    song_name_year: str
    similarity_percentage: float

# Function for song recommendations
def recommended_song_euclidean(song_name, n):
    # 1. getting the vector of the song entered by the user
    target_song = final_data.query('name == @song_name')
    if target_song.shape[0] == 0:
        raise HTTPException(status_code=404, detail='That song is not in the dataset.')

    feature_vector = target_song[features].values[0]

    # Ensure all relevant columns are converted to numerical data types
    feature_vector = feature_vector.astype(float)

    # 2. calculate euclidean distances between the target song and the rest
    distances = euclidean_distances(final_data[features].values.astype(float), [feature_vector]).flatten()

    # 3. index of the similar songs
    similar_song_indices = distances.argsort()[1:n + 1]  # Exclude the first element which is the target song itself

    # % of similarity
    max_distance = np.max(distances)
    similarity_percentages = (max_distance - distances[similar_song_indices]) / max_distance * 100

    # 4. list of recommendations with similarity percentages and song IDs
    recommendations_list = []
    for i in range(len(similar_song_indices)):
        song_id = final_data.iloc[similar_song_indices[i]]['id']
        song_name_year = "{} ({})".format(final_data.iloc[similar_song_indices[i]]['name'], final_data.iloc[similar_song_indices[i]]['year'])
        similarity_percentage = similarity_percentages[i]
        recommendations_list.append({
            "song_id": song_id,
            "song_name_year": song_name_year,
            "similarity_percentage": similarity_percentage
        })

    return recommendations_list

# -------------------------------------------------- #

data1 = pd.read_csv('data/df_ncf.csv')
# Create a Surprise Reader object to parse the data
reader = Reader(rating_scale=(1, 5))
# Load the data into Surprise Dataset
dataset = Dataset.load_from_df(data1[['UserID', 'SongID', 'Ratings']], reader)

trainset, testset = train_test_split(dataset, test_size=0.2, random_state=42)

unique_tracks_data = pd.read_csv('data/unique_tracks.txt', sep='<SEP>', header=None, names=['artist_id', 'song_id', 'song_name', 'artist_name'])

#user_id = 'f1b86755fc50d39da8b1cec604f2f25ec822282e'

# Get the list of all unique song IDs
unique_songs = data1['SongID'].unique()

model_filename = "model/surprise_model.pkl"  # Replace with the actual path to the saved model
_,model = load(model_filename)

class UserIdRequest(BaseModel):
    user_id: str
    
class ArtistRecommendationResponse(BaseModel):
    song_id: str
    artist_name: str
    song_name: str
    predicted_rating: float
    
def nmf_recommendations(user_id,n):
    
    user_predictions = [(song_id, model.predict(user_id, song_id).est) for song_id in unique_songs]
    user_predictions.sort(key=lambda x: x[1], reverse=True)
    top_n_recommendations = user_predictions[:n]
    
    recommendations_artist_list = []
    
    for i, (song_id, rating) in enumerate(top_n_recommendations, 1):
        song_data = unique_tracks_data[unique_tracks_data['song_id'] == song_id]
        if not song_data.empty:
            song_name = song_data.iloc[0]['song_name']
            artist_name = song_data.iloc[0]['artist_name']
            recommendations_artist_list.append({
                "song_id": song_id,
                "song_name": song_name,
                "artist_name": artist_name,
                "predicted_rating": rating
            })
            
    return recommendations_artist_list
            
app = FastAPI()

@app.post("/recommend-song/", response_model=list[SongRecommendationResponse])
def recommend_song(request: SongRecommendationRequest):
    try:
        song_name = request.song_name.upper()
        # Call the recommendation function and get the recommendations
        recommendations = recommended_song_euclidean(song_name, 5)
        response_data = []
        for recommendation in recommendations:
            song_id = recommendation["song_id"]
            song_name_year = recommendation["song_name_year"]
            similarity_percentage = recommendation["similarity_percentage"]
            response_data.append({
                "song_id": song_id,
                "song_name_year": song_name_year,
                "similarity_percentage": similarity_percentage
            })
        return response_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/recommend-artist/", response_model=list[ArtistRecommendationResponse])
def recommend_songs_for_user(user_request: UserIdRequest):
    try:
        # Get the user ID from the request
        user_id = user_request.user_id
        #print("fjeanfkfaefieafaeiuf",user_id)
        recommended_artist = nmf_recommendations(user_id,10)
        return recommended_artist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


