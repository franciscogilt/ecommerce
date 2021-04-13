from .models import Watchlist


def watchlist_count(request):
    if request.user.is_authenticated:
        return {
            "watchlist_count": Watchlist.objects.get(user=request.user).listings.all().count()
        }
    else:
        return {
            "watchlist_count": 0
        }
