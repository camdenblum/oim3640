
import requests

#response = requests.get("https://oim.108122.xyz/words/random")

#print(response.json()) ## gives a random word from the API

response = requests.get("https://oim.108122.xyz/mass",
                        headers={"X-Token": "camdencamden"})

data = response.json()

print(data['name'])
print(data['governor'])

#for town in data['data'[:5]]:
 #   print(f"{town['name']}: pop {town['population']:,}")

# Find the smallest town by population
smallest = min(data['data'], key=lambda t: t['population'])
print(f"Smallest town: {smallest['name']} with population {smallest['population']:,}")

## find top for 5 towns by population 
#top_5 = sorted(data['data'], key=lambda t: t['population'], reverse=True)[:5]
#print("Top 5 largest towns:")
#for town in top_5:
 #   print(f"{town['name']}: pop {town['population']:,}")


## find population data about Charlton and size of the area square miles of the town
charlton = next((t for t in data['data'] if t['name'] == 'Charlton'), None)
if charlton:
    print(f"Charlton population: {charlton['population']:,}")
    print(f"Charlton area: {charlton['area_sq_mi']:,}")
    print(f"Charlton founded: {charlton['founded']:,}")
    print(f"Charlton county: {charlton['county']:,}")


else:
    print("Charlton not found in data.")


