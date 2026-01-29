/**
 * Temperature Chart for wxmeow
 *
 * Creates an interactive hourly temperature chart for the selected forecast day.
 * Requires Chart.js to be loaded.
 */

document.addEventListener("DOMContentLoaded", function () {
  let charts = {}; // Store chart instances for each day
  let hourlyData = null; // Store the hourly forecast data

  // Initialize hourly data from window object if available
  if (window.hourlyData) {
    hourlyData = window.hourlyData;
    console.log(
      `[DEBUG] Initialized hourlyData from window: ${hourlyData.length} data points`,
    );
  } else {
    console.warn("[WARNING] No window.hourlyData found");
  }

  // Get user's current timezone for proper time handling
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  console.debug(`[DEBUG] Detected user timezone: ${userTimezone}`);

  // Function to display timezone information for debugging
  function displayTimezoneInfo() {
    const now = new Date();
    const utcOffset = now.getTimezoneOffset();
    const offsetHours = Math.floor(Math.abs(utcOffset) / 60);
    const offsetMinutes = Math.abs(utcOffset) % 60;
    const offsetSign = utcOffset <= 0 ? "+" : "-";

    console.log(`[TIMEZONE INFO] User timezone: ${userTimezone}`);
    console.log(
      `[TIMEZONE INFO] UTC offset: ${offsetSign}${offsetHours.toString().padStart(2, "0")}:${offsetMinutes.toString().padStart(2, "0")}`,
    );
    console.log(`[TIMEZONE INFO] Current local time: ${now.toLocaleString()}`);
    console.log(`[TIMEZONE INFO] Current UTC time: ${now.toUTCString()}`);
  }

  // Validate that timezone conversion is working correctly
  function validateTimezoneConversion(sampleTime) {
    try {
      const utcDate = new Date(sampleTime);
      const localDate = new Date(
        utcDate.toLocaleString("en-US", { timeZone: userTimezone }),
      );

      console.log(`[TIMEZONE VALIDATION] Original: ${sampleTime}`);
      console.log(`[TIMEZONE VALIDATION] UTC parsed: ${utcDate.toISOString()}`);
      console.log(
        `[TIMEZONE VALIDATION] Local converted: ${localDate.toISOString()}`,
      );
      console.log(`[TIMEZONE VALIDATION] Local hour: ${localDate.getHours()}`);

      return {
        original: sampleTime,
        utc: utcDate,
        local: localDate,
        localHour: localDate.getHours(),
      };
    } catch (e) {
      console.error(`[TIMEZONE VALIDATION] Error: ${e.message}`);
      return null;
    }
  }

  // Initialize timezone information on load
  displayTimezoneInfo();

  // Validate timezone conversion with a sample time
  const sampleUTCTime = new Date().toISOString();
  validateTimezoneConversion(sampleUTCTime);

  // Helper function to convert UTC time to local timezone
  function convertUTCToLocal(utcTimeString) {
    try {
      const utcDate = new Date(utcTimeString);
      if (isNaN(utcDate.getTime())) {
        console.debug(`[DEBUG] Invalid UTC time string: ${utcTimeString}`);
        return utcTimeString;
      }

      // Create a new date in local timezone with the same components
      const localDate = new Date(
        utcDate.getUTCFullYear(),
        utcDate.getUTCMonth(),
        utcDate.getUTCDate(),
        utcDate.getUTCHours(),
        utcDate.getUTCMinutes(),
        utcDate.getUTCSeconds(),
        utcDate.getUTCMilliseconds(),
      );

      console.debug(
        `[DEBUG] Converted ${utcTimeString} (UTC) to ${localDate.toISOString()} (local)`,
      );
      return localDate.toISOString();
    } catch (e) {
      console.debug(`[DEBUG] Error converting UTC to local: ${e.message}`);
      return utcTimeString;
    }
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

    // Prepare data for the chart - ensure proper 24-hour ordering
    console.debug(`[DEBUG] Filtered data length: ${filteredData.length}`);
    console.debug(`[DEBUG] First item time: ${filteredData[0]?.time}`);
    console.debug(
      `[DEBUG] Last item time: ${filteredData[filteredData.length - 1]?.time}`,
    );

    // Sort data by hour to ensure proper ordering
    filteredData.sort((a, b) => {
      const hourA = new Date(a.time).getHours();
      const hourB = new Date(b.time).getHours();
      return hourA - hourB;
    });

    // Create time-based data points for both temperature and precipitation
    const chartData = filteredData.map((item, index) => {
      const date = new Date(item.time);
      const hour = date.getHours();
      console.debug(
        `[DEBUG] Item ${index}: hour ${hour}, temp ${item.temperature}`,
      );
      return {
        x: hour, // Use hour as x-axis value
        y:
          item.temperature !== null && item.temperature !== undefined
            ? item.temperature
            : null,
        time: item.time,
        condition: item.condition || "",
      };
    });

    // Prepare precipitation data
    const precipData = filteredData.map((item, index) => {
      const date = new Date(item.time);
      const hour = date.getHours();
      const precipValue = item.precip || item.precipitation || 0;
      console.debug(
        `[DEBUG] Item ${index}: hour ${hour}, precip ${precipValue}%`,
      );
      return {
        x: hour,
        y: precipValue,
        time: item.time,
      };
    });

    console.debug(
      `[DEBUG] Chart data prepared with ${chartData.length} points`,
    );
    console.debug(
      `[DEBUG] Noon data point:`,
      chartData.find((d) => d.x === 12),
    );

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
    // Simple, accessible colors - spartan theme
    const tempGradient = ctx.createLinearGradient(0, 0, 0, 300);
    const precipGradient = ctx.createLinearGradient(0, 0, 0, 300);

    // Temperature: dark gray/black - main data
    tempGradient.addColorStop(0, "rgba(60, 60, 60, 0.6)");
    tempGradient.addColorStop(0.5, "rgba(60, 60, 60, 0.3)");
    tempGradient.addColorStop(1, "rgba(60, 60, 60, 0.1)");

    // Precipitation: muted red - secondary data
    precipGradient.addColorStop(0, "rgba(180, 60, 60, 0.5)");
    precipGradient.addColorStop(0.5, "rgba(180, 60, 60, 0.25)");
    precipGradient.addColorStop(1, "rgba(180, 60, 60, 0.05)");

    // Create the chart
    currentChart = new Chart(ctx, {
      type: "line",
      data: {
        datasets: [
          {
            label: "Temperature (°F)",
            data: chartData,
            spanGaps: true,
            backgroundColor: tempGradient,
            borderColor: "#3c3c3c",
            borderWidth: 2,
            pointBackgroundColor: "#3c3c3c",
            pointBorderColor: "#fff",
            pointHoverBackgroundColor: "#3c3c3c", 
            pointHoverBorderColor: "#000",
            pointRadius: 3,
            pointHoverRadius: 6,
            tension: 0.3,
            fill: true,
            yAxisID: 'y',
          },
          {
            label: "Precipitation (%)",
            data: precipData,
            spanGaps: true,
            backgroundColor: precipGradient,
            borderColor: "#b43c3c",
            borderWidth: 2,
            pointBackgroundColor: "#b43c3c",
            pointBorderColor: "#fff", 
            pointHoverBackgroundColor: "#b43c3c",
            pointHoverBorderColor: "#000",
            pointRadius: 3,
            pointHoverRadius: 6,
            tension: 0.3,
            fill: true,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            left: 40,
            right: 10,
            top: 20,
            bottom: 10,
          },
        },
        color: "#333333",
        animation: {
          duration: 400,
          easing: "easeOutQuart",
        },
        hover: {
          mode: "nearest",
          intersect: false,
          animationDuration: 200,
        },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              usePointStyle: true,
              color: "#333333",
              padding: 20,
              font: {
                size: 12,
              },
            },
          },
          tooltip: {
            backgroundColor: "rgba(255, 255, 255, 0.95)",
            titleColor: "#333",
            bodyColor: "#333",
            borderColor: "#ccc",
            borderWidth: 1,
            padding: 8,
            cornerRadius: 4,
            displayColors: false,
            callbacks: {
              label: function (context) {
                const datasetLabel = context.dataset.label;
                const value = context.raw.y;
                
                if (value === null || value === undefined) {
                  return `${datasetLabel}: No data`;
                }
                
                if (datasetLabel.includes("Precipitation")) {
                  return `${datasetLabel}: ${value}%`;
                } else {
                  return `${datasetLabel}: ${value}°F`;
                }
              },
              title: function (tooltipItems) {
                const hour = tooltipItems[0].raw.x;
                if (hour === 0) return "12:00 AM";
                if (hour === 12) return "12:00 PM";
                if (hour < 12) return `${hour}:00 AM`;
                return `${hour - 12}:00 PM`;
              },
            },
          },
          title: {
            display: true,
            text: `Hourly Forecast - ${formatDate(selectedDate)}`,
            color: "#333333",
            font: {
              size: 14,
            },
          },
        },
        scales: {
          y: {
            type: 'linear',
            display: true,
            position: 'left',
            beginAtZero: false,
            title: {
              display: true,
              text: "Temperature (°F)",
              color: "#333333",
            },
            ticks: {
              color: "#333333",
            },
            grid: {
              color: "rgba(0, 0, 0, 0.1)",
            },
          },
          y1: {
            type: 'linear',
            display: true,
            position: 'right',
            beginAtZero: true,
            max: 100,
            title: {
              display: true,
              text: "Precipitation (%)",
              color: "#333333",
            },
            ticks: {
              color: "#333333",
            },
            grid: {
              drawOnChartArea: false,
            },
          },
          x: {
            title: {
              display: true,
              text: "Time of Day",
              color: "#333333",
            },
            type: "linear",
            position: "bottom",
            min: 0,
            max: 23,
            ticks: {
              color: "#333333",
              stepSize: 3,
              callback: function (value) {
                if (value === 0) return "12 AM";
                if (value === 3) return "3 AM"; 
                if (value === 6) return "6 AM";
                if (value === 9) return "9 AM";
                if (value === 12) return "12 PM";
                if (value === 15) return "3 PM";
                if (value === 18) return "6 PM";
                if (value === 21) return "9 PM";
                return "";
              },
            },
            grid: {
              display: true,
              color: function (context) {
                const value = context.tick.value;
                // Emphasize midnight and noon
                if (value === 0 || value === 12) {
                  return "rgba(0, 0, 0, 0.3)";
                }
                // Show grid lines for every 6 hours
                if (value % 6 === 0) {
                  return "rgba(0, 0, 0, 0.15)";
                }
                return "rgba(0, 0, 0, 0.05)";
              },
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

  // Helper function to get the date for the selected day index in local timezone
  function getSelectedDate(dayIndex) {
    // Handle the current day (index 0) as today in local timezone
    const today = new Date();
    const localToday = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
    );

    if (dayIndex === 0) {
      return localToday;
    }

    // For other days, try to get the date from the forecast
    const forecastDates = document.querySelectorAll('[id^="date-"]');
    if (forecastDates.length > dayIndex) {
      const dateText = forecastDates[dayIndex].textContent;
      if (dateText) {
        // Handle different date formats - try to parse the date
        try {
          const parsedDate = new Date(dateText);
          // Ensure the parsed date is in local timezone
          return new Date(
            parsedDate.getFullYear(),
            parsedDate.getMonth(),
            parsedDate.getDate(),
          );
        } catch (e) {
          // Fall through to the fallback
        }
      }
    }

    // Fallback: calculate the date based on the index in local timezone
    const targetDate = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate() + parseInt(dayIndex),
    );
    return targetDate;
  }

  // Filter hourly data by date (matching just the date portion)
  function filterHourlyDataByDate(hourlyData, targetDate) {
    if (!hourlyData || hourlyData.length === 0) {
      return [];
    }

    // Use local timezone for consistent date comparison
    const targetDateLocal = new Date(
      targetDate.getFullYear(),
      targetDate.getMonth(),
      targetDate.getDate(),
    );

    console.debug("[DEBUG] Target date:", targetDate);
    console.debug("[DEBUG] First hourly data item:", hourlyData[0]);
    
    const targetDateStr = targetDate.toISOString().split("T")[0];

    // Filter data by comparing dates - simplified approach
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

        // Compare by ISO date string (most reliable)
        const itemDateStr = itemDate.toISOString().split("T")[0];
        const matchesISO = itemDateStr === targetDateStr;

        // Compare by day and month as fallback
        const matchesDay =
          itemDate.getDate() === targetDate.getDate() &&
          itemDate.getMonth() === targetDate.getMonth();

        console.debug(
          `[DEBUG] Item time: ${item.time}, Item date: ${itemDateStr}, Target: ${targetDateStr}, Matches: ${matchesISO || matchesDay}`,
        );

        return matchesISO || matchesDay;
      } catch (e) {
        console.debug("[DEBUG] Error parsing date:", e, item);
        return false;
      }
    });

    console.debug(
      `[DEBUG] Filtered ${filteredData.length} items for ${targetDateStr}`,
    );

    // If we got results, ensure they're sorted by time and fill gaps for 24-hour coverage
    if (filteredData.length > 0) {
      console.debug(
        `[DEBUG] Successfully filtered ${filteredData.length} data points for date ${targetDateStr}`,
      );

      // Sort by time to ensure proper order
      filteredData.sort((a, b) => new Date(a.time) - new Date(b.time));

      // Ensure we have 24-hour coverage centered around noon
      return ensureFullDayCoverage(filteredData, targetDate);
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
      return ensureFullDayCoverage(filteredData, targetDate);
    }

    // Third attempt: if we're showing today (day 0), show available data from current time
    const localToday = new Date();
    const todayStr = localToday.toLocaleDateString("en-CA");
    if (targetDateStr === todayStr) {
      console.debug(`[DEBUG] Showing today's data (${todayStr}) - may start from current time`);
      const dayData = hourlyData.slice(0, Math.min(24, hourlyData.length));
      return ensureFullDayCoverage(dayData, targetDate);
    }

    // Fourth attempt: For future days, calculate proper midnight-to-midnight periods
    const dayDiff = Math.floor(
      (targetDate - localToday) / (24 * 60 * 60 * 1000),
    );
    
    if (dayDiff > 0 && dayDiff < 5) {
      console.debug(
        `[DEBUG] Future day ${dayDiff}: finding midnight-to-midnight hours`,
      );
      
      // For future days, we need to account for the fact that today's data 
      // might start at current hour, not midnight
      const currentHour = new Date().getHours();
      const todayHoursRemaining = 24 - currentHour;
      
      // Future day data should start after today's remaining hours
      const futureStartIndex = todayHoursRemaining + ((dayDiff - 1) * 24);
      const futureEndIndex = Math.min(futureStartIndex + 24, hourlyData.length);
      
      console.debug(
        `[DEBUG] Future day ${dayDiff}: startIndex=${futureStartIndex}, endIndex=${futureEndIndex}, current hour=${currentHour}`,
      );
      
      const dayData = hourlyData.slice(futureStartIndex, futureEndIndex);
      return ensureFullDayCoverage(dayData, targetDate);
    }

    // If all else fails, return empty array
    return [];
  }

  // Helper function to ensure 24-hour coverage with noon centered in local timezone
  function ensureFullDayCoverage(data, targetDate) {
    console.debug(
      `[DEBUG] ensureFullDayCoverage called with ${data.length} items`,
    );

    // Always create a complete 24-hour structure regardless of input
    const fullDayData = [];
    const baseDate = new Date(
      targetDate.getFullYear(),
      targetDate.getMonth(),
      targetDate.getDate(),
      0,
      0,
      0,
      0,
    );

    // Create exactly 24 data points for hours 0-23
    for (let hour = 0; hour < 24; hour++) {
      const hourDate = new Date(
        baseDate.getFullYear(),
        baseDate.getMonth(),
        baseDate.getDate(),
        hour,
        0,
        0,
        0,
      );

      // Find existing data for this hour
      let existingData = null;
      if (data && data.length > 0) {
        existingData = data.find((item) => {
          if (!item.time) return false;
          const itemDate = new Date(item.time);
          const itemHour = itemDate.getHours();
          return itemHour === hour;
        });
      }

      if (existingData) {
        // Use existing data but ensure proper time format
        fullDayData.push({
          time: hourDate.toISOString(),
          temperature: existingData.temperature,
          condition: existingData.condition || "Clear",
        });
        console.debug(
          `[DEBUG] Hour ${hour}: using existing data (${existingData.temperature}°F)`,
        );
      } else {
        // Don't create placeholder data - just skip missing hours
        // This prevents synthetic sine wave temperature data
        console.debug(`[DEBUG] Hour ${hour}: no data available, skipping`);
        continue;
      }
    }

    console.debug(`[DEBUG] Created complete 24-hour dataset:`);
    console.debug(`[DEBUG] Midnight (hour 0): ${fullDayData[0].temperature}°F`);
    console.debug(`[DEBUG] 6 AM (hour 6): ${fullDayData[6].temperature}°F`);
    console.debug(`[DEBUG] NOON (hour 12): ${fullDayData[12].temperature}°F`);
    console.debug(`[DEBUG] 6 PM (hour 18): ${fullDayData[18].temperature}°F`);
    console.debug(`[DEBUG] 11 PM (hour 23): ${fullDayData[23].temperature}°F`);

    return fullDayData;
  }

  // Format time for display in chart labels using browser's local timezone
  function formatTime(timeString) {
    try {
      const date = new Date(timeString);
      if (isNaN(date.getTime())) {
        throw new Error("Invalid date");
      }

      // Get hour in local timezone
      const hour = date.getHours();

      // Special formatting for key hours to emphasize noon (in local time)
      if (hour === 0) return "12 AM";
      if (hour === 6) return "6 AM";
      if (hour === 12) return "12 PM"; // Noon - emphasized (local time)
      if (hour === 18) return "6 PM";

      // Standard formatting for other hours using browser's locale and timezone
      return date.toLocaleTimeString([], {
        hour: "numeric",
        hour12: true,
        timeZone: userTimezone,
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
  // Format date for display
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

    fetch(`/api/hourly/${encodeURIComponent(location)}`)
      .then((response) => {
        if (!response.ok) throw new Error("Weather API error");
        return response.json();
      })
      .then((data) => {
        console.debug("[DEBUG] Raw API response:", data);

        // The API now returns the hourly data directly as an array
        let forecastData;
        
        if (Array.isArray(data)) {
          forecastData = data;
        } else if (data && data.hourly_forecast) {
          // Legacy support for wrapped format
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
        } else {
          console.warn("No hourly forecast data in response");
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
