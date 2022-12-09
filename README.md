# Auction-House-Web-App
## A web application similar to eBay where users can buy and sell products to other users by auctioning and bidding.

## Features:
- Homepage to see all active auctions by all users
- Page for logged in users to create a new auction
- Listing page that features all details about the product such as:
    1. bidding options if auction is active
    2. result of the auction if the auction is inactive (ended either manually by owner or by reaching deadline)
    3. option to end the listing early if owned by the user
    4. option to add product to the user's personal watchlist
    5. a comments section
- Personal watchlist page for the logged in user
- Categories page where user can sort auctions by category

## Full Demo Videos:
### Main Demo: https://share.getcloudapp.com/z8ulqNPd
### Auction End Demo: https://share.getcloudapp.com/jkuOJzEy

## Screenshots:
#### Main home page
![](/screenshots/home.png)

#### Listing Page (after winning)
![](/screenshots/listing.png)

## Tech Stack:
HTML, CSS, Python, Django, and SQLite

## Challenges and Lessons Learned:
- Learning and working with Django models and forms
- Making migrations and connecting django models to an SQLite database
- Understanding many to many relationships between Django models

## How to Run the Program:
- python3 manage.py makemigrations auctions
- python3 manage.py migrate
- python3 manage.py runserver
