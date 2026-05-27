
# app_user/views.py
from django.shortcuts import render, redirect
from django.conf import settings
from .forms import ProfileForm
from .models import Profile
from app_shop.utils import make_post


def edit_profile_view(request):
    user = request.user

    # Always ensure profile exists (SAFE)
    profile, _ = Profile.objects.get_or_create(user=user)

    editing = request.GET.get("edit", "false") == "true"
    success = request.GET.get("success", "false") == "true"

    # =============================
    # POST: Save profile
    # =============================
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile, user=user)

        if form.is_valid():
            entered_phone = form.cleaned_data.get("phone")
            # 🔥 SAVE PHONE TO CustomUser (NOT Profile)
            if entered_phone and not user.phone:
                user.phone = entered_phone
                user.save(update_fields=["phone"])

            # -------------------------
            # Build billing address
            # -------------------------
            billingAddress = {
                "line1": form.cleaned_data.get("bLine1"),
                "line2": form.cleaned_data.get("bLine2"),
                "city": form.cleaned_data.get("bCity"),
                "state": form.cleaned_data.get("bState"),
                "zip": int(form.cleaned_data.get("bZip") or 0) if str(form.cleaned_data.get("bZip", "") or "").isdigit() else 0,
                "country": "India",
                "mobileNumber": user.phone,  # ✅ real user phone
                "statecode": "07",
            }

            # -------------------------
            # Build delivery address
            # -------------------------
            deliveryAddress = {
                "line1": form.cleaned_data.get("dLine1"),
                "line2": form.cleaned_data.get("dLine2"),
                "city": form.cleaned_data.get("dCity"),
                "state": form.cleaned_data.get("dState"),
                "zip": int(form.cleaned_data.get("dZip") or 0) if str(form.cleaned_data.get("dZip", "") or "").isdigit() else 0,
                "country": "India",
                "mobileNumber": user.phone,
                "statecode": "07",
            }

            profile = form.save(commit=False)
            profile.user = user

            # -------------------------
            # Same-as-delivery logic
            # -------------------------
            if form.cleaned_data.get("same_as_delivery"):
                profile.billingAddress = billingAddress
                profile.deliveryAddress = billingAddress
            else:
                profile.billingAddress = billingAddress
                profile.deliveryAddress = deliveryAddress

            # -------------------------
            # Partner-side IDs (REQUIRED)
            # -------------------------
            if not profile.billingAddressId:
                profile.billingAddressId = f"{profile.customerRefNo}_BILL"

            profile.save()

            # =============================
            # MMTC createProfile (RUN ONCE)
            # =============================
            if not profile.dgcustomerRefNo:
                session_id = request.session.get("mmtc_session_id")

                # Safe guard for local/testing
                if session_id:
                    payload = {
                        "mobileNumber": user.phone,
                        "customerRefNo": profile.customerRefNo,
                        "fullName": profile.name,
                        "kycStatus": "Y" if profile.kycStatus else "I",
                        "partner_id": settings.MMTC_PARTNER_ID,
                        "emailAddress": user.email,
                        "dob": profile.dob.strftime("%Y-%m-%d") if profile.dob else None,
                        "billingAddress": profile.billingAddress,
                        "deliveryAddress": profile.deliveryAddress,
                    }

                    resp = make_post(
                        endpoint="CUSTOMER_CREATE_PROFILE",
                        payload=payload,
                        token=session_id,
                    )

                    if resp.get("status") == 200:
                        dg_ref = resp.get("data", {}).get("dgCustomerRefNo")
                        if dg_ref:
                            profile.dgcustomerRefNo = dg_ref
                            profile.save(update_fields=["dgcustomerRefNo"])

            return redirect("/app_user/edit-profile/?success=true")

    # =============================
    # GET: Load profile for editing
    # =============================
    initial = {}

    if profile.billingAddress:
        initial.update({
            "bLine1": profile.billingAddress.get("line1"),
            "bLine2": profile.billingAddress.get("line2"),
            "bCity": profile.billingAddress.get("city"),
            "bState": profile.billingAddress.get("state"),
            "bZip": profile.billingAddress.get("zip"),
        })

    if profile.deliveryAddress:
        initial.update({
            "dLine1": profile.deliveryAddress.get("line1"),
            "dLine2": profile.deliveryAddress.get("line2"),
            "dCity": profile.deliveryAddress.get("city"),
            "dState": profile.deliveryAddress.get("state"),
            "dZip": profile.deliveryAddress.get("zip"),
        })

    form = ProfileForm(instance=profile, user=user, initial=initial)

    # =============================
    # Render
    # =============================
    if editing:
        return render(request, "app_user/profile.html", {
            "form": form,
            "editing": True,
        })

    return render(request, "app_user/profile.html", {
        "profile": profile,
        "editing": False,
        "success": success,
    })
