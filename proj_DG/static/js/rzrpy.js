async function startPayment() {
    const response = await fetch('/create-order/');
    const data = await response.json();

    if (data.error) {
        alert('Failed to create order');
        return;
    }

    const options = {
        key: "rzp_test_RHqAo3jvKfEYnW",
        amount: data.amount,         // ✔ use amount as returned (already in paise)
        currency: data.currency,
        name: "DigiGold",
        description: "Test Transaction",
        order_id: data.id,           // ✔ Correct: Razorpay returns "id"
        handler: function (response) {
            alert("Payment successful! Payment ID: " + response.razorpay_payment_id);
        },
        prefill: {
            name: "John Doe",
            email: "john@example.com",
            contact: "9876543210"
        },
        theme: {
            color: "#3399cc"
        }
    };

    const rzp = new Razorpay(options);
    rzp.open();
}
