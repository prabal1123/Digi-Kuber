# create a form from model TradeBuy to edit and validate quote
from django import forms
from .models import TradeBuy

class TradeBuyForm(forms.ModelForm):
    class Meta:
        model = TradeBuy
        fields = ['value', 'quantity', 'preTaxAmount', 'tax1Amt', 'tax2Amt', 'tax3Amt', 'totalAmount']
        widgets = {
            'customerRefNo': forms.TextInput(attrs={'class': 'form-control'}),
            'transactionRefNo': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control'}),
            'currencyPair': forms.Select(attrs={'class': 'form-control'}),
            'calculationType': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'value': 'Amount',
            'quantity': 'Quantity',
            'preTaxAmount': 'Pre-Tax Amount',
            'tax1Amt': 'Tax 1 Amount',
            'tax2Amt': 'Tax 2 Amount',
            'tax3Amt': 'Tax 3 Amount',
            'totalAmount': 'Total Amount',
        }
    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return value
    def clean_customerRefNo(self):
        customerRefNo = self.cleaned_data.get('customerRefNo')
        if not customerRefNo:
            raise forms.ValidationError("Customer Reference Number is required.")
        return customerRefNo
    def clean_transactionRefNo(self):
        transactionRefNo = self.cleaned_data.get('transactionRefNo')
        if not transactionRefNo:
            raise forms.ValidationError("Transaction Reference Number is required.")
        return transactionRefNo
    def clean_currencyPair(self):
        currencyPair = self.cleaned_data.get('currencyPair')
        if not currencyPair:
            raise forms.ValidationError("Currency Pair is required.")
        return currencyPair
    def clean_calculationType(self):
        calculationType = self.cleaned_data.get('calculationType')
        if not calculationType:
            raise forms.ValidationError("Calculation Type is required.")
        return calculationType
    def clean(self):
            cleaned_data = super().clean()
            return cleaned_data
def save(self, commit=True):
    instance = super().save(commit=False)
    if commit:
        instance.save()
    return instance