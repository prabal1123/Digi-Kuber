from django.db import models
from app_login.models import CustomUser
from app_user.models import Profile

# models.py
from django.db import models
from django.contrib.auth.models import User

class Quote(models.Model):
    user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    customerRefNo = models.CharField(max_length=512, null=True, blank=True)
    sessionKey = models.CharField(max_length=40, null=True, blank=True)
    currencyPair = models.CharField(max_length=10)
    basePrice = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    quantity = models.DecimalField(max_digits=10, decimal_places=4, default=1.0000)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax1Perc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax2Perc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    tax3Perc = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    isValidated = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Quote #{self.id} - {self.sessionKey}"


class TradeBuy(models.Model):
    customerRefNo = models.CharField(max_length=512)
    transactionRefNo = models.CharField(max_length=512, null=True, blank=True)
    value = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    currencyPair = models.CharField(max_length=10)
    calculationType = models.CharField(max_length=1, default='A')
    preTaxAmount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    quantity = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    quoteId = models.CharField(max_length=512, null=True, blank=True)
    tax1Amt = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    tax2Amt = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    tax3Amt = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    billingAddressId = models.CharField(max_length=512, null=True, blank=True)
    transactionDate = models.DateTimeField(null=True, blank=True)
    transactionOrderID = models.CharField(max_length=512, null=True, blank=True)
    totalAmount = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)

    #quantity should be calculated field in this model based on value and preTaxAmount
    def save(self, *args, **kwargs):
        if self.calculationType == 'A' and self.preTaxAmount and self.preTaxAmount > 0:
            self.quantity = self.value / self.preTaxAmount
        elif self.calculationType == 'A' and self.preTaxAmount and self.preTaxAmount > 0:
            self.value = self.quantity * self.preTaxAmount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"TradeBuy created at {self.transactionRefNo} for Customer {self.customerRefNo}"
