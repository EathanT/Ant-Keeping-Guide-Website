from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150, blank=True)
    favorite_region = models.CharField(max_length=100, blank=True)
    receive_email_updates = models.BooleanField(default=True)

    def __str__(self):
        return self.display_name or self.user.username


class Species(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]
    REGION_CHOICES = [
        ("temperate", "Temperate"),
        ("tropical", "Tropical"),
        ("desert", "Desert"),
        ("mediterranean", "Mediterranean"),
        ("other", "Other"),
    ]
    FOUNDING_MODE_CHOICES = [
        ("claustral", "Fully claustral"),
        ("semi_claustral", "Semi claustral"),
        ("parasitic", "Parasitic"),
        ("dependent", "Dependent"),
    ]
    DIAPAUSE_CHOICES = [
        ("required", "Requires diapause"),
        ("light", "Light diapause"),
        ("none", "No diapause"),
    ]

    slug = models.SlugField(unique=True)
    genus = models.CharField(max_length=100)
    species = models.CharField(max_length=100, blank=True)
    common_name = models.CharField(max_length=150, blank=True)

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)
    region = models.CharField(max_length=20, choices=REGION_CHOICES)
    founding_mode = models.CharField(max_length=20, choices=FOUNDING_MODE_CHOICES)
    diapause = models.CharField(max_length=20, choices=DIAPAUSE_CHOICES)

    thumbnail = models.ImageField(upload_to="species_thumbs/", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["genus", "species"]

    def __str__(self):
        return f"{self.genus} {self.species}".strip()

    def display_name(self):
        if self.common_name:
            return f"{self.common_name} ({self.genus} {self.species})".strip()
        return str(self)

    def care_safe(self):
        try:
            return self.care
        except ObjectDoesNotExist:
            return None


class SpeciesCare(models.Model):
    species = models.OneToOneField(Species, on_delete=models.CASCADE, related_name="care")
    temperature_min_c = models.PositiveIntegerField()
    temperature_max_c = models.PositiveIntegerField()
    humidity_min = models.PositiveIntegerField(help_text="As percent")
    humidity_max = models.PositiveIntegerField(help_text="As percent")

    diapause_notes = models.TextField()
    founding_setup = models.TextField()
    small_colony_setup = models.TextField()
    medium_colony_setup = models.TextField()
    large_colony_setup = models.TextField()
    diet = models.TextField()
    common_issues = models.TextField(blank=True)

    def __str__(self):
        return f"Care for {self.species}"


class Vendor(models.Model):
    CATEGORY_CHOICES = [
        ("formicarium", "Formicariums"),
        ("heating", "Heating"),
        ("tools", "Tools"),
        ("queens", "Legal queen sellers"),
        ("other", "Other"),
    ]
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    url = models.URLField()
    region = models.CharField(max_length=100, blank=True)
    is_trusted = models.BooleanField(default=True)
    species = models.ManyToManyField("Species", blank=True, related_name="vendors")

    def __str__(self):
        return self.name


class NuptialFlight(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="flights")
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flights",
    )
    location_name = models.CharField(max_length=200)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    date = models.DateField()
    region = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.species} at {self.location_name} on {self.date}"


class ForumSection(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = "Forum section"
        verbose_name_plural = "Forum sections"

    def __str__(self):
        return self.name


class ForumThread(models.Model):
    section = models.ForeignKey(ForumSection, on_delete=models.CASCADE, related_name="threads")
    species = models.ForeignKey(
        Species,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="threads",
    )
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="threads")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def last_post(self):
        return self.posts.order_by("-created_at").first()


class ForumPost(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Post by {self.author} in {self.thread}"


class SpeciesBookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "species")

    def __str__(self):
        return f"{self.user} bookmarked {self.species}"


class SpeciesSuggestion(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggestions",
    )
    species = models.ForeignKey(
        Species,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="suggestions",
    )

    proposed_genus = models.CharField(max_length=100)
    proposed_species = models.CharField(max_length=100, blank=True)
    proposed_common_name = models.CharField(max_length=150, blank=True)
    care_notes = models.TextField()
    reason = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_suggestions",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Suggestion for {self.proposed_genus} {self.proposed_species}".strip()
