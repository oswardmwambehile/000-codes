from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from django.contrib import messages

def add_visit(request):
    return render(request, 'users/add_vist.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re

User = get_user_model()

def register(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password1 = request.POST.get('password1')
        position = request.POST.get('position')
        zone = request.POST.get('zone')
        branch = request.POST.get('branch')
        contact = request.POST.get('contact')
        company_name = request.POST.get('company_name')  # ✅ New

        # Password validation...
        if password != password1:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('register')
        if not re.search(r'[A-Z]', password):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect('register')
        if not re.search(r'[a-z]', password):
            messages.error(request, "Password must contain at least one lowercase letter.")
            return redirect('register')
        if not re.search(r'\d', password):
            messages.error(request, "Password must contain at least one digit.")
            return redirect('register')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            messages.error(request, "Password must contain at least one special character.")
            return redirect('register')

        try:
            validate_password(password)
        except ValidationError as e:
            for error in e:
                messages.error(request, error)
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        if not re.match(r'^(?:\+255|0)[67][1-9]\d{7}$', contact):
            messages.error(request, "Enter a valid Tanzanian phone number (e.g. +255712345678 or 0712345678).")
            return redirect('register')

        if User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists():
            messages.error(request, "A user with this first and last name already exists.")
            return redirect('register')

        # ✅ Create user with company_name
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            position=position,
            zone=zone,
            branch=branch,
            contact=contact,
            company_name=company_name  # ✅ Include here
        )

        messages.success(request, "User created successfully.")
        return redirect('register')

    return render(request, 'company/add_user.html')

# The POSITION_CHOICES tuple
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

def login_user(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        # Authenticate with email as username (because USERNAME_FIELD = 'email')
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            # Check user's position and redirect accordingly
            if user.position in ['Facilitator', 'Product Brand Manager', 'Zonal Sales Executive']:
                return redirect('add_visit')  # Redirect to 'index' for these positions
            elif user.position in ['Corporate Officer', 'Mobile Sales Officer', 'Desk Sales Officer']:
                return redirect('dashboard')  # Redirect to 'dashboard' for these positions
            else:
                return redirect('index')  # Default redirect for all other positions
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    # Handle GET request: Render the login page/form
    return render(request, 'auth/login.html')  # Ensure you have a 'login.html' template





def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect('login')
    else:
        messages.error(request,'You must login first to access the page')
        return redirect('login')



from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .forms import NewVisitForm, ProductInterestedFormSet
from .models import CustomerContact, NewVisit, ProductInterested

@login_required
def new_visit(request):
    if request.method == "POST":
        # ✅ Include request.FILES for image uploads
        form = NewVisitForm(request.POST, request.FILES)
        formset = ProductInterestedFormSet(request.POST, queryset=ProductInterested.objects.none())

        if form.is_valid() and formset.is_valid():
            # 🔒 Restriction: allow only if no visit exists OR last visit is "Won Paid"
            company = form.cleaned_data.get("company_name")
            if company:
                existing_visits = NewVisit.objects.filter(company_name=company).order_by("-id")
                if existing_visits.exists():
                    latest_visit = existing_visits.first()
                    if latest_visit.status != "Won Paid":
                        messages.error(
                            request,
                            f"A visit for {company} already exists with status '{latest_visit.status}'. "
                            "You can only add a new visit if the last one is 'Won Paid'."
                        )
                        return render(request, "users/new_visit.html", {"form": form, "formset": formset})

            # Save visit if restriction passes
            visit = form.save(commit=False)
            visit.added_by = request.user
            visit.save()

            for f in formset:
                if f.cleaned_data and not f.cleaned_data.get("DELETE", False):
                    product = f.save(commit=False)
                    product.visit = visit
                    product.save()

            messages.success(request, "New visit created successfully!")
            return redirect("all_visit_list")
        else:
            print("❌ Visit form errors:", form.errors)
            print("❌ Product formset errors:", formset.errors)
    else:
        form = NewVisitForm()
        formset = ProductInterestedFormSet(queryset=ProductInterested.objects.none())

    return render(request, "users/new_visit.html", {"form": form, "formset": formset})



# -------------------------------
# Get contacts by company_id (AJAX)
# -------------------------------
@login_required
def get_contacts(request, company_id):
    contacts = CustomerContact.objects.filter(customer_id=company_id).order_by("contact_name")
    data = [
        {
            "id": c.id,
            "contact_name": c.contact_name
        }
        for c in contacts
    ]
    return JsonResponse({"contacts": data})


# -------------------------------
# Get contact details by contact_id (AJAX)
# -------------------------------
@login_required
def get_contact_details(request, contact_id):
    contact = get_object_or_404(CustomerContact, id=contact_id)
    data = {
        "contact_number": contact.contact_detail or "",
        "designation": contact.customer.designation or ""
    }
    return JsonResponse(data)


from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.dateparse import parse_date
from .models import NewVisit
import requests

def get_location_name(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1}
        headers = {"User-Agent": "my_visits_app_ando_2025"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "address" in data:
                addr = data["address"]
                return {
                    "place_name": data.get("display_name", "Unknown"),
                    "region": addr.get("state", ""),
                    "zone": addr.get("county", ""),
                    "nation": addr.get("country", ""),
                }
    except Exception as e:
        print(f"Reverse geocode error: {e}")
    return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}

@login_required
def all_visit_list(request):
    created_date = request.GET.get("created_date")
    visits_qs = NewVisit.objects.filter(added_by=request.user).order_by("-created_at")

    if created_date:
        parsed_date = parse_date(created_date)
        if parsed_date:
            visits_qs = visits_qs.filter(created_at__date=parsed_date)

    paginator = Paginator(visits_qs, 20)
    page_number = request.GET.get("page")
    visits_page = paginator.get_page(page_number)

    for visit in visits_page:
        if visit.latitude and visit.longitude:
            loc = get_location_name(visit.latitude, visit.longitude)
            visit.place_name = loc["place_name"]
            visit.region = loc["region"]
            visit.zone = loc["zone"]
            visit.nation = loc["nation"]
        else:
            visit.place_name = "Not Available"
            visit.region = ""
            visit.zone = ""
            visit.nation = ""

    return render(
        request,
        "users/all_visit_list.html",
        {"visits": visits_page, "created_date": created_date},
    )



from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.dateparse import parse_date
from .models import NewVisit
import requests

def get_location_name(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1}
        headers = {"User-Agent": "my_visits_app_ando_2025"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "address" in data:
                addr = data["address"]
                return {
                    "place_name": data.get("display_name", "Unknown"),
                    "region": addr.get("state", ""),
                    "zone": addr.get("county", ""),
                    "nation": addr.get("country", ""),
                }
    except Exception as e:
        print(f"Reverse geocode error: {e}")
    return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}

def adminall_visit_list(request):
    # Base queryset: all visits
    visits_qs = NewVisit.objects.all().order_by("-created_at")

    # Filtering
    created_date = request.GET.get("created_date")
    status = request.GET.get("status")
    meeting_stage = request.GET.get("meeting_stage")
    tag = request.GET.get("tag")

    if created_date:
        parsed_date = parse_date(created_date)
        if parsed_date:
            visits_qs = visits_qs.filter(created_at__date=parsed_date)

    if status:
        visits_qs = visits_qs.filter(status__iexact=status)  # <-- use status field

    if meeting_stage:
        visits_qs = visits_qs.filter(meeting_stage__iexact=meeting_stage)

    if tag:
        visits_qs = visits_qs.filter(tag__iexact=tag)

    # Pagination
    paginator = Paginator(visits_qs, 20)
    page_number = request.GET.get("page")
    visits_page = paginator.get_page(page_number)

    # Add location info
    for visit in visits_page:
        if visit.latitude and visit.longitude:
            loc = get_location_name(visit.latitude, visit.longitude)
            visit.place_name = loc["place_name"]
            visit.region = loc["region"]
            visit.zone = loc["zone"]
            visit.nation = loc["nation"]
        else:
            visit.place_name = "Not Available"
            visit.region = ""
            visit.zone = ""
            visit.nation = ""

    # For dropdowns in template
    meeting_stages = [s[0] for s in NewVisit.MEETING_STAGE_CHOICES]
    tags = [t[0] for t in NewVisit.TAG_CHOICES]
    status_choices = [s[0] for s in NewVisit.STATUS_CHOICES]

    context = {
        "visits": visits_page,
        "created_date": created_date,
        "status": status,
        "meeting_stage": meeting_stage,
        "tag": tag,
        "meeting_stages": meeting_stages,
        "tags": tags,
        "status_choices": status_choices,
    }

    return render(request, "company/adminall_visit_list.html", context)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import NewVisit
import requests

def get_location_name(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1}
        headers = {"User-Agent": "my_visits_app_ando_2025"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            addr = data.get("address", {})
            return {
                "place_name": data.get("display_name", "Unknown"),
                "region": addr.get("state", ""),
                "zone": addr.get("county", ""),
                "nation": addr.get("country", ""),
            }
    except Exception as e:
        print(f"Reverse geocode error: {e}")
    return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}


@login_required
def visit_detail(request, visit_id):
    visit = get_object_or_404(NewVisit, id=visit_id)

    # Add location details
    if visit.latitude and visit.longitude:
        loc = get_location_name(visit.latitude, visit.longitude)
        visit.place_name = loc["place_name"]
        visit.region = loc["region"]
        visit.zone = loc["zone"]
        visit.nation = loc["nation"]
    else:
        visit.place_name = "Not Available"
        visit.region = ""
        visit.zone = ""
        visit.nation = ""

    products_interested = visit.products.all()
    total_final_order = sum(p.final_order_amount or 0 for p in products_interested)

    # 🟢 Attach display-only fields
    if visit.status == "Won Paid":
        total_payment_collected = total_final_order
        total_balance = 0
        for p in products_interested:
            p.display_collected = p.final_order_amount or 0
            p.display_balance = 0
    else:
        total_payment_collected = sum(p.total_collected or 0 for p in products_interested)
        total_balance = sum(p.remaining_balance or 0 for p in products_interested)
        for p in products_interested:
            p.display_collected = p.total_collected or 0
            p.display_balance = p.remaining_balance or 0

    return render(request, "users/visit_detail.html", {
        "visit": visit,
        "products_interested": products_interested,
        "total_final_order": total_final_order,
        "total_payment_collected": total_payment_collected,
        "total_balance": total_balance,
    })



from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import NewVisit
import requests

def get_location_name(lat, lon):
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 10, "addressdetails": 1}
        headers = {"User-Agent": "my_visits_app_ando_2025"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            addr = data.get("address", {})
            return {
                "place_name": data.get("display_name", "Unknown"),
                "region": addr.get("state", ""),
                "zone": addr.get("county", ""),
                "nation": addr.get("country", ""),
            }
    except Exception as e:
        print(f"Reverse geocode error: {e}")
    return {"place_name": "Unknown", "region": "", "zone": "", "nation": ""}


@login_required
def visit_details(request, visit_id):
    visit = get_object_or_404(NewVisit, id=visit_id)

    # Add location details
    if visit.latitude and visit.longitude:
        loc = get_location_name(visit.latitude, visit.longitude)
        visit.place_name = loc["place_name"]
        visit.region = loc["region"]
        visit.zone = loc["zone"]
        visit.nation = loc["nation"]
    else:
        visit.place_name = "Not Available"
        visit.region = ""
        visit.zone = ""
        visit.nation = ""

    products_interested = visit.products.all()
    total_final_order = sum(p.final_order_amount or 0 for p in products_interested)

    # 🟢 Attach display-only fields
    if visit.status == "Won Paid":
        total_payment_collected = total_final_order
        total_balance = 0
        for p in products_interested:
            p.display_collected = p.final_order_amount or 0
            p.display_balance = 0
    else:
        total_payment_collected = sum(p.total_collected or 0 for p in products_interested)
        total_balance = sum(p.remaining_balance or 0 for p in products_interested)
        for p in products_interested:
            p.display_collected = p.total_collected or 0
            p.display_balance = p.remaining_balance or 0

    return render(request, "company/visit_detail.html", {
        "visit": visit,
        "products_interested": products_interested,
        "total_final_order": total_final_order,
        "total_payment_collected": total_payment_collected,
        "total_balance": total_balance,
    })


from django.contrib.auth import authenticate, update_session_auth_hash



def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password1) < 8:
            messages.error(request, 'New password must be at least 8 characters.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # keep user logged in
            messages.success(request, 'Password changed successfully.')
            return redirect('change_password')

    return render(request, 'users/change_password.html')

def adminchange_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password1) < 8:
            messages.error(request, 'New password must be at least 8 characters.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # keep user logged in
            messages.success(request, 'Password changed successfully.')
            return redirect('change_password')

    return render(request, 'company/change_password.html')

@login_required
def profile_view(request):
    user = request.user  # The logged-in user
    return render(request, 'users/profile.html', {'user': user})



@login_required
def adminprofile_view(request):
    user = request.user  # The logged-in user
    return render(request, 'company/profile.html', {'user': user})



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from .forms import UpdateVisitForm, UpdateProductInterestedForm
from .models import NewVisit, ProductInterested, ProductPaymentHistory, VisitStageHistory
from decimal import Decimal
import json


@login_required
def update_visit(request, visit_id):
    visit = get_object_or_404(NewVisit, id=visit_id)

    stage = request.POST.get("meeting_stage") or visit.meeting_stage
    contract_outcome = request.POST.get("contract_outcome") or visit.contract_outcome

    extra_forms = 1 if request.method == "GET" and visit.products.count() == 0 else 0
    ProductFormSet = modelformset_factory(
        ProductInterested,
        form=UpdateProductInterestedForm,
        extra=extra_forms,
        can_delete=True
    )

    if request.method == "POST":
        visit_form = UpdateVisitForm(request.POST, request.FILES, instance=visit, stage=stage)  # ✅ Include FILES
        formset = ProductFormSet(
            request.POST,
            queryset=visit.products.all(),
            form_kwargs={"stage": stage, "contract_outcome": contract_outcome},
            prefix="product"
        )

        if visit_form.is_valid() and formset.is_valid():
            visit = visit_form.save(commit=False)
            visit.company_name = NewVisit.objects.get(id=visit.id).company_name
            visit.meeting_stage = stage
            visit.contract_outcome = contract_outcome
            visit.save()

            products_snapshot = []

            for form in formset:
                if form.cleaned_data.get("DELETE") and form.instance.pk:
                    form.instance.delete()
                    continue

                product = form.save(commit=False)
                product.visit = visit

                for f in ["order_estimate", "final_order_amount"]:
                    if getattr(product, f) is None:
                        setattr(product, f, 0)

                if stage == "Payment Followup":
                    paid_amount = form.cleaned_data.get("payment_collected") or 0
                    paid_amount = Decimal(paid_amount)

                    if paid_amount > 0:
                        remaining_for_product = product.remaining_balance

                        if paid_amount > remaining_for_product:
                            paid_amount = remaining_for_product

                        if paid_amount > 0:
                            ProductPaymentHistory.objects.create(
                                product=product,
                                amount_collected=paid_amount,
                                collected_by=request.user
                            )

                product.save()  # Save any manual field changes

                products_snapshot.append({
                    "product_interested": product.get_product_interested_display(),
                    "order_estimate": float(product.order_estimate or 0),
                    "final_order_amount": float(product.final_order_amount or 0),
                    "total_collected": float(product.total_collected),
                    "remaining_balance": float(product.remaining_balance),
                })

            # Handle temp products
            temp_products = [v for k, v in request.POST.items() if k.startswith("temp_product_")]
            for product_name in temp_products:
                if not visit.products.filter(product_interested=product_name).exists():
                    product = ProductInterested.objects.create(
                        visit=visit,
                        product_interested=product_name,
                        order_estimate=0,
                        final_order_amount=0,
                        payment_collected=0
                    )
                    products_snapshot.append({
                        "product_interested": product.get_product_interested_display(),
                        "order_estimate": float(product.order_estimate),
                        "final_order_amount": float(product.final_order_amount),
                        "total_collected": float(product.total_collected),
                        "remaining_balance": float(product.remaining_balance),
                    })

            # ✅ Recalculate status after payments
            visit.update_payment_status()
            visit.save()  # ensure status is persisted

            # Save stage history with meeting_type and visit_image
            VisitStageHistory.objects.create(
                visit=visit,
                meeting_stage=visit.meeting_stage,
                meeting_type=visit.meeting_type,              # ✅ Added
                visit_image=visit.visit_image if visit.visit_image else None, # ✅ Added
                tag=visit.tag,
                item_discussed=visit.item_discussed,
                contract_outcome=visit.contract_outcome,
                is_payment_collected=visit.is_payment_collected,
                status=visit.status,
                client_budget=float(visit.client_budget) if visit.client_budget else 0,
                contact_person_name=visit.contact_person.contact_name if visit.contact_person else "",
                contact_number=visit.contact_number,
                designation=visit.designation,
                contract_amount=float(visit.contract_amount) if visit.contract_amount else 0,
                is_order_final=visit.is_order_final,
                products_snapshot=products_snapshot,
                updated_by=request.user
            )

            return redirect("visit_detail", visit_id=visit.id)

    else:
        visit_form = UpdateVisitForm(instance=visit, stage=stage)
        formset = ProductFormSet(
            queryset=visit.products.all(),
            form_kwargs={"stage": stage, "contract_outcome": contract_outcome},
            prefix="product"
        )

    # Attach previous payments to formset
    for pf in formset:
        payments = ProductPaymentHistory.objects.filter(product=pf.instance).order_by("id") if pf.instance.pk else []
        pf.previous_payments_json = json.dumps([
            {
                "date": p.created_at.strftime("%Y-%m-%d") if hasattr(p, "created_at") else "",
                "amount": float(p.amount_collected),
                "user": f"{getattr(p.collected_by, 'first_name', '')} {getattr(p.collected_by, 'last_name', '')}".strip()
            }
            for p in payments
        ])

    if visit.contact_person:
        visit_form.fields["contact_number"].initial = visit.contact_person.contact_detail or ""
        visit_form.fields["designation"].initial = visit.contact_person.customer.designation or ""

    saved_stage_index = [s[0] for s in NewVisit.MEETING_STAGE_CHOICES].index(visit.meeting_stage)

    return render(request, "users/update_visit.html", {
        "form": visit_form,
        "formset": formset,
        "visit": visit,
        "saved_stage_index": saved_stage_index
    })


# views.py
@login_required
def get_contact_details_update(request, contact_id):
    """
    Fetch contact details for update visit form dynamically.
    """
    try:
        contact = CustomerContact.objects.get(pk=contact_id)
        data = {
            "contact_number": contact.contact_detail or "",
            "designation": contact.customer.designation or "",
        }
        return JsonResponse(data)
    except CustomerContact.DoesNotExist:
        return JsonResponse({"contact_number": "", "designation": ""})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import NewVisit, VisitStageHistory

@login_required
def visit_history(request, visit_id):
    current_visit = get_object_or_404(NewVisit, id=visit_id)
    company = current_visit.company_name

    # ✅ Fetch all stage history snapshots for this visit
    stage_updates = current_visit.stage_history.all()  # thanks to related_name="stage_history"

    return render(request, "users/visit_history.html", {
        "current_visit": current_visit,
        "company": company,
        "stage_updates": stage_updates,  # send all updates with updated_at
    })



@login_required
def visits_history(request, visit_id):
    current_visit = get_object_or_404(NewVisit, id=visit_id)
    company = current_visit.company_name

    # ✅ Fetch all stage history snapshots for this visit
    stage_updates = current_visit.stage_history.all()  # thanks to related_name="stage_history"

    return render(request, "company/visit_history.html", {
        "current_visit": current_visit,
        "company": company,
        "stage_updates": stage_updates,  # send all updates with updated_at
    })




from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib import messages
from .models import NewVisit, ProductInterested
from .forms import ProductInterestedFormSet

@login_required
def add_product_to_visit(request, visit_id):
    visit = get_object_or_404(NewVisit, id=visit_id)

    # Formset for products related to this visit
    formset = ProductInterestedFormSet(queryset=visit.products.none())

    if request.method == "POST":
        formset = ProductInterestedFormSet(request.POST, queryset=visit.products.none())
        if formset.is_valid():
            added_products = []
            duplicate_products = []

            for form in formset:
                product_name = form.cleaned_data.get('product_interested')
                if product_name:
                    # Check if product already exists for this visit
                    if visit.products.filter(product_interested=product_name).exists() or product_name in added_products:
                        duplicate_products.append(product_name)
                    else:
                        product = form.save(commit=False)
                        product.visit = visit
                        product.save()
                        added_products.append(product_name)

            if duplicate_products:
                msg = f"The following product(s) already exist for this visit and were not added: {', '.join(duplicate_products)}"
                messages.warning(request, msg)

            # AJAX request: return JSON success
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "duplicates": duplicate_products})

            messages.success(request, "Products added successfully!")
            return redirect('update_visit', visit_id=visit.id)
        else:
            # AJAX request: return form HTML with errors
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                form_html = render_to_string(
                    'users/_product_form_modal.html',
                    {'formset': formset, 'visit': visit},
                    request=request
                )
                return JsonResponse({"success": False, "form_html": form_html})

    # GET request: render form HTML for AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form_html = render_to_string(
            'users/add_product_form_partial.html',
            {'formset': formset, 'visit': visit},
            request=request
        )
        return JsonResponse({"success": True, "form_html": form_html})

    # Normal page load
    return render(request, 'users/add_product_to_visit.html', {
        'visit': visit,
        'formset': formset
    })


from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import NewVisit, ProductInterested

@login_required
def delete_product_from_visit(request, visit_id, product_id):
    visit = get_object_or_404(NewVisit, id=visit_id)
    product = get_object_or_404(ProductInterested, id=product_id, visit=visit)

    if request.method == "POST":
        product.delete()

        # If request is AJAX → return JSON
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        # Normal (non-AJAX) delete → redirect as before
        messages.success(request, "Product deleted successfully.")
        return redirect('update_visit', visit_id=visit.id)

    # Fallback: normal confirmation page if user visits link directly
    return render(request, "users/confirm_delete_product.html", {
        "visit": visit,
        "product": product
    })



# views.py
from django.shortcuts import render, get_object_or_404
from .models import VisitStageHistory

def visit_stage_detail(request, update_id):
    # Fetch the stage update record
    stage_update = get_object_or_404(VisitStageHistory, id=update_id)
    
    return render(request, 'users/stage_detail.html', {'stage_update': stage_update})


def visit_stage_details(request, update_id):
    # Fetch the stage update record
    stage_update = get_object_or_404(VisitStageHistory, id=update_id)
    
    return render(request, 'company/stage_detail.html', {'stage_update': stage_update})

