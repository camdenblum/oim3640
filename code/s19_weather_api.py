
import requests
from pprint import pprint
from dotenv import load_dotenv
import os


load_dotenv()
API_KEY = os.getenv('OPENWEATHER_API_KEY')

#city = input("Enter a city name to get the current weather: ")
#url = (f'https://api.openweathermap.org/data/2.5/weather?q=city&appid={API_KEY}&units=imperial')

#print(url)

#data = requests.get(url).json()
#print(f"city: {data['main']['temp']}°F")

##Can you modify the code to get weather for any city? (Hint: use input() to get the city name from the user and include it in the API request URL)
url = (f'https://api.openweathermap.org/data/2.5/weather?q={location}&appid={API_KEY}&units=imperial')

print(url)

data = requests.get(url).json()
print(f"city: {data['main']['temp']}°F")
