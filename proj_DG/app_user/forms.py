from django import forms
from .models import Profile

class ProfileForm(forms.ModelForm):
    email = forms.EmailField(disabled=True, required=False)
    phone = forms.CharField(disabled=True, required=False)
    bLine1 = forms.CharField(label='Billing Address Line 1', required=False)
    bLine2 = forms.CharField(label='Billing Address Line 2', required=False)
    bCity = forms.CharField(label='Billing City', required=False)
    bState = forms.CharField(label='Billing State', required=False)
    bZip = forms.CharField(label='Billing Zip', required=False)
    dLine1 = forms.CharField(label='Delivery Address Line 1', required=False)
    dLine2 = forms.CharField(label='Delivery Address Line 2', required=False)
    dCity = forms.CharField(label='Delivery City', required=False)
    dState = forms.CharField(label='Delivery State', required=False)
    dZip = forms.CharField(label='Delivery Zip', required=False)


    class Meta:
        model = Profile
        fields = [
            'name',
            # 'billingAddress',
            # 'deliveryAddress',
            'same_as_delivery',
            'kycStatus',
            'nameProofType',
            'addressProofType',
            'nameProofId',
            'addressProofId',
            'dob',
            'email',
            'phone'
        ]



    # def __init__(self, *args, **kwargs):
    #     user = kwargs.pop('user', None)
    #     super().__init__(*args, **kwargs)

    #     if user:
    #         # always show email
    #         self.fields['email'].initial = user.email

    #         if user.phone:
    #             # 🔒 phone already verified → lock it
    #             self.fields['phone'].initial = user.phone
    #             self.fields['phone'].disabled = True
    #             self.fields['phone'].required = False
    #         else:
    #             # 🔓 email signup → phone required
    #             self.fields['phone'].disabled = False
    #             self.fields['phone'].required = True


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['email'].initial = user.email

            if user.phone:
                self.fields['phone'].initial = user.phone
                self.fields['phone'].disabled = True
                self.fields['phone'].required = False
            else:
                self.fields['phone'].disabled = False
                self.fields['phone'].required = True

    def clean_bZip(self):
        zip_val = self.cleaned_data.get('bZip', '').strip()
        if zip_val:
            if not zip_val.isdigit():
                raise forms.ValidationError("Billing zip must be numeric.")
            if not (100000 <= int(zip_val) <= 999999):
                raise forms.ValidationError("Billing zip must be a valid 6-digit Indian pincode.")
        return zip_val

    def clean_dZip(self):
        zip_val = self.cleaned_data.get('dZip', '').strip()
        if zip_val:
            if not zip_val.isdigit():
                raise forms.ValidationError("Delivery zip must be numeric.")
            if not (100000 <= int(zip_val) <= 999999):
                raise forms.ValidationError("Delivery zip must be a valid 6-digit Indian pincode.")
        return zip_val