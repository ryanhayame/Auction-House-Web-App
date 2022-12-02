from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator
from datetime import timedelta
from django.utils import timezone

# Remember that each time you change anything in auctions/models.py, 
# you’ll need to first run python manage.py makemigrations and then 
# python manage.py migrate to migrate those changes to your database.
class User(AbstractUser):
    pass

class Listing(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="ownerListings")
    title = models.CharField(max_length=50)
    desc = models.TextField(max_length=500)
    bid = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0.00)])
    isActive = models.BooleanField(default=True)
    image = models.ImageField(blank=True, null=True, upload_to='')

    DURATIONS = [
        (0, 'Select One'),
        (6, '6 Hours'),
        (12 , '12 Hours'),
        (24 , '1 Day'),
        (48 , '2 Days'),
        (72, '3 Days'),
        (120, '5 Days'), 
        (168, '1 Week'),
        (336, '2 Weeks')
    ]
    duration = models.IntegerField(choices=DURATIONS, default=0, validators=[MinValueValidator(1)])

    CATEGORIES = [
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
    ]
    category = models.IntegerField(choices=CATEGORIES, default=0, validators=[MinValueValidator(1)])
    timestamp = models.DateTimeField(default=timezone.now())
    watchers = models.ManyToManyField(User, blank=True, related_name="watchlist")
    deadline = models.DateTimeField(blank=True, null=True)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="userWins")

    def save(self, *args, **kwargs):
        self.bid = round(self.bid, 2)
        if not self.deadline:
            self.deadline = self.timestamp + timedelta(hours=self.duration)
        super(Listing, self).save(*args, **kwargs)

    def datepublished(self):
        return self.timestamp.strftime('%B %d %Y')

class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="placedBids")
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="placedBids")
    amount = models.DecimalField(max_digits=6, decimal_places=2)

class Comment(models.Model):
    message = models.TextField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    poster = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="comments")