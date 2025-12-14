from django.urls import path
from . import views

app_name = "guide"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),

    path("species/", views.species_list, name="species_list"),
    path("species/compare/", views.species_compare, name="species_compare"),
    path("species/compare/clear/", views.clear_compare, name="clear_compare"),
    path("species/<slug:slug>/", views.species_detail, name="species_detail"),
    path("species/<int:pk>/bookmark/", views.toggle_bookmark, name="toggle_bookmark"),
    path("species/<int:pk>/add-to-compare/", views.add_to_compare, name="add_to_compare"),
    path("species/<slug:slug>/care-card/", views.care_card_pdf, name="care_card"),

    path("flights/", views.flights_list, name="flights"),
    path("flights/new/", views.flights_add, name="flights_add"),
    path("api/flights/", views.api_flights, name="api_flights"),

    path("vendors/", views.vendors_list, name="vendors"),

    path("forum/", views.forum_index, name="forum_index"),
    path("forum/section/<slug:slug>/", views.forum_section_detail, name="forum_section"),
    path("forum/section/<slug:slug>/new-thread/", views.forum_thread_create, name="forum_thread_create"),
    path("forum/thread/<int:pk>/", views.forum_thread_detail, name="forum_thread"),

    path("account/profile/", views.profile_view, name="profile"),
    path("account/register/", views.register, name="register"),

    path("suggestions/", views.suggestion_list, name="suggestion_list"),
    path("suggestions/<int:pk>/", views.suggestion_review, name="suggestion_review"),
    path("species/<slug:species_slug>/suggest/", views.suggestion_create, name="suggestion_for_species"),
    path("suggest/", views.suggestion_create, name="suggestion_create"),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
