// ===============================
// Hour-based charts (HOME PAGE)
// ===============================

const HOURS_RANGE = 8;
const REFRESH_INTERVAL = 10 * 60 * 1000; // 10 minutes

// -------------------------------
// GOLD CHART
// -------------------------------
const goldChart = new ApexCharts(
  document.querySelector("#goldChart"),
  {
    chart: {
      type: "line",
      height: 220,
      background: "transparent",
      toolbar: { show: false },
      animations: { enabled: true }
    },
    series: [
      {
        name: "Gold Price",
        data: []
      }
    ],
    stroke: {
      curve: "smooth",
      width: 2
    },
    colors: ["#f4c542"],
    xaxis: {
      type: "datetime",
      labels: {
        datetimeUTC: false,
        format: "HH:mm"
      }
    },
    yaxis: {
      labels: { show: false }
    },
    grid: { show: false },

    // ✅ CUSTOM GOLD TOOLTIP
    tooltip: {
      custom: function ({ series, seriesIndex, dataPointIndex, w }) {
        const price = series[seriesIndex][dataPointIndex];
        const time = new Date(
          w.globals.seriesX[seriesIndex][dataPointIndex]
        ).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit"
        });

        return `
          <div style="
            background:#0f0f0f;
            border:1px solid #f4c542;
            padding:10px 14px;
            border-radius:8px;
            color:#f4c542;
            font-weight:600;
            min-width:120px;
          ">
            <div style="color:#aaa; font-size:12px; margin-bottom:4px;">
              ${time}
            </div>
            <div style="font-size:16px;">
              ₹${price.toFixed(2)}
            </div>
          </div>
        `;
      }
    }
  }
);

goldChart.render();

// -------------------------------
// SILVER CHART
// -------------------------------
const silverChart = new ApexCharts(
  document.querySelector("#silverChart"),
  {
    chart: {
      type: "line",
      height: 220,
      background: "transparent",
      toolbar: { show: false },
      animations: { enabled: true }
    },
    series: [
      {
        name: "Silver Price",
        data: []
      }
    ],
    stroke: {
      curve: "smooth",
      width: 2
    },
    colors: ["#e9e8e3"],
    xaxis: {
      type: "datetime",
      labels: {
        datetimeUTC: false,
        format: "HH:mm"
      }
    },
    yaxis: {
      labels: { show: false }
    },
    grid: { show: false },

    // ✅ CUSTOM SILVER TOOLTIP
    tooltip: {
      custom: function ({ series, seriesIndex, dataPointIndex, w }) {
        const price = series[seriesIndex][dataPointIndex];
        const time = new Date(
          w.globals.seriesX[seriesIndex][dataPointIndex]
        ).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit"
        });

        return `
          <div style="
            background:#0f0f0f;
            border:1px solid #999;
            padding:10px 14px;
            border-radius:8px;
            color:#e9e8e3;
            font-weight:600;
            min-width:120px;
          ">
            <div style="color:#aaa; font-size:12px; margin-bottom:4px;">
              ${time}
            </div>
            <div style="font-size:16px;">
              ₹${price.toFixed(2)}
            </div>
          </div>
        `;
      }
    }
  }
);

silverChart.render();

// -------------------------------
// LOAD HOURLY DATA
// -------------------------------
function loadHourlyCharts() {
  fetch(`/app_shop/live-prices/?hours=${HOURS_RANGE}`)
    .then(r => r.json())
    .then(data => {

      if (data.gold) {
        goldChart.updateSeries([
          {
            data: data.gold.map(([ts, price]) => ({
              x: new Date(ts).getTime(),
              y: price
            }))
          }
        ]);
      }

      if (data.silver) {
        silverChart.updateSeries([
          {
            data: data.silver.map(([ts, price]) => ({
              x: new Date(ts).getTime(),
              y: price
            }))
          }
        ]);
      }
    })
    .catch(err => {
      console.error("Hourly chart error:", err);
    });
}

// Initial load
loadHourlyCharts();

// Refresh every 5 minutes
setInterval(loadHourlyCharts, REFRESH_INTERVAL);
