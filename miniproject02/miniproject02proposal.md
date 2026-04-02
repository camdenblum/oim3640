

## What I'm Building
A Flask web app that lets users enter any Boston-area location and instantly find 
the nearest upcoming professional sports game (MLB, NBA, NHL, or NFL), complete 
with game details, venue location, and directions — all in one place.



## Why I Chose This
I chose this project because I'm genuinely interested in Boston sports and wanted 
to build something I'd actually use. As someone who follows local teams and 
occasionally attends games, I've experienced the frustration of checking multiple 
team websites and schedules just to figure out which game is happening soonest and 
closest to where I am. That process is slow and scattered. This app solves that 
real problem by combining location search, live schedule data, and mapping into a 
single, simple interface — so a user can go from "I want to catch a game tonight" 
to knowing exactly which one and how to get there in seconds.



## Core Features
The app will allow users to enter any place name or address, such as "Babson College" 
or "Boston Common," which gets geocoded into coordinates using the Mapbox API. From 
there, the app queries upcoming game schedules for Boston's four major professional 
teams — the Red Sox, Celtics, Bruins, and Patriots — and identifies which home game 
is happening soonest relative to the user's location. The results page will display 
the team, opponent, sport type, venue name, game date and time, and distance from 
the user's entered location. An interactive Mapbox map will also render directly in 
the browser, showing both the user's location and the game venue marked with pins. 
The entire experience will be wrapped in a clean, styled Flask-powered interface with 
proper error handling for cases like invalid locations or no upcoming home games.



## What I Don't Know Yet
Honestly, there is a lot I still need to figure out, and most of it is new territory 
for me. The biggest unknown is finding and learning a reliable sports schedule API — 
such as SportsDB or a similar free source — that covers multiple leagues and 
understanding how its JSON responses are structured well enough to extract the data 
I need. Beyond just retrieving that data, I'll also need to figure out how to sort 
and compare games across different teams by both date and distance at the same time, 
which is more complex logic than I've written before. On the Flask side, I understand 
the basics from class but still need to get comfortable with POST requests, passing 
data between routes, and rendering dynamic results cleanly in HTML templates. Since 
this project chains Mapbox geocoding, a sports API, and Mapbox map rendering all 
together, I'll also need to learn how to connect these pieces without things breaking 
in between. Embedding an interactive Mapbox map in a webpage using Mapbox GL JS is 
something I've never done and will need to explore carefully. I'll also need to learn 
how to calculate real-world distance between two lat/lng coordinate pairs in Python, 
likely using the haversine formula or a helper library. Finally, handling real-world 
edge cases like missing data, API rate limits, away games, and offseason schedules 
is something I haven't had to manage before and will need to think through carefully 
as I build.


## AI Note: 

Prompt: take this mini project assignemnet description, and make my proposal 100% perfect and in depth following the critria 100% and keeping my orgional idea, keep the sections the same and clearly organize your response so i can use it in my assignemnt, I also uploaded the assigment criteria and my first iteration of my proposal