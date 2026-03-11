import requests

API_KEY = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI2YWM4NzA4ZDJhYmRjYjAzYjI4N2ZlNzdjZGRhMTVmYyIsIm5iZiI6MTcxNTAwNjYxOC43NTUsInN1YiI6IjY2MzhlYzlhNWVkOGU5MDEyOTE1NmQ0NCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.A4MLLAZQ_jJfwZ4NvAWqz27izVaTmyuo00zVSzrHbew"

url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}"

response = requests.get(url)

movies = response.json()["results"]

print(movies[0])