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
        print(PLAN_IDS)
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
    def get(self, request):
        return Response({"message": "Subscription was canceled."}, status=status.HTTP_200_OK)


class HandleStripeWebhook(APIView):
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        # Print the received payload and signature
        print(f"Received payload: {payload}")
        print(f"Received signature header: {sig_header}")

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

        print(f"Received event: {event}")

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            print(f"Session data: {session}")

            user_id = session['metadata']['user_id']
            plan_type = session['metadata']['plan_type']
            print(f"User ID: {user_id}, Plan type: {plan_type}")

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

            subscription = Subscriptions.objects.create(
                user=user,
                stripe_subscription_id=session['subscription'],
                stripe_price_id=session['line_items']['data'][0]['price']['id'],
                plan_type=plan_type,
                status='active',
                start_date=timezone.now(),
                end_date=end_date,
            )

            print(f"Subscription created: {subscription}")

            if 'invoice' in session:
                invoice = session['invoice']
                invoice_status = session['payment_status']
                print(f"Invoice data: {invoice}, Status: {invoice_status}")
                BillingHistory.objects.create(
                    user=user,
                    stripe_invoice_id=invoice['id'],
                    amount=invoice['amount_paid'] / 100,  
                    paid_at=timezone.now(),
                    status=invoice_status,
                    subscription=subscription,
                )
                print("Billing history created.")

        return Response({'status': 'success'}, status=status.HTTP_200_OK)




class CheckSubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """
        Get the subscription status of the authenticated user.
        Returns whether the user is subscribed or not.
        """
        user = request.user

        try:
            subscription = Subscriptions.objects.get(user=user)
            is_subscribed = (
                subscription.status == Subscriptions.ACTIVE and 
                subscription.end_date > timezone.now()
            )
            return Response({'isSubscribed': is_subscribed}, status=200)
        
        except Subscriptions.DoesNotExist:
            return Response({'isSubscribed': False}, status=200)
