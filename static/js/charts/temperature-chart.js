/**
 * Temperature Chart for wxmeow
 *
 * Creates an interactive hourly temperature chart for the selected forecast day.
 * Requires Chart.js to be loaded.
 */

document.addEventListener("DOMContentLoaded", function () {
  let charts = {}; // Store chart instances for each day
  let hourlyData = null; // Store the hourly forecast data

  // Helper function to check if dark mode is active
  function isDarkMode() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  // Function to create or update the temperature chart
  function createTemperatureChart(dayIndex) {
    console.log(`Creating/updating chart for day ${dayIndex}`);
    console.debug(`[DEBUG] Chart creation process started for day ${dayIndex}`);
    // Get the container where we'll place the chart for this day
    const chartContainer = document.getElementById(
      `hourly-temperature-chart-${dayIndex}`,
    );
    if (!chartContainer) {
      console.error("Chart container not found for day", dayIndex);
      return;
    }

    // Show the container and ensure proper styling
    chartContainer.style.display = "block";
    chartContainer.style.width = "100%";
    chartContainer.style.maxWidth = "800px";
    chartContainer.style.margin = "20px auto";
    console.debug(
      `[DEBUG] Chart container styling applied: ${chartContainer.id}, display=${chartContainer.style.display}`,
    );

    // If there's an existing chart for this day, destroy it
    if (charts[dayIndex]) {
      console.debug(`[DEBUG] Destroying existing chart for day ${dayIndex}`);
      charts[dayIndex].destroy();
      charts[dayIndex] = null;
    }

    // If we don't have hourly data, fetch it
    if (!hourlyData) {
      console.debug(
        `[DEBUG] No hourly data available, attempting to fetch data`,
      );
      const location = getCurrentLocation();
      if (location) {
        console.debug(
          `[DEBUG] Found location: ${location}, fetching hourly data`,
        );
        fetchHourlyData(location, dayIndex);
        return;
      } else {
        console.error(`[ERROR] No location found to fetch hourly data`);
        chartContainer.innerHTML = "<p>No hourly data available</p>";
        console.log("No hourly data available");
        return;
      }
    }

    // Filter hourly data for the selected day
    const selectedDate = getSelectedDate(dayIndex);
    if (!selectedDate) {
      console.error("Could not determine date for day:", dayIndex);
      chartContainer.innerHTML =
        "<p>Could not determine date for selected day</p>";
      return;
    }

    // Filter hourly data for the selected date
    const filteredData = filterHourlyDataByDate(hourlyData, selectedDate);
    console.log(
      `Day ${dayIndex} (${selectedDate.toDateString()}): Found ${filteredData.length} hourly data points`,
    );

    // If no data for this day, show message
    if (filteredData.length === 0) {
      console.warn(
        `[WARNING] No hourly data points found for day ${dayIndex} (${selectedDate.toDateString()})`,
      );
      chartContainer.innerHTML = "<p>No hourly data available for this day</p>";
      return;
    }

    // Prepare data for the chart
    const labels = filteredData.map((item) => formatTime(item.time));
    const temperatures = filteredData.map((item) => item.temperature);
    const conditions = filteredData.map((item) => item.condition || "");

    // Create canvas element if it doesn't exist
    chartContainer.innerHTML = ""; // Clear any previous content
    const canvas = document.createElement("canvas");
    canvas.id = `temperature-chart-${dayIndex}`;
    canvas.classList.add("temperature-chart");
    canvas.style.width = "100%";
    canvas.style.height = "300px";
    canvas.style.maxWidth = "100%";
    canvas.style.display = "block";
    chartContainer.appendChild(canvas);
    console.debug(
      `[DEBUG] Canvas created for chart ${dayIndex}: ${canvas.id}, dimensions: ${canvas.style.width}x${canvas.style.height}`,
    );

    // Set up gradient for the chart
    const ctx = canvas.getContext("2d");
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);

    if (isDarkMode()) {
      gradient.addColorStop(0, "rgba(255, 159, 64, 0.7)");
      gradient.addColorStop(0.5, "rgba(255, 159, 64, 0.3)");
      gradient.addColorStop(1, "rgba(255, 159, 64, 0.05)");
    } else {
      gradient.addColorStop(0, "rgba(66, 133, 244, 0.7)");
      gradient.addColorStop(0.5, "rgba(66, 133, 244, 0.3)");
      gradient.addColorStop(1, "rgba(66, 133, 244, 0.05)");
    }

    // Create the chart
    currentChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Temperature (°F)",
            data: temperatures,
            backgroundColor: gradient,
            borderColor: isDarkMode()
              ? "rgba(255, 159, 64, 1)"
              : "rgba(66, 133, 244, 1)",
            borderWidth: 3,
            pointBackgroundColor: isDarkMode()
              ? "rgba(255, 159, 64, 1)"
              : "rgba(66, 133, 244, 1)",
            pointBorderColor: isDarkMode() ? "#333" : "#fff",
            pointHoverBackgroundColor: isDarkMode() ? "#333" : "#fff",
            pointHoverBorderColor: isDarkMode()
              ? "rgba(255, 159, 64, 1)"
              : "rgba(66, 133, 244, 1)",
            pointRadius: 4,
            pointHoverRadius: 7,
            tension: 0.4,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            left: 10,
            right: 30,
            top: 20,
            bottom: 10,
          },
        },
        color: isDarkMode() ? "#e0e0e0" : "#333333",
        animation: {
          duration: 1200,
          easing: "easeOutQuart",
        },
        hover: {
          mode: "nearest",
          intersect: false,
          animationDuration: 300,
        },
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: isDarkMode()
              ? "rgba(30, 30, 30, 0.9)"
              : "rgba(255, 255, 255, 0.95)",
            titleColor: isDarkMode() ? "#fff" : "#333",
            bodyColor: isDarkMode() ? "#fff" : "#333",
            borderColor: isDarkMode() ? "#666" : "#ccc",
            borderWidth: 1,
            padding: 12,
            cornerRadius: 6,
            displayColors: false,
            callbacks: {
              label: function (context) {
                const dataIndex = context.dataIndex;
                const temp = temperatures[dataIndex];
                const condition = conditions[dataIndex] || "Unknown";
                const formattedTemp = temp ? `${temp}°F` : "N/A";

                return [
                  `Temperature: ${formattedTemp}`,
                  `Condition: ${condition}`,
                ];
              },
              title: function (tooltipItems) {
                // Format the time in a more readable way
                try {
                  const time = tooltipItems[0].label;
                  const date = new Date(
                    filteredData[tooltipItems[0].dataIndex].time,
                  );
                  return date.toLocaleTimeString([], {
                    weekday: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  });
                } catch (e) {
                  return tooltipItems[0].label;
                }
              },
            },
          },
          title: {
            display: true,
            text: `Hourly Temperature - ${formatDate(selectedDate)}`,
            color: isDarkMode() ? "#e0e0e0" : "#333333",
            font: {
              size: 16,
            },
          },
        },
        scales: {
          y: {
            beginAtZero: false,
            title: {
              display: true,
              text: "Temperature (°F)",
              color: isDarkMode() ? "#e0e0e0" : "#333333",
            },
            ticks: {
              color: isDarkMode() ? "#e0e0e0" : "#333333",
            },
            grid: {
              color: isDarkMode()
                ? "rgba(255, 255, 255, 0.1)"
                : "rgba(0, 0, 0, 0.1)",
            },
          },
          x: {
            title: {
              display: true,
              text: "Time",
              color: isDarkMode() ? "#e0e0e0" : "#333333",
            },
            ticks: {
              color: isDarkMode() ? "#e0e0e0" : "#333333",
            },
            grid: {
              color: isDarkMode()
                ? "rgba(255, 255, 255, 0.1)"
                : "rgba(0, 0, 0, 0.1)",
            },
          },
        },
      },
    });

    // Make sure the chart displays correctly
    canvas.style.height = "300px";
    canvas.style.width = "100%";

    // Store the chart reference
    charts[dayIndex] = currentChart;
  }

  // Helper function to get the date for the selected day index
  function getSelectedDate(dayIndex) {
    // Handle the current day (index 0) as today
    const today = new Date();

    if (dayIndex === 0) {
      return today;
    }

    // For other days, try to get the date from the forecast
    const forecastDates = document.querySelectorAll('[id^="date-"]');
    if (forecastDates.length > dayIndex) {
      const dateText = forecastDates[dayIndex].textContent;
      if (dateText) {
        // Handle different date formats - try to parse the date
        try {
          return new Date(dateText);
        } catch (e) {
          // Fall through to the fallback
        }
      }
    }

    // Fallback: calculate the date based on the index
    const date = new Date();
    date.setDate(today.getDate() + parseInt(dayIndex));
    return date;
  }

  // Filter hourly data by date (matching just the date portion)
  function filterHourlyDataByDate(hourlyData, targetDate) {
    if (!hourlyData || hourlyData.length === 0) {
      return [];
    }

    console.debug("[DEBUG] Target date:", targetDate);
    console.debug("[DEBUG] First hourly data item:", hourlyData[0]);

    // Convert target date to strings in different formats for comparison
    const targetDateStr = targetDate.toISOString().split("T")[0];
    const targetDateDay = targetDate.getDate();
    const targetMonth = targetDate.getMonth() + 1; // JavaScript months are 0-indexed

    // Filter data by comparing dates
    let filteredData = hourlyData.filter((item) => {
      try {
        if (!item.time) return false;

        // Parse the date from the time field
        const itemDate = new Date(item.time);

        // Check if it's a valid date
        if (isNaN(itemDate.getTime())) {
          console.debug("[DEBUG] Invalid date:", item.time);
          return false;
        }

        // Compare by ISO date string
        const itemDateStr = itemDate.toISOString().split("T")[0];
        const matchesISO = itemDateStr === targetDateStr;

        // Compare by day and month as fallback
        const matchesDay =
          itemDate.getDate() === targetDay &&
          itemDate.getMonth() + 1 === targetMonth;

        return matchesISO || matchesDay;
      } catch (e) {
        console.debug("[DEBUG] Error parsing date:", e, item);
        return false;
      }
    });

    console.debug(
      `[DEBUG] Filtered ${filteredData.length} items for ${targetDateStr}`,
    );

    // If we got results, return them
    if (filteredData.length > 0) {
      console.debug(
        `[DEBUG] Successfully filtered ${filteredData.length} data points for date ${targetDateStr}`,
      );
      return filteredData;
    }

    // Find the day of the week for our target date (0=Sunday, 1=Monday, etc)
    const targetDayOfWeek = targetDate.getDay();

    // Second attempt: try to find items with a "dayOfWeek" property matching our target
    filteredData = hourlyData.filter((item) => {
      if (item.dayOfWeek !== undefined) {
        return parseInt(item.dayOfWeek) === targetDayOfWeek;
      }
      return false;
    });

    if (filteredData.length > 0) {
      return filteredData;
    }

    // Third attempt: if we're showing today (day 0), show the first 24 hours of data
    if (targetDate.toDateString() === new Date().toDateString()) {
      return hourlyData.slice(0, Math.min(24, hourlyData.length));
    }

    // Fourth attempt: if we're showing day N, show hours (N*24) through ((N+1)*24)
    const today = new Date();
    const dayDiff = Math.floor((targetDate - today) / (24 * 60 * 60 * 1000));
    if (dayDiff >= 0 && dayDiff < 5) {
      const startIndex = Math.min(dayDiff * 24, hourlyData.length - 1);
      const endIndex = Math.min(startIndex + 24, hourlyData.length);
      return hourlyData.slice(startIndex, endIndex);
    }

    // If all else fails, return empty array
    return [];
  }

  // Format time for display in chart labels
  function formatTime(timeString) {
    try {
      const date = new Date(timeString);
      if (isNaN(date.getTime())) {
        throw new Error("Invalid date");
      }

      // Just show hour without minutes for cleaner display
      return date.toLocaleTimeString([], {
        hour: "numeric",
      });
    } catch (e) {
      // If we can't parse the date, see if it contains a time string we can extract
      if (typeof timeString === "string") {
        // Try to match various time formats
        const timeMatch = timeString.match(
          /(\d{1,2})(?::(\d{2}))?(?:\s*(am|pm|AM|PM))?/,
        );
        if (timeMatch) {
          return timeMatch[0];
        }

        // Look for hour strings like "3 AM", "2PM", etc.
        const hourMatch = timeString.match(/(\d{1,2})\s*(am|pm|AM|PM)/);
        if (hourMatch) {
          return hourMatch[0];
        }
      }

      // If all else fails, return the string or "N/A"
      return timeString || "N/A";
    }
  }

  // Format date for display in chart title
  function formatDate(date) {
    return date.toLocaleDateString([], {
      weekday: "short",
      month: "short",
      day: "numeric",
    });
  }

  // Setup event handlers for the day buttons
  function setupEventHandlers() {
    // Listen for the custom daySelected event
    // Manual day selection for testing
    $(document).on("daySelected", function (event, dayIndex) {
      const dayNum = parseInt(dayIndex);
      console.log(`Day Selected event triggered for day ${dayNum}`);
      console.debug(
        `[DEBUG] Day selection event received. Day=${dayNum}, Event source:`,
        event.target,
      );

      // Wait a tiny bit for the DOM to update before showing the chart
      setTimeout(function () {
        updateActiveChart(dayNum);
      }, 50);
    });

    // Add manual click handlers to ensure they work
    $(".day-selector").on("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      const dayId = $(this).attr("id");
      console.log(
        `Manual day selector click handler triggered for day ${dayId}`,
      );
      console.debug(
        `[DEBUG] Day selector clicked: id=${dayId}, element=`,
        this,
      );
      $(document).trigger("daySelected", [dayId]);
      return false;
    });
  }

  // Helper function to update the active chart
  function updateActiveChart(dayIndex) {
    console.log(`Updating active chart for day ${dayIndex}`);
    console.debug(
      `[DEBUG] Starting update of active chart for day ${dayIndex}`,
    );

    // Hide all chart containers first
    for (let i = 0; i < 5; i++) {
      let container = $(`#hourly-temperature-chart-${i}`);
      container.hide();
      console.debug(
        `[DEBUG] Hiding chart container ${i}: found=${container.length > 0}`,
      );
    }

    // Create or update the chart
    createTemperatureChart(dayIndex);

    // Store the current day - this should be already set by the day selector click
    lastSelectedDay = dayIndex;

    // Ensure the chart is visible and properly positioned
    const chartContainer = $(`#hourly-temperature-chart-${dayIndex}`);
    console.debug(
      `[DEBUG] Found chart container for day ${dayIndex}: ${chartContainer.length > 0}`,
    );

    chartContainer.css({
      display: "block",
      width: "100%",
      "max-width": "800px",
      margin: "20px auto",
      height: "350px",
    });
    console.debug(`[DEBUG] Applied CSS to chart container ${dayIndex}`);

    // Force layout recalculation
    chartContainer.hide().show(0);
    console.debug(
      `[DEBUG] Forced redraw of chart container ${dayIndex}, visibility now: ${chartContainer.is(":visible")}`,
    );
  }

  // Fetch hourly forecast data from the API
  function fetchHourlyData(location, initialDayIndex = 0) {
    // Only proceed if we have a location
    if (!location) {
      console.error("No location provided for fetchHourlyData");
      return;
    }

    console.log(`Fetching hourly data for location: ${location}`);

    // Find all chart containers and show loading message
    for (let i = 0; i < 5; i++) {
      const container = document.getElementById(
        `hourly-temperature-chart-${i}`,
      );
      if (container) {
        container.innerHTML = "<p>Loading temperature data...</p>";
        // Only show loading for the active day
        if (i === parseInt(initialDayIndex)) {
          container.style.display = "block";
        }
      }
    }

    fetch(`/api/weather/${encodeURIComponent(location)}`)
      .then((response) => {
        if (!response.ok) throw new Error("Weather API error");
        return response.json();
      })
      .then((data) => {
        console.debug("[DEBUG] Raw API response:", data);

        if (data && data.hourly_forecast) {
          let forecastData;

          // Handle different response formats
          if (typeof data.hourly_forecast === "string") {
            console.warn("Hourly forecast is a string, not an array");
            forecastData = [];
          } else if (Array.isArray(data.hourly_forecast)) {
            forecastData = data.hourly_forecast;
          } else {
            console.warn(
              "Unexpected hourly forecast format:",
              typeof data.hourly_forecast,
            );
            forecastData = [];
          }

          console.log(
            `Received ${forecastData.length} hourly forecast data points`,
          );

          if (forecastData.length > 0) {
            hourlyData = forecastData;

            // Sort hourly data by time if available
            hourlyData.sort((a, b) => {
              try {
                return new Date(a.time) - new Date(b.time);
              } catch (e) {
                return 0;
              }
            });

            // Log the first few data points for debugging
            console.log(
              "First 3 hourly data points:",
              hourlyData.slice(0, 3).map((item) => ({
                time: item.time,
                temp: item.temperature || item.temp,
                condition: item.condition,
              })),
            );

            // Show initial chart for the specified day
            createTemperatureChart(initialDayIndex);
          } else {
            handleNoForecastData(
              "No hourly forecast data points available",
              initialDayIndex,
            );
          }
        } else {
          handleNoForecastData(
            "No hourly forecast data available in API response",
            initialDayIndex,
          );
        }
      })
      .catch((error) => {
        console.error("Error fetching hourly forecast data:", error);
        handleNoForecastData(
          "Unable to load hourly forecast data",
          initialDayIndex,
        );
      });

    // Helper function to handle missing forecast data
    function handleNoForecastData(message, dayIndex) {
      console.warn(message);
      for (let i = 0; i < 5; i++) {
        const container = document.getElementById(
          `hourly-temperature-chart-${i}`,
        );
        if (container) {
          container.innerHTML = `<p>${message}</p>`;
          container.style.display = i === parseInt(dayIndex) ? "block" : "none";
        }
      }
    }
  }

  // Get the current location from the data attribute or URL
  function getCurrentLocation() {
    // First try to get it from the data attribute on body
    const bodyElement = document.body;
    if (bodyElement && bodyElement.getAttribute("data-location")) {
      return bodyElement.getAttribute("data-location");
    }

    // Fall back to parsing the URL
    const pathParts = window.location.pathname.split("/");
    if (pathParts.length > 2 && pathParts[1] === "wx") {
      return decodeURIComponent(pathParts[2]);
    }
    return null;
  }

  // Initialize everything when the document is ready
  $(document).ready(function () {
    // Set up event handlers
    setupEventHandlers();

    console.log("Temperature chart initialized");

    // Get current location
    const location = getCurrentLocation();
    if (location) {
      console.log(`Location found: ${location}`);
      // Start with day 0 selected
      fetchHourlyData(location, 0);
    } else {
      console.warn("No location found for temperature chart");
      // Update all chart containers with error message
      for (let i = 0; i < 5; i++) {
        const container = document.getElementById(
          `hourly-temperature-chart-${i}`,
        );
        if (container) {
          container.innerHTML = "<p>No location specified</p>";
          // Only show for currently active day
          if (i === 0) {
            container.style.display = "block";
          }
        }
      }
    }
  });

  // Update chart when theme changes
  const themeToggle = document.getElementById("theme-toggle");
  if (themeToggle) {
    themeToggle.addEventListener("change", function () {
      // If we have data, recreate all charts with the new theme
      if (hourlyData) {
        // Get current day index, defaulting to 0
        const dayIndex =
          typeof lastSelectedDay !== "undefined" ? lastSelectedDay : 0;

        // Wait for theme change to take effect
        setTimeout(function () {
          // Clear all charts first
          for (let i = 0; i < 5; i++) {
            if (charts[i]) {
              charts[i].destroy();
              charts[i] = null;
            }
          }

          // Create chart for current day
          createTemperatureChart(dayIndex);

          // Preload charts for other days - focus on the next day first
          setTimeout(() => {
            // Calculate the next day (circular)
            const nextDay = (dayIndex + 1) % 5;

            // Create chart for the next day first
            const nextContainer = document.getElementById(
              `hourly-temperature-chart-${nextDay}`,
            );
            if (nextContainer && !charts[nextDay]) {
              nextContainer.style.display = "none";
              createTemperatureChart(nextDay);
            }

            // Then create charts for remaining days
            setTimeout(() => {
              for (let i = 0; i < 5; i++) {
                if (i !== dayIndex && i !== nextDay && !charts[i]) {
                  const container = document.getElementById(
                    `hourly-temperature-chart-${i}`,
                  );
                  if (container) {
                    container.style.display = "none";
                    createTemperatureChart(i);
                  }
                }
              }
            }, 300);
          }, 200);
        }, 100);
      }
    });
  }
});
