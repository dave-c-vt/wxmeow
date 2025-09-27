/**
 * Temperature Chart for wxmeow
 *
 * Creates static hourly temperature charts for all forecast days.
 * Charts are pre-loaded on page load and shown/hidden based on day selection.
 */

document.addEventListener("DOMContentLoaded", function () {
  let charts = {}; // Store chart instances for each day
  let hourlyData = null; // Store the hourly forecast data
  let cachedData = {}; // Cache for hourly data by location

  console.log("Temperature chart module initializing...");

  // Helper function to check if dark mode is active
  function isDarkMode() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  // Helper function to get accessible colors
  function getAccessibleColors() {
    if (isDarkMode()) {
      return {
        primary: "rgba(255, 159, 64, 1)",
        primaryFaded: "rgba(255, 159, 64, 0.7)",
        primaryLight: "rgba(255, 159, 64, 0.3)",
        primaryVeryLight: "rgba(255, 159, 64, 0.1)",
        text: "#e0e0e0",
        gridColor: "#888888",
        tickColor: "#cccccc",
      };
    } else {
      return {
        primary: "rgba(21, 101, 192, 1)",
        primaryFaded: "rgba(21, 101, 192, 0.8)",
        primaryLight: "rgba(21, 101, 192, 0.4)",
        primaryVeryLight: "rgba(21, 101, 192, 0.15)",
        text: "#1a1a1a",
        gridColor: "#666666",
        tickColor: "#333333",
      };
    }
  }

  // Get the date for a specific day index
  function getSelectedDate(dayIndex) {
    const today = new Date();
    if (dayIndex === 0) {
      return today;
    }
    const date = new Date(today);
    date.setDate(today.getDate() + parseInt(dayIndex));
    return date;
  }

  // Filter hourly data by date
  function filterHourlyDataByDate(hourlyData, targetDate) {
    if (!hourlyData || !Array.isArray(hourlyData) || hourlyData.length === 0) {
      return [];
    }

    const targetDateStr = targetDate.toISOString().split("T")[0];

    return hourlyData.filter((item) => {
      try {
        if (!item.time) return false;
        const itemDate = new Date(item.time);
        if (isNaN(itemDate.getTime())) return false;
        const itemDateStr = itemDate.toISOString().split("T")[0];
        return itemDateStr === targetDateStr;
      } catch (e) {
        return false;
      }
    });
  }

  // Format time for display
  function formatTime(timeString) {
    try {
      const date = new Date(timeString);
      if (isNaN(date.getTime())) return timeString;
      return date.toLocaleTimeString([], { hour: "numeric", hour12: true });
    } catch (e) {
      return timeString;
    }
  }

  // Show a message in a chart container
  function showChartMessage(dayIndex, message) {
    const chartContainer = document.getElementById(
      `hourly-temperature-chart-${dayIndex}`,
    );
    if (chartContainer) {
      chartContainer.innerHTML = `<div class="chart-message" role="status" aria-live="polite"><p>${message}</p></div>`;
    }
  }

  // Create a temperature chart for a specific day
  function createTemperatureChart(dayIndex) {
    console.log(`Creating chart for day ${dayIndex}`);

    const chartContainer = document.getElementById(
      `hourly-temperature-chart-${dayIndex}`,
    );
    if (!chartContainer) {
      console.error(`Chart container not found for day ${dayIndex}`);
      return;
    }

    // If chart already exists, don't recreate it
    if (charts[dayIndex]) {
      console.log(`Chart for day ${dayIndex} already exists`);
      return;
    }

    // Check if we have hourly data
    if (!hourlyData || !Array.isArray(hourlyData) || hourlyData.length === 0) {
      console.warn(`No hourly data available for day ${dayIndex}`);
      showChartMessage(dayIndex, "No hourly forecast data available");
      return;
    }

    // Get the date for this day
    const selectedDate = getSelectedDate(dayIndex);
    const filteredData = filterHourlyDataByDate(hourlyData, selectedDate);

    // If no data for this day, create dummy data
    if (filteredData.length === 0) {
      console.log(`No data for day ${dayIndex}, creating dummy data`);
      const baseTemp = 65 + dayIndex * 3;
      for (let hour = 0; hour < 24; hour++) {
        const time = new Date(selectedDate);
        time.setHours(hour);
        const hourlyVariation = Math.sin(((hour - 14) * Math.PI) / 12) * 12;
        const temperature = Math.round(baseTemp + hourlyVariation);

        filteredData.push({
          time: time.toISOString(),
          temperature: temperature,
          temp: temperature,
          condition: "Forecast Unavailable",
        });
      }
    }

    // Prepare chart data
    const labels = filteredData.map((item) => formatTime(item.time));
    const temperatures = filteredData.map((item) => {
      let temp = parseFloat(item.temperature || item.temp);
      return isNaN(temp) ? 70 : temp;
    });

    // Clear container and create canvas
    chartContainer.innerHTML = "";
    const canvas = document.createElement("canvas");
    canvas.id = `temperature-chart-${dayIndex}`;
    canvas.classList.add("temperature-chart");
    canvas.style.width = "100%";
    canvas.style.height = "300px";
    canvas.style.display = "block";

    // Add accessibility attributes
    canvas.setAttribute("role", "img");
    canvas.setAttribute(
      "aria-label",
      `Temperature chart for ${selectedDate.toLocaleDateString()}, showing hourly temperatures from ${Math.min(...temperatures)}°F to ${Math.max(...temperatures)}°F`,
    );

    chartContainer.appendChild(canvas);

    // Get accessible colors
    const colors = getAccessibleColors();

    // Create gradient
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, colors.primaryFaded);
    gradient.addColorStop(0.5, colors.primaryLight);
    gradient.addColorStop(1, colors.primaryVeryLight);

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
              backgroundColor: gradient,
              borderColor: colors.primary,
              borderWidth: 3,
              pointBackgroundColor: colors.primary,
              pointBorderColor: isDarkMode() ? "#333" : "#fff",
              pointBorderWidth: 2,
              pointRadius: 5,
              pointHoverRadius: 8,
              pointHoverBorderWidth: 3,
              tension: 0.4,
              fill: true,
              spanGaps: true,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: {
            intersect: false,
            mode: "index",
          },
          layout: {
            padding: {
              left: 15,
              right: 25,
              top: 15,
              bottom: 15,
            },
          },
          animation: {
            duration: 800,
            easing: "easeOutQuart",
          },
          plugins: {
            legend: {
              display: false,
            },
            tooltip: {
              backgroundColor: isDarkMode()
                ? "rgba(30, 30, 30, 0.95)"
                : "rgba(255, 255, 255, 0.95)",
              titleColor: colors.text,
              bodyColor: colors.text,
              borderColor: colors.gridColor,
              borderWidth: 1,
              padding: 12,
              cornerRadius: 6,
              displayColors: false,
              callbacks: {
                title: function (tooltipItems) {
                  return `Time: ${tooltipItems[0].label}`;
                },
                label: function (context) {
                  return `Temperature: ${context.parsed.y}°F`;
                },
              },
            },
          },
          scales: {
            x: {
              display: true,
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
              },
              ticks: {
                color: colors.tickColor,
                font: {
                  size: 12,
                  weight: "bold",
                },
                maxTicksLimit: 8,
              },
              title: {
                display: true,
                text: "Time of Day",
                color: colors.text,
                font: {
                  size: 13,
                  weight: "bold",
                },
              },
            },
            y: {
              display: true,
              grid: {
                color: colors.gridColor,
                lineWidth: 1,
              },
              ticks: {
                color: colors.tickColor,
                font: {
                  size: 12,
                  weight: "bold",
                },
                callback: function (value) {
                  return value + "°F";
                },
              },
              title: {
                display: true,
                text: "Temperature (°F)",
                color: colors.text,
                font: {
                  size: 13,
                  weight: "bold",
                },
              },
            },
          },
        },
      });

      console.log(`Successfully created chart for day ${dayIndex}`);
    } catch (error) {
      console.error(`Error creating chart for day ${dayIndex}:`, error);
      showChartMessage(dayIndex, "Chart failed to load");
    }
  }

  // Get current location from page data
  function getCurrentLocation() {
    const bodyElement = document.body;
    if (bodyElement && bodyElement.getAttribute("data-location")) {
      return bodyElement.getAttribute("data-location");
    }

    const pathParts = window.location.pathname.split("/");
    if (pathParts.length > 2 && pathParts[1] === "wx") {
      return decodeURIComponent(pathParts[2]);
    }
    return null;
  }

  // Fetch hourly data from API
  function fetchHourlyData() {
    const location = getCurrentLocation();
    if (!location) {
      console.error("No location found for hourly data");
      return Promise.reject("No location specified");
    }

    // Check cache first
    if (cachedData[location]) {
      console.log(`Using cached hourly data for ${location}`);
      hourlyData = cachedData[location];
      return Promise.resolve(hourlyData);
    }

    console.log(`Fetching hourly data from API for ${location}`);
    return fetch(`/api/weather/${encodeURIComponent(location)}`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Weather API error: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        console.log("API response received:", data);

        if (
          data &&
          data.hourly_forecast &&
          Array.isArray(data.hourly_forecast) &&
          data.hourly_forecast.length > 0
        ) {
          hourlyData = data.hourly_forecast;
          cachedData[location] = hourlyData;
          console.log(
            `Loaded ${hourlyData.length} hourly data points for ${location}`,
          );
          return hourlyData;
        } else {
          console.warn("No valid hourly forecast data in API response");
          // Create dummy data as fallback
          hourlyData = createDummyData();
          return hourlyData;
        }
      })
      .catch((error) => {
        console.error("Error fetching hourly data:", error);
        // Create dummy data as fallback
        hourlyData = createDummyData();
        return hourlyData;
      });
  }

  // Create dummy data for demonstration
  function createDummyData() {
    console.log("Creating dummy hourly data");
    const dummyData = [];
    const now = new Date();

    for (let day = 0; day < 5; day++) {
      for (let hour = 0; hour < 24; hour++) {
        const time = new Date(now);
        time.setDate(now.getDate() + day);
        time.setHours(hour);

        const baseTemp = 65 + day * 2;
        const hourlyVariation = Math.sin(((hour - 14) * Math.PI) / 12) * 10;
        const randomVariation = (Math.random() - 0.5) * 4;
        const temperature = Math.round(
          baseTemp + hourlyVariation + randomVariation,
        );

        dummyData.push({
          time: time.toISOString(),
          temperature: temperature,
          temp: temperature,
          condition: "Generated forecast",
        });
      }
    }

    return dummyData;
  }

  // Create all charts at once
  function createAllCharts() {
    console.log("Creating all temperature charts...");

    // Create charts for all 5 days
    for (let i = 0; i < 5; i++) {
      createTemperatureChart(i);
    }

    console.log("All temperature charts created");

    // Hide all charts except day 0 initially
    showChartForDay(0);
  }

  // Show chart for specific day (hide others)
  function showChartForDay(dayIndex) {
    console.log(`Showing chart for day ${dayIndex}`);

    // Hide all chart containers
    for (let i = 0; i < 5; i++) {
      const container = document.getElementById(
        `hourly-temperature-chart-${i}`,
      );
      if (container) {
        container.style.display = i === parseInt(dayIndex) ? "block" : "none";
        container.setAttribute(
          "aria-hidden",
          i === parseInt(dayIndex) ? "false" : "true",
        );
      }
    }
  }

  // Event listener for day selection
  $(document).on("daySelected", function (event, dayIndex) {
    console.log(`Day ${dayIndex} selected, showing corresponding chart`);
    showChartForDay(parseInt(dayIndex));
  });

  // Handle theme changes
  function handleThemeChange() {
    console.log("Theme changed, updating all charts...");

    // Destroy existing charts
    Object.keys(charts).forEach((dayIndex) => {
      if (charts[dayIndex]) {
        charts[dayIndex].destroy();
        delete charts[dayIndex];
      }
    });

    // Wait a moment for theme to apply, then recreate charts
    setTimeout(() => {
      createAllCharts();
    }, 100);
  }

  // Listen for theme toggle changes
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("change", handleThemeChange);
  }

  // Initialize everything
  function initialize() {
    console.log("Initializing temperature charts...");

    fetchHourlyData()
      .then(() => {
        createAllCharts();
      })
      .catch((error) => {
        console.error("Failed to load hourly data:", error);
        // Still create charts with dummy data
        createAllCharts();
      });
  }

  // Wait for Chart.js to load, then initialize
  function waitForChartJS() {
    if (typeof Chart === "undefined") {
      console.log("Waiting for Chart.js to load...");
      setTimeout(waitForChartJS, 100);
    } else {
      console.log("Chart.js loaded, initializing...");
      initialize();
    }
  }

  // Wait for jQuery to be available
  function waitForJQuery() {
    if (typeof $ === "undefined") {
      console.log("Waiting for jQuery to load...");
      setTimeout(waitForJQuery, 100);
    } else {
      console.log("jQuery loaded, waiting for Chart.js...");
      waitForChartJS();
    }
  }

  // Start initialization
  waitForJQuery();
});
