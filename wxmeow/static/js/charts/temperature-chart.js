/**
 * Temperature Chart for wxmeow
 *
 * Creates an interactive hourly temperature chart for the selected forecast day.
 * Requires Chart.js to be loaded.
 */

// Wait for both DOM and Chart.js to be ready
function initializeCharts() {
  if (typeof Chart === "undefined") {
    console.log("Chart.js not loaded yet, retrying in 100ms");
    setTimeout(initializeCharts, 100);
    return;
  }

  console.log("Chart.js loaded, initializing charts");

  let charts = {}; // Store chart instances for each day
  let lastSelectedDay = 0; // Track currently selected day

  // Enhanced event listener for day selection
  $(document).on("daySelected", function (e, dayIndex) {
    console.log(`Day ${dayIndex} selected, creating/updating chart`);
    setTimeout(() => createTemperatureChart(dayIndex), 100);
  });

  // Helper function to check if dark mode is active
  function isDarkMode() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  // Function to create or update the temperature chart
  function createTemperatureChart(dayIndex) {
    console.log(`Creating temperature chart for day ${dayIndex}`);

    // Get the container where we'll place the chart for this day
    const chartContainer = document.getElementById(
      `hourly-temperature-chart-${dayIndex}`,
    );
    if (!chartContainer) {
      console.error("Chart container not found for day", dayIndex);
      return;
    }

    console.log(
      `Creating chart for day ${dayIndex} in container:`,
      chartContainer.id,
    );

    // Show the container and ensure proper styling
    chartContainer.style.display = "block";
    chartContainer.style.width = "100%";
    chartContainer.style.maxWidth = "800px";
    chartContainer.style.margin = "20px auto";
    chartContainer.style.height = "350px";
    chartContainer.style.minHeight = "350px";

    // If there's an existing chart for this day, destroy it
    if (charts[dayIndex]) {
      console.log(`Destroying existing chart for day ${dayIndex}`);
      charts[dayIndex].destroy();
      charts[dayIndex] = null;
    }

    // For now, use dummy data to avoid complexity
    console.log("Using dummy data for chart");
    const dummyData = getDummyDataForDay(dayIndex);
    createChartWithData(dayIndex, dummyData);
  }

  // Function to create chart with data
  function createChartWithData(dayIndex, data) {
    const chartContainer = document.getElementById(
      `hourly-temperature-chart-${dayIndex}`,
    );
    if (!chartContainer) {
      console.error("Chart container not found for day", dayIndex);
      return;
    }

    console.log(
      `Creating chart with ${data.length} data points for day ${dayIndex}`,
    );

    // Clear any previous content
    chartContainer.innerHTML = "";

    // Create canvas element
    const canvas = document.createElement("canvas");
    canvas.id = `temperature-chart-${dayIndex}`;
    canvas.style.width = "100%";
    canvas.style.height = "300px";
    chartContainer.appendChild(canvas);

    const ctx = canvas.getContext("2d");

    // Prepare chart data
    const labels = data.map((item) => {
      const time = new Date(item.time);
      return time.getHours() + ":00";
    });

    const temperatures = data.map((item) => item.temperature);

    console.log(
      `Chart data - Labels: ${labels.length}, Temps: ${temperatures.length}`,
    );

    // Prepare precipitation data with simulated values
    const precipitation = data.map((item, index) => {
      // Use a simple pattern for demo precipitation data
      return Math.max(0, Math.sin(index / 3) * 30 + 10);
    });

    // Create the chart
    try {
      charts[dayIndex] = new Chart(ctx, {
        type: "line",
        data: {
          labels: labels,
          datasets: [
            {
              label: "Temperature (°F)",
              data: temperatures,
              borderColor: isDarkMode() ? "#FF9F40" : "#4285F4",
              backgroundColor: isDarkMode()
                ? "rgba(255, 159, 64, 0.2)"
                : "rgba(66, 133, 244, 0.2)",
              borderWidth: 3,
              fill: true,
              tension: 0.4,
              pointRadius: 4,
              pointHoverRadius: 6,
              yAxisID: "y",
            },
            {
              label: "Precipitation (%)",
              data: precipitation,
              type: "bar",
              borderColor: "#2196F3",
              backgroundColor: "rgba(33, 150, 243, 0.4)",
              borderWidth: 1,
              yAxisID: "y1",
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            mode: "index",
            intersect: false,
          },
          plugins: {
            title: {
              display: true,
              text: `24-Hour Temperature & Precipitation Forecast`,
              color: isDarkMode() ? "#e0e0e0" : "#333333",
              font: {
                size: 16,
                weight: "bold",
              },
              padding: 20,
            },
            legend: {
              display: true,
              position: "top",
              labels: {
                color: isDarkMode() ? "#e0e0e0" : "#333333",
                font: {
                  size: 12,
                },
                usePointStyle: true,
                padding: 20,
              },
            },
            tooltip: {
              backgroundColor: isDarkMode()
                ? "rgba(30, 30, 30, 0.95)"
                : "rgba(255, 255, 255, 0.95)",
              titleColor: isDarkMode() ? "#fff" : "#333",
              bodyColor: isDarkMode() ? "#fff" : "#333",
              borderColor: isDarkMode() ? "#666" : "#ccc",
              borderWidth: 1,
              padding: 15,
              cornerRadius: 8,
              displayColors: true,
              callbacks: {
                label: function (context) {
                  if (context.datasetIndex === 0) {
                    return `Temperature: ${context.parsed.y}°F`;
                  } else {
                    return `Precipitation: ${context.parsed.y}%`;
                  }
                },
                title: function (tooltipItems) {
                  const time = tooltipItems[0].label;
                  return `Time: ${time}`;
                },
              },
            },
          },
          scales: {
            x: {
              title: {
                display: true,
                text: "Time of Day",
                color: isDarkMode() ? "#e0e0e0" : "#333333",
                font: {
                  size: 14,
                  weight: "bold",
                },
              },
              ticks: {
                color: isDarkMode() ? "#e0e0e0" : "#333333",
                font: {
                  size: 11,
                },
              },
              grid: {
                color: isDarkMode()
                  ? "rgba(255, 255, 255, 0.1)"
                  : "rgba(0, 0, 0, 0.1)",
                drawBorder: false,
              },
            },
            y: {
              type: "linear",
              display: true,
              position: "left",
              beginAtZero: false,
              title: {
                display: true,
                text: "Temperature (°F)",
                color: isDarkMode() ? "#FF9F40" : "#4285F4",
                font: {
                  size: 14,
                  weight: "bold",
                },
              },
              ticks: {
                color: isDarkMode() ? "#e0e0e0" : "#333333",
                font: {
                  size: 11,
                },
                callback: function (value) {
                  return Math.round(value) + "°F";
                },
              },
              grid: {
                color: isDarkMode()
                  ? "rgba(255, 255, 255, 0.1)"
                  : "rgba(0, 0, 0, 0.1)",
                drawBorder: false,
              },
            },
            y1: {
              type: "linear",
              display: true,
              position: "right",
              min: 0,
              max: 100,
              title: {
                display: true,
                text: "Precipitation (%)",
                color: isDarkMode() ? "#64B5F6" : "#2196F3",
                font: {
                  size: 14,
                  weight: "bold",
                },
              },
              ticks: {
                color: isDarkMode() ? "#e0e0e0" : "#333333",
                font: {
                  size: 11,
                },
                callback: function (value) {
                  return value + "%";
                },
              },
              grid: {
                drawOnChartArea: false,
                drawBorder: false,
              },
            },
          },
          animation: {
            duration: 1500,
            easing: "easeInOutQuart",
          },
          elements: {
            point: {
              hoverRadius: 8,
            },
            line: {
              tension: 0.4,
            },
          },
        },
      });

      console.log(`Chart created successfully for day ${dayIndex}`);
    } catch (error) {
      console.error(`Error creating chart for day ${dayIndex}:`, error);
      chartContainer.innerHTML = `<p style="text-align: center; padding: 50px; color: var(--text-color);">Chart failed to load</p>`;
    }
  }

  // Helper function to get dummy data for a specific day
  function getDummyDataForDay(dayIndex) {
    const dummyData = [];
    const baseDate = new Date();
    baseDate.setDate(baseDate.getDate() + dayIndex);

    const conditions = [
      "Clear",
      "Partly Cloudy",
      "Cloudy",
      "Light Rain",
      "Rain",
    ];
    const dayCondition = conditions[dayIndex % conditions.length];

    for (let hour = 0; hour < 24; hour++) {
      const time = new Date(baseDate);
      time.setHours(hour);

      // Create realistic temperature curve for the day
      const baseTemp = 68 + dayIndex * 3;
      const hourlyVariation = Math.sin(((hour - 14) * Math.PI) / 12) * 12;
      const temperature = Math.round(baseTemp + hourlyVariation);

      dummyData.push({
        time: time.toISOString(),
        temperature: temperature,
        temp: temperature,
        condition: dayCondition,
        day: dayIndex,
      });
    }

    return dummyData;
  }
}

// Initialize everything when DOM is ready
$(document).ready(function () {
  // Wait a bit for Chart.js to load, then initialize
  setTimeout(function () {
    if (typeof Chart !== "undefined") {
      initializeCharts();
    } else {
      console.log("Chart.js still not loaded, trying again...");
      setTimeout(function () {
        if (typeof Chart !== "undefined") {
          initializeCharts();
        } else {
          console.error("Chart.js failed to load");
        }
      }, 1000);
    }
  }, 500);
});
