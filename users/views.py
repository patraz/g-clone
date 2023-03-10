from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, RedirectView, UpdateView, TemplateView
import stripe
User = get_user_model()
stripe.api_key = settings.STRIPE_PRIVATE_KEY


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profile.html"
    def get_context_data(self, *args, **kwargs):
            context = super(UserProfileView, self).get_context_data(*args, **kwargs)
            user = User.objects.get(email=self.request.user.email)
            
            context['details_submitted'] = user.stripe_account_connected
            return context


class UserDetailView(LoginRequiredMixin, DetailView):

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})

    def get_object(self):
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()


class StripeAccountLinkView(LoginRequiredMixin, RedirectView):

    permanent = False

    def get_redirect_url(self):
        domain = "https://vhzyqkiunb.eu11.qoddiapp.com"
        if settings.DEBUG:
            domain = "https://d44a-109-173-214-110.eu.ngrok.io"
        account_links = stripe.AccountLink.create(
            account=self.request.user.stripe_account_id,
            refresh_url=domain + reverse("stripe-account-link"),
            return_url=domain + reverse("profile"),
            type='account_onboarding',
        )
        return account_links["url"]