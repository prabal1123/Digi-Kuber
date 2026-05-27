// ===============================
// Live price updater (HOME PAGE)
// ===============================

function updateHomePrices() {
  fetch("/app_shop/live-prices/")
    .then(response => response.json())
    .then(data => {

      // HERO GOLD
      const goldEl = document.getElementById("gold-price");
      if (goldEl && data.gold) {
        goldEl.innerText = `₹${data.gold}/g`;
      }

      // HERO SILVER
      const silverEl = document.getElementById("silver-price");
      if (silverEl && data.silver) {
        silverEl.innerText = `₹${data.silver}/g`;
      }

      // CHART GOLD
      const goldChartEl = document.getElementById("gold-chart-price");
      if (goldChartEl && data.gold) {
        goldChartEl.innerText = `₹${data.gold}/g`;
      }

      // CHART SILVER
      const silverChartEl = document.getElementById("silver-chart-price");
      if (silverChartEl && data.silver) {
        silverChartEl.innerText = `₹${data.silver}/g`;
      }

    })
    .catch(err => {
      console.error("Price fetch error:", err);
    });
}

// Initial load
updateHomePrices();

// Update every 5 seconds (unchanged)
// setInterval(updateHomePrices, 5000);
setInterval(updateHomePrices, 2 * 60 * 1000);
