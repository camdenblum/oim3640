import requests

# GET: read all messages
data = requests.get('https://oim.108122.xyz/messages').json()
for msg in data:
    print(msg)

# POST: send a message (1-140 characters)
requests.post('https://oim.108122.xyz/message',
              json={'message': 'Hello from Cam!'},
              headers={'X-Token': 'camdencamden'})

url = 'http://api.open-notify.org/astros.json'
data = requests.get(url).json()
print(f"{data['number']} people in space right now!")
for p in data['people']:
    print(f"  {p['name']} on {p['craft']}")
