from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.db import transaction

from django.conf import settings
import requests
from urllib.parse import quote

from .models import (
    Species,
    SpeciesCare,
    Vendor,
    NuptialFlight,
    ForumSection,
    ForumThread,
    ForumPost,
    SpeciesBookmark,
    SpeciesSuggestion,
    Profile,
)
from .forms import (
    RegistrationForm,
    SpeciesFilterForm,
    NuptialFlightForm,
    ForumThreadForm,
    ForumPostForm,
    SpeciesSuggestionForm,
    ProfileForm,
)

def ensure_demo_content():
    # Create a bit of starter data when the database is empty. 
    if Species.objects.exists():
        return

    with transaction.atomic():
        # Demo user for sample forum threads.
        demo_user, created = User.objects.get_or_create(
            username="demo_keeper",
            defaults={"email": "demo@example.com"},
        )
        if created or not demo_user.has_usable_password():
            demo_user.set_unusable_password()
            demo_user.save()

        # Core starter species that show up on the homepage and flight map.
        lasius_niger = Species.objects.create(
            slug="lasius-niger",
            genus="Lasius",
            species="niger",
            common_name="Black garden ant",
            difficulty="easy",
            region="temperate",
            founding_mode="claustral",
            diapause="required",
        )
        formica_fusca = Species.objects.create(
            slug="formica-fusca",
            genus="Formica",
            species="fusca",
            common_name="Silky field ant",
            difficulty="medium",
            region="temperate",
            founding_mode="claustral",
            diapause="required",
        )
        camponotus_pennsylvanicus = Species.objects.create(
            slug="camponotus-pennsylvanicus",
            genus="Camponotus",
            species="pennsylvanicus",
            common_name="Black carpenter ant",
            difficulty="medium",
            region="temperate",
            founding_mode="claustral",
            diapause="required",
        )
        solenopsis_invicta = Species.objects.create(
            slug="solenopsis-invicta",
            genus="Solenopsis",
            species="invicta",
            common_name="Red imported fire ant",
            difficulty="hard",
            region="tropical",
            founding_mode="claustral",
            diapause="none",
        )
        messor_barbarus = Species.objects.create(
            slug="messor-barbarus",
            genus="Messor",
            species="barbarus",
            common_name="Barbarian harvester ant",
            difficulty="medium",
            region="mediterranean",
            founding_mode="claustral",
            diapause="light",
        )
        tetramorium_immigrans = Species.objects.create(
            slug="tetramorium-immigrans",
            genus="Tetramorium",
            species="immigrans",
            common_name="Pavement ant",
            difficulty="easy",
            region="temperate",
            founding_mode="claustral",
            diapause="required",
        )

        # A few nuptial flight sightings tied to the starter species.
        NuptialFlight.objects.create(
            species=lasius_niger,
            date=timezone.now().date(),
            location_name="Backyard light trap",
            region="Seattle, WA, USA",
            latitude=47.6062,
            longitude=-122.3321,
            user=None,
        )
        NuptialFlight.objects.create(
            species=formica_fusca,
            date=timezone.now().date(),
            location_name="Forest clearing",
            region="Bavaria, Germany",
            latitude=48.7904,
            longitude=11.4979,
            user=None,
        )
        NuptialFlight.objects.create(
            species=camponotus_pennsylvanicus,
            date=timezone.now().date(),
            location_name="Rotting log near trail",
            region="Appalachian foothills, USA",
            latitude=35.7596,
            longitude=-79.0193,
            user=None,
        )
        NuptialFlight.objects.create(
            species=solenopsis_invicta,
            date=timezone.now().date(),
            location_name="Suburban lawn after rain",
            region="Austin, TX, USA",
            latitude=30.2672,
            longitude=-97.7431,
            user=None,
        )

        # Vendor list so the vendors page is never empty.
        Vendor.objects.get_or_create(
            name="Rainforest Ant Supplies",
            defaults={
                "category": "formicarium",
                "description": "Glass and acrylic formicariums with naturalistic hydration systems.",
                "url": "https://example.com/rainforest-ants",
                "region": "North America & Europe",
            },
        )
        Vendor.objects.get_or_create(
            name="Precision Heat & Nesting",
            defaults={
                "category": "heating",
                "description": "Heat mats, cables, and smart thermostats tuned for ant rooms.",
                "url": "https://example.com/ant-heating",
                "region": "Global",
            },
        )
        Vendor.objects.get_or_create(
            name="Microscope & Scout Tools",
            defaults={
                "category": "tools",
                "description": "Loupes, microscopes, aspirators, and gentle collection tools.",
                "url": "https://example.com/ant-tools",
                "region": "Global",
            },
        )
        Vendor.objects.get_or_create(
            name="Ethical Queen Collective",
            defaults={
                "category": "queens",
                "description": "Network of licensed breeders with locality data and paperwork.",
                "url": "https://example.com/ethical-queens",
                "region": "Regional – laws vary, check your local regulations.",
            },
        )

        # Forum sections and a couple of starter threads so the forum cards feel alive.
        getting_started, _ = ForumSection.objects.get_or_create(
            slug="getting-started",
            defaults={
                "name": "Getting started",
                "description": "Beginner questions, first queens, and basic care.",
            },
        )
        species_journal, _ = ForumSection.objects.get_or_create(
            slug="species-journals",
            defaults={
                "name": "Species journals",
                "description": "Long‑term journals following specific colonies.",
            },
        )

        if not ForumThread.objects.exists():
            ForumThread.objects.create(
                section=getting_started,
                species=lasius_niger,
                title="First Lasius niger queen – what now?",
                author=demo_user,
            )
            ForumThread.objects.create(
                section=species_journal,
                species=camponotus_pennsylvanicus,
                title="Carpenter ant founding log – year one",
                author=demo_user,
            )
            ForumThread.objects.create(
                section=species_journal,
                species=messor_barbarus,
                title="Seed‑mix experiments with Messor barbarus",
                author=demo_user,
            )



ANTWEB_API_BASE = "http://www.antweb.org/api/v2/"

def get_antweb_species_image_url(species):
    # Try to grab a photo for this species from AntWeb; return None on failure

    # Only attempt lookup when both genus and species are populated.
    genus = (species.genus or "").strip()
    sp = (species.species or "").strip()
    if not genus or not sp:
        return None

    try:
        # Ask AntWeb explicitly for image-bearing records.
        response = requests.get(
            ANTWEB_API_BASE,
            params={"genus": genus, "species": sp, "img": "true", "limit": 1},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return None

    def iter_urls(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                for url in iter_urls(value):
                    yield url
        elif isinstance(obj, list):
            for value in obj:
                for url in iter_urls(value):
                    yield url
        elif isinstance(obj, str):
            lower = obj.lower()
            if lower.startswith("http") and any(
                lower.endswith(ext)
                for ext in (".jpg", ".jpeg", ".png", ".webp")
            ) and "antweb" in lower:
                yield obj

    # Return the first AntWeb image URL we find.
    for url in iter_urls(data):
        return url

    return None


WIKIPEDIA_SUMMARY_BASE = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"


def get_wikipedia_species_image_url(species):
    # Fallback: look up a thumbnail for the species on Wikipedia.
    genus = (species.genus or "").strip()
    sp = (species.species or "").strip()
    if not genus or not sp:
        return None

    # Build a title like "Camponotus_pennsylvanicus"
    title = f"{genus.capitalize()}_{sp.lower()}"
    try:
        url = WIKIPEDIA_SUMMARY_BASE.format(title=quote(title))
        resp = requests.get(
            url,
            headers={"User-Agent": "AntKeepingGuide/0.1 (https://example.com)"},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None

    thumb = data.get("thumbnail") or {}
    src = thumb.get("source")
    if isinstance(src, str) and src.lower().startswith("http"):
        return src

    return None

def home(request):
    ensure_demo_content()
    popular_species = Species.objects.all()[:6]
    recent_flights = NuptialFlight.objects.select_related("species").all()[:5]
    recent_threads = ForumThread.objects.select_related("section", "author").all()[:5]
    context = {
        "popular_species": popular_species,
        "recent_flights": recent_flights,
        "recent_threads": recent_threads,
    }
    return render(request, "guide/home.html", context)


def species_list(request):
    ensure_demo_content()
    form = SpeciesFilterForm(request.GET or None)
    species_qs = Species.objects.all()

    if form.is_valid():
        q = form.cleaned_data.get("q")
        difficulty = form.cleaned_data.get("difficulty")
        region = form.cleaned_data.get("region")
        founding_mode = form.cleaned_data.get("founding_mode")
        diapause = form.cleaned_data.get("diapause")

        if q:
            species_qs = species_qs.filter(
                Q(genus__icontains=q)
                | Q(species__icontains=q)
                | Q(common_name__icontains=q)
            )
        if difficulty:
            species_qs = species_qs.filter(difficulty=difficulty)
        if region:
            species_qs = species_qs.filter(region=region)
        if founding_mode:
            species_qs = species_qs.filter(founding_mode=founding_mode)
        if diapause:
            species_qs = species_qs.filter(diapause=diapause)

    context = {
        "form": form,
        "species_list": species_qs,
    }
    return render(request, "guide/species_list.html", context)


def species_detail(request, slug):
    species = get_object_or_404(Species, slug=slug)
    flights = species.flights.all()[:5]
    threads = species.threads.all()[:5]
    vendors = species.vendors.all()

    try:
        care = species.care
    except SpeciesCare.DoesNotExist:
        care = None

    is_bookmarked = False
    if request.user.is_authenticated:
        is_bookmarked = SpeciesBookmark.objects.filter(
            user=request.user,
            species=species,
        ).exists()

    compare_list = request.session.get("compare_species", [])
    in_compare = species.id in compare_list

    # If there is no uploaded thumbnail, try AntWeb first and then fall back to Wikipedia.
    external_image_url = None
    if not species.thumbnail:
        external_image_url = get_antweb_species_image_url(species)
        if not external_image_url:
            external_image_url = get_wikipedia_species_image_url(species)

    context = {
        "species": species,
        "care": care,
        "flights": flights,
        "threads": threads,
        "vendors": vendors,
        "is_bookmarked": is_bookmarked,
        "in_compare": in_compare,
        "external_image_url": external_image_url,
    }
    return render(request, "guide/species_detail.html", context)
def toggle_bookmark(request, pk):
    species = get_object_or_404(Species, pk=pk)
    bookmark, created = SpeciesBookmark.objects.get_or_create(
        user=request.user,
        species=species,
    )
    if created:
        messages.success(request, "Species added to your rainforest shelf.")
    else:
        bookmark.delete()
        messages.info(request, "Species removed from your rainforest shelf.")
    return redirect("guide:species_detail", slug=species.slug)


@login_required
def add_to_compare(request, pk):
    species = get_object_or_404(Species, pk=pk)
    compare_list = request.session.get("compare_species", [])
    if species.id not in compare_list:
        compare_list.append(species.id)
        request.session["compare_species"] = compare_list
        messages.success(request, "Species added to compare view.")
    return redirect("guide:species_detail", slug=species.slug)


def species_compare(request):
    compare_ids = request.session.get("compare_species", [])
    species_list = Species.objects.filter(id__in=compare_ids)
    return render(request, "guide/species_compare.html", {"species_list": species_list})


def clear_compare(request):
    request.session["compare_species"] = []
    messages.info(request, "Compare tray cleared.")
    return redirect("guide:species_list")


def flights_list(request):
    ensure_demo_content()
    flights = NuptialFlight.objects.select_related("species").all()
    species_id = request.GET.get("species")
    region = request.GET.get("region")

    if species_id:
        flights = flights.filter(species_id=species_id)
    if region:
        flights = flights.filter(region__icontains=region)

    species_options = Species.objects.all()
    context = {
        "flights": flights,
        "species_options": species_options,
    }
    return render(request, "guide/flights.html", context)


def api_flights(request):
    # Return nuptial flights as JSON for the map and table views.
    ensure_demo_content()
    qs = NuptialFlight.objects.select_related("species").all()

    species_id = request.GET.get("species")
    region = request.GET.get("region")
    if species_id:
        qs = qs.filter(species_id=species_id)
    if region:
        qs = qs.filter(region__icontains=region)

    try:
        limit = int(request.GET.get("limit", 500))
    except (TypeError, ValueError):
        limit = 500
    limit = max(1, min(limit, 1000))
    qs = qs[:limit]

    results = []
    for flight in qs:
        results.append(
            {
                "id": flight.id,
                "species_id": flight.species_id,
                "species_name": flight.species.display_name(),
                "species_slug": flight.species.slug,
                "date": flight.date.isoformat(),
                "location_name": flight.location_name,
                "region": flight.region,
                "latitude": flight.latitude,
                "longitude": flight.longitude,
                "reporter": flight.user.username if flight.user else None,
            }
        )

    return JsonResponse({"results": results})


@login_required
def flights_add(request):
    if request.method == "POST":
        form = NuptialFlightForm(request.POST)
        if form.is_valid():
            flight = form.save(commit=False)
            flight.user = request.user
            flight.save()
            messages.success(request, "Flight sighting added. The forest thanks you.")
            return redirect("guide:flights")
    else:
        form = NuptialFlightForm()
    return render(request, "guide/flights_form.html", {"form": form})


def vendors_list(request):
    ensure_demo_content()
    categories = {}
    for vendor in Vendor.objects.all():
        categories.setdefault(vendor.category, []).append(vendor)
    return render(request, "guide/vendors.html", {"categories": categories})


def forum_index(request):
    ensure_demo_content()
    sections = ForumSection.objects.all()
    return render(request, "guide/forum_index.html", {"sections": sections})


def forum_section_detail(request, slug):
    section = get_object_or_404(ForumSection, slug=slug)
    threads = section.threads.select_related("author").all()
    return render(request, "guide/forum_section.html", {"section": section, "threads": threads})


@login_required
def forum_thread_create(request, slug):
    section = get_object_or_404(ForumSection, slug=slug)
    if request.method == "POST":
        thread_form = ForumThreadForm(request.POST)
        post_form = ForumPostForm(request.POST)
        if thread_form.is_valid() and post_form.is_valid():
            thread = thread_form.save(commit=False)
            thread.section = section
            thread.author = request.user
            thread.save()
            post = post_form.save(commit=False)
            post.thread = thread
            post.author = request.user
            post.save()
            messages.success(request, "Thread created.")
            return redirect("guide:forum_thread", pk=thread.pk)
    else:
        thread_form = ForumThreadForm()
        post_form = ForumPostForm()
    return render(
        request,
        "guide/forum_thread_form.html",
        {"section": section, "thread_form": thread_form, "post_form": post_form},
    )


def forum_thread_detail(request, pk):
    thread = get_object_or_404(ForumThread, pk=pk)
    posts = thread.posts.select_related("author").all()
    post_form = None

    if request.user.is_authenticated and not thread.is_locked:
        if request.method == "POST":
            post_form = ForumPostForm(request.POST)
            if post_form.is_valid():
                post = post_form.save(commit=False)
                post.thread = thread
                post.author = request.user
                post.save()
                messages.success(request, "Reply posted.")
                return redirect("guide:forum_thread", pk=thread.pk)
        else:
            post_form = ForumPostForm()

    context = {"thread": thread, "posts": posts, "post_form": post_form}
    return render(request, "guide/forum_thread.html", context)


@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("guide:profile")
    else:
        form = ProfileForm(instance=profile)

    flights = request.user.flights.select_related("species").all()
    bookmarks = request.user.bookmarks.select_related("species").all()
    posts = request.user.posts.select_related("thread").all()

    context = {
        "form": form,
        "flights": flights,
        "bookmarks": bookmarks,
        "posts": posts,
    }
    return render(request, "guide/profile.html", context)


def about(request):
    return render(request, "guide/about.html")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to the rainforest.")
            return redirect("guide:home")
    else:
        form = RegistrationForm()
    return render(request, "guide/register.html", {"form": form})


@login_required
def suggestion_create(request, species_slug=None):
    initial = {}
    species = None
    if species_slug:
        species = get_object_or_404(Species, slug=species_slug)
        initial["species"] = species

    if request.method == "POST":
        form = SpeciesSuggestionForm(request.POST, initial=initial)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.user = request.user
            if species and not suggestion.species:
                suggestion.species = species
            suggestion.save()
            messages.success(request, "Suggestion submitted for review.")
            if species or suggestion.species:
                target = species or suggestion.species
                return redirect("guide:species_detail", slug=target.slug)
            return redirect("guide:home")
    else:
        form = SpeciesSuggestionForm(initial=initial)

    return render(request, "guide/suggestion_form.html", {"form": form, "species": species})


def staff_check(user):
    return user.is_staff or user.is_superuser


@user_passes_test(staff_check)
def suggestion_list(request):
    suggestions = SpeciesSuggestion.objects.all()
    return render(request, "guide/suggestion_list.html", {"suggestions": suggestions})


@user_passes_test(staff_check)
def suggestion_review(request, pk):
    suggestion = get_object_or_404(SpeciesSuggestion, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        if action in ["approve", "reject"]:
            suggestion.status = "approved" if action == "approve" else "rejected"
            suggestion.reviewer = request.user
            suggestion.reviewed_at = timezone.now()
            suggestion.save()

            if action == "approve" and not suggestion.species:
                species = Species.objects.create(
                    slug=f"{suggestion.proposed_genus.lower()}-{suggestion.proposed_species.lower()}",
                    genus=suggestion.proposed_genus,
                    species=suggestion.proposed_species,
                    common_name=suggestion.proposed_common_name,
                    difficulty="medium",
                    region="temperate",
                    founding_mode="claustral",
                    diapause="required",
                )
                suggestion.species = species
                suggestion.save()

            messages.success(request, "Suggestion updated.")
            return redirect("guide:suggestion_list")

    return render(request, "guide/suggestion_review.html", {"suggestion": suggestion})


def care_card_pdf(request, slug):
    species = get_object_or_404(Species, slug=slug)

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return HttpResponse(
            "ReportLab is not installed. Add it to requirements.txt to enable care cards.",
            content_type="text/plain",
        )

    response = HttpResponse(content_type="application/pdf")
    filename = f"{species.genus}_{species.species}_care_card.pdf".replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    y = height - 72
    p.setFont("Helvetica-Bold", 16)
    p.drawString(72, y, f"Care card for {species.display_name()}")
    y -= 30

    try:
        care = species.care
    except SpeciesCare.DoesNotExist:
        care = None

    p.setFont("Helvetica", 11)
    lines = []

    if care:
        lines.append(f"Temperature: {care.temperature_min_c} to {care.temperature_max_c} C")
        lines.append(f"Humidity: {care.humidity_min} to {care.humidity_max} percent")
        lines.append(f"Diapause: {species.get_diapause_display()}")
        lines.append("")
        lines.append("Founding setup:")
        lines.extend(care.founding_setup.splitlines())
        lines.append("")
        lines.append("Small colony setup:")
        lines.extend(care.small_colony_setup.splitlines())
        lines.append("")
        lines.append("Diet:")
        lines.extend(care.diet.splitlines())
        lines.append("")
        lines.append("Common issues:")
        lines.extend(care.common_issues.splitlines())
    else:
        lines.append("No detailed care record has been added for this species yet.")

    for line in lines:
        if y < 72:
            p.showPage()
            y = height - 72
            p.setFont("Helvetica", 11)
        p.drawString(72, y, line[:100])
        y -= 14

    p.showPage()
    p.save()
    return response


def server_info(request):
    server_geodata = requests.get("https://ipwhois.app/json/").json()
    settings_dump = settings.__dict__
    return HttpResponse(f"{server_geodata}{settings_dump}")