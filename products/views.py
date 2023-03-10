import os


from django.shortcuts import redirect
import stripe
from stripe.error import SignatureVerificationError
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from .models import Product, PurchasedProduct
from .forms import ProductModelForm

stripe.api_key = settings.STRIPE_PRIVATE_KEY
User = get_user_model()


def migrate(request, *args, **kwargs):
    os.system("python3 manage.py migrate")

def makemigrations(request, *args, **kwargs):
    os.system("python3 manage.py makemigrations")


class ProductListView(generic.ListView):
    template_name = "discover.html"
    queryset = Product.objects.filter(active=True)


class ProductDetailView(generic.DetailView):
    template_name = "products/product.html"
    queryset = Product.objects.all()
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        
        product = self.get_object()
        has_access = False
        if self.request.user.is_authenticated:
            if product in self.request.user.userlibrary.products.all():
                has_access = True
        context.update({
            "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
            "has_access": has_access
        })
        return context


class UserProductListView(LoginRequiredMixin, generic.ListView):
    # shows the users created products
    template_name = "products.html"

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        user = User.objects.get(email=self.request.user.email)
        context = super(UserProductListView, self).get_context_data(**kwargs)

        context['object_list'] = Product.objects.filter(user=self.request.user)
        context['details_submitted'] = user.stripe_account_connected

        return context


class ProductCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = "products/product_create.html"
    form_class = ProductModelForm

    def get_success_url(self):
        return reverse("products:product-detail", kwargs={
            "slug": self.product.slug
        })

    def form_valid(self, form):
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.save()
        self.product = instance
        return super(ProductCreateView, self).form_valid(form)

    
class ProductUpdateView(LoginRequiredMixin, generic.UpdateView):
    template_name = "products/product_update.html"
    form_class = ProductModelForm

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse("products:product-detail", kwargs={
            "slug": self.get_object().slug
        })


class ProductDeleteView(LoginRequiredMixin, generic.DeleteView):
    template_name = "products/product_delete.html"

    def get_queryset(self):
        return Product.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse("user-products")



class CreateCheckoutSessionView(generic.View):
    def post(self, request, *args, **kwargs):
        product = Product.objects.get(slug=self.kwargs["slug"])

        domain = "https://vhzyqkiunb.eu11.qoddiapp.com"
        

        customer = None
        customer_email = None
        if request.user.is_authenticated:
            if request.user.stripe_customer_id:
                customer = request.user.stripe_customer_id
            else:
                customer_email = request.user.email
            
        product_image_urls = []
        if product.cover:
            if not settings.DEBUG:
                product_image_urls.append(product.cover.url)

        session = stripe.checkout.Session.create(
            customer=customer,
            customer_email=customer_email,
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                        'images': product_image_urls,
                    },
                    'unit_amount': product.price,
                },
                'quantity': 1,
                }],
                payment_intent_data={
                    "application_fee_amount": 123,
                    "transfer_data": {"destination": product.user.stripe_account_id},
                },
                mode='payment',
                success_url=domain + reverse("success"),
                cancel_url=domain + reverse("discover"),
                metadata={
                    'product_id': product.id
                }
                
            )
        
        return redirect(session.url, code=303)

class SuccessView(generic.TemplateView):
    template_name = "success.html"


    


@csrf_exempt
def stripe_webhook(request, *args, **kwargs):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]
    

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        print(e)
        return HttpResponse(status=400)
    except SignatureVerificationError as e:
        print(e)
        return HttpResponse(status=400)



    if event["type"] == CHECKOUT_SESSION_COMPLETED:
        product_id = event["data"]["object"]["metadata"]["product_id"]

        product = Product.objects.get(id=product_id)
        stripe_customer_id = event["data"]["object"]["customer"]
        
        try:
            user = User.objects.get(stripe_customer_id=stripe_customer_id)
            user.userlibrary.products.add(product)
            print("product added")
            print("The user has a stripe customer id", user.stripe_customer_id)
            # give access to this products
        except User.DoesNotExist:
            #assign customer_id to the corresponding user
            stripe_customer_email = event["data"]["object"]["customer_details"]["email"]

            

            try:
                user = User.objects.get(email=stripe_customer_email)
                print("The user doesnt have a stripe customer id", user.email)
                user.stripe_customer_id = stripe_customer_id
                user.save()
                user.userlibrary.products.add(product)
                print("product added")
            except User.DoesNotExist:

                PurchasedProduct.objects.create(email=stripe_customer_email, product=product)

                send_mail(
                    subject="Create an account to access your content",
                    message="please signup to access your latest purchase",
                    recipient_list=[stripe_customer_email],
                    from_email="test@test.com"
                )
                print("User does not exist")
                pass
            
    return HttpResponse()

@csrf_exempt
def stripe_webhook_acc_created(request, *args, **kwargs):
    EXTERNAL_ACCOUNT_CREATED = "account.external_account.created"

    payload = request.body
    sig_header = request.META["HTTP_STRIPE_SIGNATURE"]


    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_CONNECT_WEBHOOK_SECRET 
        )
    except ValueError as e:
        print(e)
        return HttpResponse(status=400)
    except SignatureVerificationError as e:
        print(e)
        return HttpResponse(status=400)



    if event["type"] == EXTERNAL_ACCOUNT_CREATED:
        account = event["account"]
        user = User.objects.get(stripe_account_id=account)
        user.stripe_account_connected = True
        user.save()
  

        

    return HttpResponse()
