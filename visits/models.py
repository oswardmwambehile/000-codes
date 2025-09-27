from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils.timezone import now, localdate


# -------------------
# Custom User
# -------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    POSITION_CHOICES = [
        ('Head of Sales', 'Head of Sales'),
        ('Facilitator', 'Facilitator'),
        ('Product Brand Manager', 'Product Brand Manager'),
        ('Corporate Manager', 'Corporate Manager'),
        ('Corporate Officer', 'Corporate Officer'),
        ('Zonal Sales Executive', 'Zonal Sales Executive'),
        ('Mobile Sales Officer', 'Mobile Sales Officer'),
        ('Desk Sales Officer', 'Desk Sales Officer'),
        ('Admin', 'Admin'),
    ]

    ZONE_CHOICES = [
        ('Coast Zone', 'Coast Zone'),
        ('Corporate', 'Corporate'),
        ('Central Zone', 'Central Zone'),
        ('Southern Zone', 'Southern Zone'),
        ('Northern Zone', 'Northern Zone'),
        ('Lake Zone', 'Lake Zone'),
    ]

    BRANCH_CHOICES = [
        ('Chanika', 'Chanika'),
        ('Mikocheni', 'Mikocheni'),
        ('Morogoro', 'Morogoro'),
        ('Zanzibar', 'Zanzibar'),
        ('ANDO HQ', 'ANDO HQ'),
        ('Dodoma', 'Dodoma'),
        ('Singida', 'Singida'),
        ('Tabora', 'Tabora'),
        ('Mbeya', 'Mbeya'),
        ('Tunduma', 'Tunduma'),
        ('Arusha', 'Arusha'),
        ('Moshi', 'Moshi'),
        ('Mwanza', 'Mwanza'),
        ('Geita', 'Geita'),
    ]
    COMPANY_CHOICES = [
        ('ANDO', 'ANDO'),
        ('KAM', 'KAM'),
        ('MATE', 'MATE'),
    ]
    # ✅ New field for company name
    company_name = models.CharField(max_length=50, choices=COMPANY_CHOICES, null=True, blank=True)

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=50, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    position = models.CharField(max_length=100, choices=POSITION_CHOICES, null=True, blank=True)
    zone = models.CharField(max_length=100, choices=ZONE_CHOICES, null=True, blank=True)
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES, null=True, blank=True)

    contact = models.CharField(
        max_length=13,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^(?:\+255|0)[67][0-9]\d{7}$',
                message="Enter a valid Tanzanian phone number (e.g. +255712345678 or 0712345678)"
            )
        ]
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name
    

from django.db import models
from django.conf import settings
from customer.models import Customer, CustomerContact
from decimal import Decimal


class NewVisit(models.Model):
    MEETING_STAGE_CHOICES = [
        ("Prospecting", "Prospecting"),
        ("Qualifying", "Qualifying"),
        ("Proposal or Negotiation", "Proposal or Negotiation"),
        ("Closing", "Closing"),
        ("Payment Followup", "Payment followup"),
    ]

    TAG_CHOICES = [
        ("Prospect", "Prospect"),
        ("Lead", "Lead"),
        ("Customer", "Customer"),
    ]

    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Won Paid", "Won Paid"),
        ("Won Pending Payment", "Won Pending Payment"),
        ("Lost", "Lost"),
    ]

    PAYMENT_CHOICES = [
        ("Yes-Full", "Yes-Full"),
        ("Yes-Partial", "Yes-Partial"),
        ("No", "No"),
    ]
    MEETING_TYPE_CHOICES = [
        ("In Person", "In Person"),
        ("Phone Call", "Phone Call"),
    ]


    company_name = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="visits", null=True, blank=True)
    contact_person = models.ForeignKey(CustomerContact, on_delete=models.CASCADE, related_name="visits", null=True, blank=True)
    contact_number = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPE_CHOICES)  # ✅ Meeting type

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    visit_image = models.ImageField(upload_to="visit_images/", null=True, blank=True)

    meeting_stage = models.CharField(max_length=50, choices=MEETING_STAGE_CHOICES, default="Prospecting")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Open", blank=True, null=True)
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, default="Prospect", null=True, blank=True)

    item_discussed = models.TextField(max_length=255)
    client_budget = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    is_order_final = models.BooleanField(null=True, blank=True)
    contract_outcome = models.CharField(max_length=10, choices=[("Won", "Won"), ("Lost", "Lost")], null=True, blank=True)
    contract_amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    reason_lost = models.TextField(null=True, blank=True)

    # ✅ Payment collection field
    is_payment_collected = models.CharField(max_length=20, choices=PAYMENT_CHOICES, null=True, blank=True)

    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_payment_status(self):
        if self.contract_outcome != "Won":
            return

        products = self.products.all()

        total_remaining = sum((p.final_order_amount or 0) - p.total_collected for p in products)
        total_collected = sum(p.total_collected for p in products)

        # --- Stage-specific logic ---
        if self.meeting_stage == "Closing":
            # Trust the user selection
            if self.is_payment_collected == "Yes-Full":
                self.status = "Won Paid"
            elif self.is_payment_collected == "Yes-Partial":
                self.status = "Won Pending Payment"
            elif self.is_payment_collected == "No":
                self.status = None

        elif self.meeting_stage == "Payment Followup":
            # Always recalc from balances
            if total_remaining == 0 and total_collected > 0:
                self.is_payment_collected = "Yes-Full"
                self.status = "Won Paid"
            elif total_collected > 0:
                self.is_payment_collected = "Yes-Partial"
                self.status = "Won Pending Payment"
            else:
                self.is_payment_collected = "No"
                self.status = None



    def update_stage_logic(self):
        """Set tag and status depending on stage, contract outcome, and payment collection."""
        if self.meeting_stage == "Prospecting":
            self.status = "Open"
            self.tag = "Prospect"
        elif self.meeting_stage == "Qualifying":
            self.status = "Open"
            self.tag = "Lead"
        elif self.meeting_stage == "Proposal or Negotiation":
            self.status = "Open"
            self.tag = "Lead"
        elif self.meeting_stage == "Closing":
            self.tag = "Customer" if self.contract_outcome == "Won" else None
            # Use payment info already calculated
            if self.contract_outcome == "Won":
                if self.is_payment_collected == "Yes-Full":
                    self.status = "Won Paid"
                elif self.is_payment_collected == "Yes-Partial":
                    self.status = "Won Pending Payment"
                else:
                    self.status = "Won Pending Payment"
            elif self.contract_outcome == "Lost":
                self.status = "Lost"

    def save(self, *args, **kwargs):
        # First, calculate payment status from products
        self.update_payment_status()
        # Then, set stage logic (tags/status) based on updated payment info
        self.update_stage_logic()
        super().save(*args, **kwargs)


    def __str__(self):
        company = self.company_name.company_name if self.company_name else "No Company"
        contact = self.contact_person.contact_name if self.contact_person else "No Contact"
        return f"Visit: {company} - {contact}"

class ProductInterested(models.Model):
    PRODUCT_CHOICES = [
        ("RESIN_ROOFING_SHEETS", "RESIN ROOFING SHEETS"),
        ("ROOF_PAINT", "ROOF PAINT"),
        ("UPVC", "UPVC"),
        ("WALL_COATING", "WALL COATING"),
        ("ZEBRA_TILES", "ZEBRA TILES"),
    ]

    visit = models.ForeignKey(NewVisit, on_delete=models.CASCADE, related_name="products")
    product_interested = models.CharField(max_length=30, choices=PRODUCT_CHOICES)
    order_estimate = models.PositiveIntegerField(null=True, blank=True)
    final_order_amount = models.PositiveIntegerField(null=True, blank=True)
    payment_collected = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    @property
    def total_collected(self):
        return self.payment_history.aggregate(total=models.Sum("amount_collected"))["total"] or 0

    @property
    def remaining_balance(self):
        return max((self.final_order_amount or 0) - self.total_collected, 0)

    def __str__(self):
        return f"{self.visit} - {self.get_product_interested_display()}"


class ProductPaymentHistory(models.Model):
    product = models.ForeignKey(ProductInterested, on_delete=models.CASCADE, related_name="payment_history")
    amount_collected = models.DecimalField(max_digits=19, decimal_places=2)
    collected_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    collected_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.product} - {self.amount_collected} on {self.collected_at.strftime('%Y-%m-%d %H:%M')}"


class VisitStageHistory(models.Model):
    visit = models.ForeignKey(NewVisit, related_name="stage_history", on_delete=models.CASCADE)

    meeting_stage = models.CharField(max_length=50, choices=NewVisit.MEETING_STAGE_CHOICES)
    contract_outcome = models.CharField(max_length=10, choices=[("Won", "Won"), ("Lost", "Lost")], null=True, blank=True)
    is_payment_collected = models.CharField(max_length=20, choices=NewVisit.PAYMENT_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=30, choices=NewVisit.STATUS_CHOICES, null=True, blank=True)

    # ⬅️ Snapshot fields
    client_budget = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    contact_person_name = models.CharField(max_length=255, null=True, blank=True)
    contact_number = models.CharField(max_length=255, null=True, blank=True)
    designation = models.CharField(max_length=255, null=True, blank=True)
    contract_amount = models.DecimalField(max_digits=19, decimal_places=2, null=True, blank=True)
    is_order_final = models.BooleanField(null=True, blank=True)
    tag = models.CharField(max_length=20, null=True, blank=True)
    item_discussed = models.TextField(max_length=255, null=True, blank=True)

    # JSON snapshot of products for that stage
    products_snapshot = models.JSONField(default=list, blank=True)
    visit_image = models.ImageField(upload_to="visit_stage_images/", null=True, blank=True)  # ✅ Added
    meeting_type = models.CharField(max_length=20, choices=NewVisit.MEETING_TYPE_CHOICES, null=True, blank=True)  # 

    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.visit} → {self.meeting_stage} at {self.updated_at}"


