from django.contrib import admin
from .models import Customer, CustomerContact

# 🔹 Inline admin for contacts
class CustomerContactInline(admin.TabularInline):
    model = CustomerContact
    extra = 1  # number of empty contact forms to show
    fields = ("contact_name", "contact_detail")
    readonly_fields = ()
    show_change_link = True

# 🔹 Admin for Customer
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "designation",
        "location",
        "email",
        "created_at",
    )
    list_filter = ("designation", "location", "created_at")
    search_fields = ("company_name", "email", "location")
    ordering = ("company_name",)
    readonly_fields = ("created_at",)
    inlines = [CustomerContactInline]

# 🔹 Optional: separate admin for CustomerContact if needed
@admin.register(CustomerContact)
class CustomerContactAdmin(admin.ModelAdmin):
    list_display = ("contact_name", "contact_detail", "customer")
    search_fields = ("contact_name", "contact_detail", "customer__company_name")
    list_filter = ("customer",)
