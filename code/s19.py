import requests

# GET: read all messages
data = requests.get('https://oim.108122.xyz/messages').json()
for msg in data:
    print(msg)

# POST: send a message (1-140 characters)
requests.post('https://oim.108122.xyz/message',
              json={'message': 'Hello from Cam!'},
              headers={'X-Token': 'camdencamden'})