// Initially disable inputs
function disableInputs() {
    document.getElementById('quantity').disabled = true;
    document.getElementById('today-price').disabled = true;
    document.getElementById('pre-tax-amount').disabled = true;
    document.getElementById('tax1-amt').disabled = true;
    document.getElementById('tax2-amt').disabled = true;
    document.getElementById('total-tax-amt').disabled = true;
    document.getElementById('total-amt').disabled = true;
}

function enableInputs() {
    document.getElementById('quantity').disabled = false;
    document.getElementById('pre-tax-amount').disabled = false;
    document.getElementById('edit-quote').hidden = true;
}

document.addEventListener('DOMContentLoaded', function () {
    const quoteDiv = document.getElementById('quote-data');

    const tax1Perc = parseFloat(quoteDiv.dataset.tax1Perc);
    const tax2Perc = parseFloat(quoteDiv.dataset.tax2Perc);
    const unitPrice = parseFloat(quoteDiv.dataset.unitPrice);

    const quantityInput = document.getElementById('quantity');
    const preTaxInput = document.getElementById('pre-tax-amount');

    const tax1AmtInput = document.getElementById('tax1-amt');
    const tax2AmtInput = document.getElementById('tax2-amt');
    const totalTaxInput = document.getElementById('total-tax-amt');
    const totalAmountInput = document.getElementById('total-amt');

    function recalculateFromQuantity() {
        let quantity = parseFloat(quantityInput.value);
        if (isNaN(quantity) || quantity <= 0) return;
        console.log(unitPrice);
        let preTaxAmount = quantity * unitPrice;
        updateAll(preTaxAmount, quantity);
    }

    function recalculateFromPreTax() {
        let preTaxAmount = parseFloat(preTaxInput.value);
        if (isNaN(preTaxAmount) || unitPrice === 0) return;

        let quantity = preTaxAmount / unitPrice;

        updateAll(preTaxAmount, quantity);
    }

    function updateAll(preTaxAmount, quantity) {
        if (isNaN(preTaxAmount) || isNaN(quantity)) return;

        const tax1Amt = (preTaxAmount * tax1Perc) / 100;
        const tax2Amt = (preTaxAmount * tax2Perc) / 100;
        const totalTaxAmt = tax1Amt + tax2Amt;
        const totalAmount = preTaxAmount + totalTaxAmt;

        // Only update if all values are valid
        if (
            !isNaN(tax1Amt) && !isNaN(tax2Amt) &&
            !isNaN(totalTaxAmt) && !isNaN(totalAmount)
        ) {
            quantityInput.value = quantity.toFixed(4);
            preTaxInput.value = preTaxAmount.toFixed(2);
            tax1AmtInput.value = tax1Amt.toFixed(2);
            tax2AmtInput.value = tax2Amt.toFixed(2);
            totalTaxInput.value = totalTaxAmt.toFixed(2);
            totalAmountInput.value = totalAmount.toFixed(2);
        }
    }


    // Event listeners
    quantityInput.addEventListener('input', recalculateFromQuantity);
    preTaxInput.addEventListener('input', recalculateFromPreTax);

    // Edit button
    document.getElementById('edit-quote').addEventListener('click', function (e) {
        e.preventDefault();  // prevent the default link action
        enableInputs();
        document.getElementById('validate-quote').style.display = 'inline-block';
        // document.getElementById('edit-quote').style.display = 'dissabled';
    });

    // Initial state
    disableInputs();
});