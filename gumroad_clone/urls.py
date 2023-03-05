"""gumroad_clone URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]


from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from products.views import (
    ProductListView, 
    UserProductListView,
    ProductCreateView,
    CreateCheckoutSessionView,
    SuccessView,
    stripe_webhook
    )
from users.views import UserProfileView, StripeAccountLinkView
urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("discover/", ProductListView.as_view(), name='discover'),
    path('products/', UserProductListView.as_view(), name='user-products'),
    path('products/create/', ProductCreateView.as_view(), name='product-create'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('stripe/auth/', StripeAccountLinkView.as_view(), name='stripe-account-link'),

    path("p/", include('products.urls', namespace='products')),
    path("create-checkout-session/<slug>/", CreateCheckoutSessionView.as_view(), name="create-checkout-session"),
    path('success/', SuccessView.as_view(), name='success'),
    path("webhooks/stripe/", stripe_webhook, name='stripe-webhook'),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
