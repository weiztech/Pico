from .models import Subscription

def subscription_type(request):
    if request.user.is_authenticated:
        subscription = Subscription.objects.filter(user=request.user).first()
        if subscription:
            return {'subscription': subscription}
        
    return {'subscription': None}