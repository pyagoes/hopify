# Hopify Music Recommendation System

Hopify Web App is a personalized music companion that utilizes the power of machine learning and collaborative filtering techniques, including the cutting-edge NMF (Non-Negative Matrix Factorization) model, to recommend songs tailored just for the users. The user can explore and discover new tracks based on their unique music preferences and past interactions with songs, making their music exploration experience delightful and engaging. Hopify analyzes the user's listening history and taste to provide accurate and exciting song suggestions that resonate with users' interests.

## Table of Contents

- **data:**
  - **data.csv:** This dataset has columns named UserID, SongID, and NoOfTimesPlayed. It gives information about the users' song interests.
  - **df_ncf.csv:** This dataset contains the same information as in data.csv but with the addition of a new column named "Ratings." The "Ratings" are given based on how much the user is interested in listening to a song. This dataset is used for training the model.
  - **unique_tracks.txt:** This dataset has columns TrackID, SongID, SongName, and ArtistName. This dataset is used to fetch the SongName and ArtistName based on the recommendations made by the SongID.

- **model:**
  - **surprise_model.pkl:** This is a saved model for recommending songs to the user. The model is trained on Non-Negative Matrix Factorization from the surprise library.
