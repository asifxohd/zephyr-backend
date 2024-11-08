import stripe
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Subscriptions, BillingHistory
from user_authentication.models import CustomUser
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from decouple import config
from django.db import transaction
from .serializers import SubscriptionSerializer
from rest_framework import generics


base_url = config('BASE_FRONTEND_URL', default='http://localhost:5173') 
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

PLAN_IDS = {
    'free_trial': settings.STRIPE_PLAN_FREE_TRIAL,
    'monthly': settings.STRIPE_PLAN_MONTHLY,  
    'semi_annual': settings.STRIPE_PLAN_SEMI_ANNUAL,
    'annual': settings.STRIPE_PLAN_ANNUAL, 
}

class CreateCheckoutSession(APIView):
    def post(self, request, plan_type):
        if plan_type not in PLAN_IDS:
            return Response({'error': 'Invalid plan type'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        price_id = PLAN_IDS[plan_type]
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{base_url}business/subscriptions/success',
                cancel_url=f'{base_url}business/subscriptions/cancel',
                customer_email=user.email,
                metadata={'user_id': user.id, 'plan_type': plan_type},
            )
            return Response({'checkout_url': checkout_session.url}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SubscriptionSuccess(APIView):
    def get(self, request):
        return Response({"message": "Subscription was successful!"}, status=status.HTTP_200_OK)


class SubscriptionCancel(APIView):
    permission_classes=[IsAuthenticated]
    def post(self, request):
        user = request.user
        try:
            subscription = Subscriptions.objects.get(user=user)
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            subscription.status = Subscriptions.CANCELED
            subscription.save()
            return Response({"message": "Subscription has been canceled."}, status=status.HTTP_200_OK)
        
        except Subscriptions.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    

class HandleStripeWebhook(APIView):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            print(f"Invalid payload error: {e}")
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            print(f"Invalid signature error: {e}")
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            user_id = session['metadata']['user_id']
            plan_type = session['metadata']['plan_type']
            
            with transaction.atomic():
                try:
                    user = CustomUser.objects.get(id=user_id)
                except CustomUser.DoesNotExist:
                    print(f"User with ID {user_id} not found.")
                    raise NotFound(detail="User not found", code=status.HTTP_404_NOT_FOUND)

                print(f"Found user: {user}")

                if plan_type == 'free_trial':
                    end_date = timezone.now() + timezone.timedelta(days=7)  # 7 days free trial
                elif plan_type == 'monthly':
                    end_date = timezone.now() + timezone.timedelta(days=30)  # 1 month
                elif plan_type == 'semi_annual':
                    end_date = timezone.now() + timezone.timedelta(days=180)  # 6 months
                elif plan_type == 'annual':
                    end_date = timezone.now() + timezone.timedelta(days=365)  # 1 year
                else:
                    print(f"Invalid plan type: {plan_type}")
                    return Response({'error': 'Invalid plan type'}, status=status.HTTP_400_BAD_REQUEST)
                
                if plan_type != 'free_trial':
                    existing_subscription = Subscriptions.objects.filter(user=user).first()
                    if existing_subscription:
                        existing_subscription.delete()
                    
                    subscription = Subscriptions.objects.create(
                        user=user,
                        stripe_subscription_id=session['subscription'],
                        plan_type=plan_type,
                        status='active',
                        start_date=timezone.now(),
                        end_date=end_date,
                    )
                else:
                    subscription = Subscriptions.objects.create(
                        user=user,
                        stripe_subscription_id=session['subscription'],
                        plan_type=plan_type,
                        status='active',
                        has_used_free_trial=True,
                        start_date=timezone.now(),
                        end_date=end_date,
                    )

                print(f"Subscription created: {subscription}")

                if 'invoice' in session:
                    invoice = session['invoice']
                    invoice_status = session['payment_status']
                    amount = int(session['amount_total']) / 100

                    BillingHistory.objects.create(
                        user=user,
                        stripe_invoice_id=invoice,
                        amount=amount,
                        paid_at=timezone.now(),
                        status=invoice_status,
                        subscription=subscription,
                    )
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)



class CheckSubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get the subscription status of the authenticated user.
        Returns whether the user is subscribed or not and
        whether the user has used their free trial.
        """
        user = request.user

        try:
            subscription = Subscriptions.objects.get(user=user)
            is_subscribed = subscription.end_date > timezone.now()
            has_used_free_trial = subscription.has_used_free_trial

            return Response({
                'isSubscribed': is_subscribed,
                'freeTrialUsed': has_used_free_trial
            }, status=200)
        
        except Subscriptions.DoesNotExist:
            return Response({
                'isSubscribed': False,
                'freeTrialUsed': False  
            }, status=200)


class SubscriptionDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            subscription = Subscriptions.objects.get(user=request.user)
        except Subscriptions.DoesNotExist:
            return Response({'detail': 'Subscription not found for this user.'}, status=404)
        
        serializer = SubscriptionSerializer(subscription)

        return Response(serializer.data)