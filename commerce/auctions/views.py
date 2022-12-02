from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import decimal
from django.utils import timezone

from .models import User, Listing, Bid, Comment

class CreateForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'desc', 'bid', 'duration', 'category', 'image']
        DURATIONS = (
            (0, 'Select One'),
            (6, '6 Hours'),
            (12 , '12 Hours'),
            (24 , '1 Day'),
            (48 , '2 Days'),
            (72, '3 Days'),
            (120, '5 Days'), 
            (168, '1 Week'),
            (336, '2 Weeks')
        )
        CATEGORIES = (
            (0, 'Select One'),
            (1, 'Antiques'),
            (2, 'Books'),
            (3, 'Business & Industrial'),
            (4, 'Clothing, Shoes & Accessories'),
            (5, 'Collectibles'),
            (6, 'Crafts'),
            (7, 'Dolls & Plushies'),
            (8, 'Electronics'),
            (9, 'Home & Garden'),
            (10, 'Motors'),
            (11, 'Pet Supplies'),
            (12, 'Sporting Goods'),
            (13, 'Toys & Hobbies'),
        )
        labels = {
            "desc": "Description",
            "bid": "Starting Price"
        }
        widgets = {
            'title' : forms.TextInput(attrs={"class": "form-control", "style": "margin-bottom: 10px;", "max_length": 64}),
            'desc' : forms.Textarea(attrs={"class": "form-control", "style": "margin-bottom: 10px;", "max_length": 500}),
            'bid' : forms.NumberInput(attrs={"class": "form-control", "style": "margin-bottom: 10px;", "max_digits": 6, "decimal_places": 2}),
            'duration' : forms.Select(choices=DURATIONS, attrs={"class": "form-control", "style": "margin-bottom: 10px;"}),
            'category' : forms.Select(choices=CATEGORIES, attrs={"class": "form-control", "style": "margin-bottom: 10px;"}),
            'image' : forms.FileInput(attrs={"style": "margin-bottom: 30px; margin-right: 100%;"})
        }

def index(request):
    # used to only show active listings
    now = timezone.now()
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all(),
        "now": now
    })

@login_required(login_url='login')
def listing(request, listing_id):
    listingObj = Listing.objects.get(id=listing_id)
    now = timezone.now()
    # if deadline is reached
    if now > listingObj.deadline:
        listingObj.isActive = False
        # get winning bid
        bids = Bid.objects.filter(listing=listingObj)
        winningBid = bids.order_by('-id')[0]
        listingObj.winner = winningBid.bidder
        listingObj.save()

    # placing bid
    if request.method == "POST":
        if listingObj.isActive:
            newBid = request.POST["newBid"]
            listingObj.bid = decimal.Decimal(newBid)
            listingObj.save()
            bid = Bid(listing=listingObj, bidder=request.user, amount=listingObj.bid)
            bid.save()
            return render(request, "auctions/listing.html", {
                "listing": listingObj,
                "minimum": round(float(listingObj.bid) + 0.01, 2),
                "message": None,
                "success": "Bid succesfully placed",
                "owned": False
            })
        else:
            # if trying to place a bid after deadline 
            # (ex. leaving page loaded after deadline then submitting)
            return render(request, "auctions/listing.html", {
                "listing": listingObj,
                "minimum": round(float(listingObj.bid) + 0.01, 2),
                "message": "Bid failed: bidding time ended",
                "success": None,
                "owned": False
            })
    # if auction is closed
    else:
        # if user is the owner of the item
        if listingObj.owner == request.user:
            return render(request, "auctions/listing.html", {
                "listing": listingObj,
                "minimum": round(float(listingObj.bid) + 0.01, 2),
                "message": None,
                "success": None,
                "owned": True
            })
        # if user is not the owner of the item
        else:
            return render(request, "auctions/listing.html", {
                "listing": listingObj,
                "minimum": round(float(listingObj.bid) + 0.01, 2),
                "message": None,
                "success": None,
                "owned": False
            })

@login_required
def comment(request):
    # request method can onny be post for this
    messagetxt = request.POST.get('message')
    listing_id = request.POST.get('id')
    listingObj = Listing.objects.get(id=listing_id)
    comment = Comment(message=messagetxt, poster=request.user, listing=listingObj)
    comment.save()
    return redirect(f"/listing/{listing_id}")

@login_required(login_url='login')
def close(request):
    # request method can only be post for this
    # updates listing object data
    listing_id = request.POST.get('id')
    listingObj = Listing.objects.get(id=listing_id)
    listingObj.deadline = timezone.now()
    listingObj.isActive = False

    # get winning bid
    bids = Bid.objects.filter(listing=listingObj)
    winningBid = bids.order_by('-id')[0]
    listingObj.winner = winningBid.bidder
    listingObj.save()

    return redirect(f"/listing/{listing_id}")


@login_required(login_url='login')
def create(request):
    if request.method == "POST":
        form = CreateForm(request.POST, request.FILES)
        if form.is_valid():
            newListing = form.save()
            newListing.owner = request.user
            newListing.save()
            # creates a starting bid from the owner (used for when item doesnt sell)
            formattedBid = round(float(newListing.bid), 2)
            bid = Bid(listing=newListing, bidder=request.user, amount=formattedBid)
            bid.save()
            # adds created listing to your watchlist
            userObj = User.objects.get(id=request.user.id)
            newListing.watchers.add(userObj)
            return redirect(f"/listing/{newListing.id}")
        else:
            # ERRORS AFTER FORM SUBMISSION
            # if negative bid is placed
            if int(form.data["bid"]) < 0:
                return render(request, "auctions/create.html", {
                    "form": CreateForm(),
                    "message": "ERROR: Starting bid cannot be negative"
                })
            # if no duration is selected
            elif form.data.get("duration") == '0':
                return render(request, "auctions/create.html", {
                    "form": CreateForm(),
                    "message": "ERROR: Please select a duration"
                })
            # if no category is selected 
            else:
                return render(request, "auctions/create.html", {
                    "form": CreateForm(),
                    "message": "ERROR: Please select a category"
                })

    return render(request, "auctions/create.html", {
        "form": CreateForm(),
        "message": None
    })

CATEGORIES = {
    'Antiques' : 1,
    'Books' : 2,
    'Business & Industrial' : 3,
    'Clothing, Shoes & Accessories' : 4,
    'Collectibles' : 5,
    'Crafts' : 6,
    'Dolls & Plushies' : 7,
    'Electronics' : 8,
    'Home & Garden' : 9,
    'Motors' : 10,
    'Pet Supplies' : 11,
    'Sporting Goods' : 12,
    'Toys & Hobbies' : 13
}

def categories(request):
    return render(request, "auctions/categories.html", {
        "categories": CATEGORIES.keys()
    })

def category(request, category_name):
    now = timezone.now()
    # gets all listings with that category_name (checks if active later)
    listings = Listing.objects.filter(category=CATEGORIES[category_name])
    # orders listing by deadline (closest deadline appears first)
    ordered = listings.order_by('deadline')
    return render(request, "auctions/category.html", {
        "category": category_name,
        "results": ordered,
        "now": now
    })

@login_required(login_url='login')
def watchlist(request):
    if request.method == "POST":
        listing_id = request.POST.get('add', None)
        # if adding to watchlist
        if listing_id:
            listingObj = Listing.objects.get(id=listing_id)
            userObj = User.objects.get(id=request.user.id)
            listingObj.watchers.add(userObj)
        # if removing from watchlist
        else:
            listing_id = request.POST.get('remove')
            listingObj = Listing.objects.get(id=listing_id)
            userObj = User.objects.get(id=request.user.id)
            listingObj.watchers.remove(userObj)
        return redirect(f"/listing/{listing_id}")
    # gets listing ids of user's watchlist from sql database of many to many variables
    listing_ids_set = request.user.watchlist.through.objects.all().filter(user_id=request.user.id).values_list('listing_id', flat=True)
    # converts listing ids to listing model objects
    listings = []
    for listing_id in listing_ids_set:
        listingObj = Listing.objects.get(id=listing_id)
        listings.append(listingObj)
    return render(request, "auctions/watchlist.html", {
        "listings" : listings
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
