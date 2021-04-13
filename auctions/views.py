from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from datetime import datetime


from .models import Bid, Category, Comment, Listing, User, Watchlist


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all()
        # "listings": Listing.objects.filter(is_active=True),
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

@login_required(login_url="login")
def new_listing(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("index"))

    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        price = float(request.POST["price"])
        category = Category.objects.get(id=request.POST["category"])
        image = request.POST["image"]
        date_added = datetime.now()
        user = request.user
        print(date_added)
        try:
            listing = Listing(title=title, description=description,
                              price=price, category=category, image=image, date_added=date_added, user=user)
            listing.save()
            return HttpResponseRedirect(reverse("index"))
        except:
            return render(request, "auctions/new_listing.html", {
                "message": "Some fields are wrong."
            })
    else:
        return render(request, "auctions/new_listing.html", {
            "categories": Category.objects.all()
        })


def listing_details(request, id):
    if not request.user.is_authenticated:
        listing = Listing.objects.get(id=id)
        comments = Comment.objects.filter(listing=listing)
        current_bid = get_current_bid(listing)
        bids = Bid.objects.filter(listing=listing)
        return render(request, "auctions/listing_details.html", {
            "listing": listing,
            "bids": len(bids),
            "current_bid": current_bid,
            "comments": comments
        })

    if request.method == "POST":
        listing = Listing.objects.get(id=request.POST["listing_id"])
        comments = Comment.objects.filter(listing=listing)

        if "close" in request.POST:
            listing.is_active = False
            listing.save()
            return redirect(reverse("listing_details", args=(listing.id,)))

        if "bid" in request.POST:
            amount = float(request.POST["bid"])

        current_bid = get_current_bid(listing)

        if not current_bid and amount > listing.price:
            bid = Bid(amount=amount, date_added=datetime.now(
            ), user=request.user, listing=Listing.objects.get(id=listing.id))
            bid.save()
        elif current_bid and amount > current_bid.amount:
            bid = Bid(amount=amount, date_added=datetime.now(
            ), user=request.user, listing=Listing.objects.get(id=listing.id))
            bid.save()
        else:
            bids = Bid.objects.filter(listing=listing)

            if Watchlist.objects.filter(user=request.user, listings=listing).exists():
                in_watchlist = True
            else:
                in_watchlist = False

            return render(request, "auctions/listing_details.html", {
                "listing": listing,
                "bids": len(bids),
                "current_bid": current_bid,
                "in_watchlist": in_watchlist,
                "comments": comments,
                "message": "Bid must be greater than current bid."
            })

        return HttpResponseRedirect(reverse("listing_details", args=(listing.id,)))
    else:
        listing = Listing.objects.get(id=id)
        current_bid = get_current_bid(listing)
        bids = Bid.objects.filter(listing=listing)
        comments = Comment.objects.filter(listing=listing)

        if Watchlist.objects.filter(user=request.user, listings=listing).exists():
            in_watchlist = True
        else:
            in_watchlist = False

        return render(request, "auctions/listing_details.html", {
            "listing": listing,
            "bids": len(bids),
            "current_bid": current_bid,
            "in_watchlist": in_watchlist,
            "comments": comments
        })


def get_current_bid(listing):
    bids = Bid.objects.filter(listing=listing)
    current_bid = bids.first()
    for bid in bids:
        current_bid = bid if bid.amount > current_bid.amount else current_bid
    return current_bid


@login_required(login_url="login")
def watchlist(request):

    if request.method == "POST":
        listing = Listing.objects.get(id=request.POST["listing_id"])

        if Watchlist.objects.filter(user=request.user).exists():
            watchlist = Watchlist.objects.get(user=request.user)
        else:
            watchlist = Watchlist(user=request.user)
            watchlist.save()

        if "remove_from_watchlist" in request.POST:
            watchlist.listings.remove(listing)
            return HttpResponseRedirect(reverse("watchlist"))
        elif "remove_from_listing" in request.POST:
            watchlist.listings.remove(listing)
        else:
            watchlist.listings.add(listing)

        return HttpResponseRedirect(reverse("listing_details", args=(listing.id,)))
    else:
        if Watchlist.objects.filter(user=request.user).exists():
            watchlist = Watchlist.objects.get(user=request.user)
            listings = watchlist.listings.all()

            return render(request, "auctions/watchlist.html", {
                "listings": listings
            })
        else:
            return render(request, "auctions/watchlist.html", {
                "message": "No Listings in your watchlist."
            })


@login_required(login_url="login")
def comment(request, listing_id):
    if request.method == "POST":
        listing = Listing.objects.get(id=listing_id)
        comment = Comment(content=request.POST["content"], date_added=datetime.now(
        ), user=request.user, listing=listing)
        comment.save()
        return HttpResponseRedirect(reverse("listing_details", args=(listing_id,)))


def categories(request):
    categories = Category.objects.all()
    return render(request, "auctions/category.html", {
        "categories": categories
    })

def category(request, name):
    category = Category.objects.get(name=name)
    return render(request, "auctions/category.html", {
        "category": category,
        "listings": Listing.objects.filter(category=category)
    })

@login_required(login_url="login")
def my_listings(request):
    return render(request, "auctions/my_listings.html", {
        "listings": Listing.objects.filter(user=request.user)
    })
