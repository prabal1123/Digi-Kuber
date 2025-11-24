from django.db import models
from app_login.models import CustomUser
from app_user.models import Profile

# models.py
from django.db import models
from django.contrib.auth.models import User

class Quote(models.Model):
    # user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    customerRefNo = models.CharField(max_length=512, null=True, blank=True, default="DummyRefNo")
    calculationType = models.CharField(max_length=1, default='A', null=True, blank=True)  # 'A' for Amount, 'Q' for Quantity
    unitPriceAmt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    preTaxAmt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    taxAmount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    quantity = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    totalAmt = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax1Perc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax2Perc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax3Perc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax1Amt = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax2Amt = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax3Amt = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    transactionOrderID = models.CharField(max_length=512, null=True, blank=True, default="DefaultOrderID")
    isValidated = models.BooleanField(default=False)
    quoteId = models.CharField(max_length=512, null=True, blank=True, default="DefaultQuoteID")
    currencyPair = models.CharField(max_length=10, default="INR")
    taxType = models.CharField(max_length=50, null=True, blank=True)
    transactionType = models.CharField(max_length=10, default="BUY")
    createdAt = models.DateTimeField(default=None, null=True, blank=True) #from API
    transactionDate = models.DateTimeField(auto_now_add=True, null=True, blank=True) #when saved to DB

    def __str__(self):
        return f"Quote #{self.id} - {self.quantity}"
