from django.contrib import admin
from .models import (
    Profile,
    Species,
    SpeciesCare,
    Vendor,
    NuptialFlight,
    ForumSection,
    ForumThread,
    ForumPost,
    SpeciesBookmark,
    SpeciesSuggestion,
)

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ("genus", "species", "common_name", "difficulty", "region", "diapause")
    prepopulated_fields = {"slug": ("genus", "species")}

@admin.register(SpeciesCare)
class SpeciesCareAdmin(admin.ModelAdmin):
    list_display = ("species", "temperature_min_c", "temperature_max_c", "humidity_min", "humidity_max")

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "region", "is_trusted")
    list_filter = ("category", "is_trusted")

@admin.register(NuptialFlight)
class NuptialFlightAdmin(admin.ModelAdmin):
    list_display = ("species", "date", "location_name", "region")
    list_filter = ("species", "region", "date")

@admin.register(ForumSection)
class ForumSectionAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ("title", "section", "author", "created_at", "is_locked")
    list_filter = ("section", "is_locked")

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ("thread", "author", "created_at")

@admin.register(SpeciesBookmark)
class SpeciesBookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "species", "created_at")

@admin.register(SpeciesSuggestion)
class SpeciesSuggestionAdmin(admin.ModelAdmin):
    list_display = ("proposed_genus", "proposed_species", "status", "created_at")
    list_filter = ("status",)

admin.site.register(Profile)
