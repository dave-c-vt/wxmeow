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

    // Check if a chart already exists and is working
    if (
      chartContainer.querySelector("canvas") &&
      !chartContainer.textContent.includes("No hourly data")
    ) {
      console.debug(
        `[DEBUG] Chart already exists for day ${dayIndex}, skipping creation`,
      );
      return;
    }

    // Preserve scroll position to prevent page jumping
    const currentScrollY = window.scrollY;
    const currentScrollX = window.scrollX;

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
    console.debug("[DEBUG] About to filter hourly data:", {
      dayIndex,
      selectedDate,
      hourlyDataLength: hourlyData ? hourlyData.length : 0,
      hourlyDataSample: hourlyData ? hourlyData.slice(0, 2) : null,
    });
    const filteredData = filterHourlyDataByDate(hourlyData, selectedDate);
    console.debug("[DEBUG] After filtering:", {
      filteredDataLength: filteredData ? filteredData.length : 0,
      filteredDataSample: filteredData ? filteredData.slice(0, 2) : null,
    });
    console.debug("[DEBUG] Returned filteredData is:", filteredData);
    console.debug(
      `[DEBUG] About to check if ${filteredData ? filteredData.length : "null"} === 0`,
    );
    console.log(
      `Day ${dayIndex} (${selectedDate.toDateString()}): Found ${filteredData.length} hourly data points`,
    );

    // If no data for this day, show message
    if (filteredData.length === 0) {
      console.warn(
        `[WARNING] No hourly data points found for day ${dayIndex} (${selectedDate.toDateString()})`,
      );
      chartContainer.innerHTML = "<p>No hourly data available for this day</p>";

      // Restore scroll position
      if (typeof currentScrollY !== "undefined") {
        setTimeout(() => window.scrollTo(currentScrollX, currentScrollY), 0);
      }
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

    // Create time-based data points instead of just labels
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
        precipitation: item.precipitation || 0,
      };
    });

    // Find highest and lowest temperatures
    const validTemps = chartData.filter(
      (item) => item.y !== null && item.y !== undefined,
    );
    let highTemp = null,
      lowTemp = null,
      highIndex = -1,
      lowIndex = -1;

    if (validTemps.length > 0) {
      highTemp = Math.max(...validTemps.map((item) => item.y));
      lowTemp = Math.min(...validTemps.map((item) => item.y));

      // Find indices of high/low temps in chartData
      highIndex = chartData.findIndex((item) => item.y === highTemp);
      lowIndex = chartData.findIndex((item) => item.y === lowTemp);
    }

    // Add sunrise/sunset times (approximate based on season/location)
    const today = new Date();
    const dayOfYear = Math.floor(
      (today - new Date(today.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24),
    );

    // Rough sunrise/sunset calculation (can be refined based on actual location)
    const sunriseHour =
      6 + Math.sin(((dayOfYear - 81) * 2 * Math.PI) / 365) * 1.5;
    const sunsetHour =
      18 - Math.sin(((dayOfYear - 81) * 2 * Math.PI) / 365) * 1.5;

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
        datasets: [
          {
            label: "Temperature (°F)",
            data: chartData,
            spanGaps: true,
            backgroundColor: gradient,
            borderColor: isDarkMode()
              ? "rgba(255, 159, 64, 1)"
              : "rgba(66, 133, 244, 1)",
            borderWidth: 3,
            pointBackgroundColor: chartData.map((item, index) => {
              // Highlight high/low temperature points
              if (index === highIndex) return "rgba(255, 99, 132, 1)"; // Red for high
              if (index === lowIndex) return "rgba(54, 162, 235, 1)"; // Blue for low
              return isDarkMode()
                ? "rgba(255, 159, 64, 1)"
                : "rgba(66, 133, 244, 1)";
            }),
            pointBorderColor: chartData.map((item, index) => {
              if (index === highIndex || index === lowIndex) return "#fff";
              return isDarkMode() ? "#333" : "#fff";
            }),
            pointRadius: chartData.map((item, index) => {
              // Make high/low points larger
              if (index === highIndex || index === lowIndex) return 8;
              return 4;
            }),
            pointBorderWidth: chartData.map((item, index) => {
              if (index === highIndex || index === lowIndex) return 3;
              return 1;
            }),
            pointHoverBackgroundColor: isDarkMode() ? "#333" : "#fff",
            pointHoverBorderColor: isDarkMode()
              ? "rgba(255, 159, 64, 1)"
              : "rgba(66, 133, 244, 1)",
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
            left: 40,
            right: 10,
            top: 50,
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
                const dataPoint = context.raw;
                const temp = dataPoint.y;
                const condition = dataPoint.condition || "Unknown";
                const precipitation = dataPoint.precipitation || 0;
                const index = context.dataIndex;

                // Handle null/missing temperature data
                if (temp === null || temp === undefined) {
                  return [
                    `Temperature: No data available`,
                    `Condition: ${condition}`,
                    `Precipitation: ${precipitation}%`,
                  ];
                }

                const formattedTemp = `${temp}°F`;
                let tempLabel = `Temperature: ${formattedTemp}`;

                // Add HIGH/LOW indicators
                if (index === highIndex) {
                  tempLabel += " (HIGH)";
                } else if (index === lowIndex) {
                  tempLabel += " (LOW)";
                }

                return [
                  tempLabel,
                  `Condition: ${condition}`,
                  `Precipitation: ${precipitation}%`,
                ];
              },
              title: function (tooltipItems) {
                // Format the time with date in a more readable way
                try {
                  const dataPoint = tooltipItems[0].raw;
                  const date = new Date(dataPoint.time);
                  return date
                    .toLocaleString([], {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                      hour12: true,
                    })
                    .toUpperCase();
                } catch (e) {
                  console.debug("[DEBUG] Error formatting tooltip title:", e);
                  return `${tooltipItems[0].label || "N/A"}`;
                }
              },
            },
          },
        },
        scales: {
          x: {
            type: "linear",
            position: "bottom",
            min: 0,
            max: 23,
            title: {
              display: true,
              text: "Hour of Day",
              font: {
                family: "Arial",
                size: 12,
                weight: "bold",
              },
              color: isDarkMode() ? "#e0e0e0" : "#333333",
            },
            ticks: {
              stepSize: 2,
              color: isDarkMode() ? "#e0e0e0" : "#333333",
              font: {
                family: "Arial",
                size: 11,
              },
              callback: function (value, index, values) {
                const hour = Math.round(value);
                if (hour === 0) return "12 AM";
                if (hour < 12) return `${hour} AM`;
                if (hour === 12) return "12 PM";
                return `${hour - 12} PM`;
              },
            },
            grid: {
              color: isDarkMode()
                ? "rgba(255, 255, 255, 0.1)"
                : "rgba(0, 0, 0, 0.1)",
              lineWidth: function (context) {
                const value = context.tick.value;
                if (value % 12 === 0) return 2;
                if (value % 6 === 0) return 1.5;
                return 1;
              },
            },
          },
          y: {
            title: {
              display: true,
              text: "Temperature (°F)",
              font: {
                family: "Arial",
                size: 12,
                weight: "bold",
              },
              color: isDarkMode() ? "#e0e0e0" : "#333333",
            },
            ticks: {
              color: isDarkMode() ? "#e0e0e0" : "#333333",
              font: {
                family: "Arial",
                size: 11,
              },
            },
            grid: {
              color: isDarkMode()
                ? "rgba(255, 255, 255, 0.1)"
                : "rgba(0, 0, 0, 0.1)",
              lineWidth: function (context) {
                const value = context.tick.value;
                if (value % 12 === 0) return 2;
                if (value % 6 === 0) return 1.5;
                return 1;
              },
            },
          },
        },
      },
    });

    // Wait for chart to render, then add custom annotations
    setTimeout(() => {
      const ctx = currentChart.ctx;
      const yAxis = currentChart.scales.y;
      const xAxis = currentChart.scales.x;

      // Draw sunrise line
      if (sunriseHour >= 0 && sunriseHour <= 23) {
        const sunriseX = xAxis.getPixelForValue(sunriseHour);
        ctx.save();
        ctx.strokeStyle = "rgba(255, 193, 7, 0.8)";
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(sunriseX, yAxis.top);
        ctx.lineTo(sunriseX, yAxis.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        // Sunrise label
        ctx.fillStyle = "rgba(255, 193, 7, 1)";
        ctx.font = "bold 14px Arial";
        ctx.textAlign = "center";
        ctx.fillText("🌅 SUNRISE", sunriseX, yAxis.top - 10);
        ctx.restore();
      }

      // Draw sunset line
      if (sunsetHour >= 0 && sunsetHour <= 23) {
        const sunsetX = xAxis.getPixelForValue(sunsetHour);
        ctx.save();
        ctx.strokeStyle = "rgba(255, 87, 34, 0.8)";
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(sunsetX, yAxis.top);
        ctx.lineTo(sunsetX, yAxis.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        // Sunset label
        ctx.fillStyle = "rgba(255, 87, 34, 1)";
        ctx.font = "bold 14px Arial";
        ctx.textAlign = "center";
        ctx.fillText("🌇 SUNSET", sunsetX, yAxis.top - 10);
        ctx.restore();
      }

      // Draw high temperature label
      if (highIndex >= 0 && validTemps.length > 0) {
        const highPoint = chartData[highIndex];
        const highX = xAxis.getPixelForValue(highPoint.x);
        const highY = yAxis.getPixelForValue(highPoint.y);

        ctx.save();
        ctx.fillStyle = "rgba(255, 99, 132, 1)";
        ctx.font = "bold 16px Arial";
        ctx.textAlign = "center";
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 3;
        ctx.strokeText(`${highTemp}°F`, highX, highY - 20);
        ctx.fillText(`${highTemp}°F`, highX, highY - 20);
        ctx.font = "bold 12px Arial";
        ctx.strokeText("HIGH", highX, highY - 35);
        ctx.fillText("HIGH", highX, highY - 35);
        ctx.restore();
      }

      // Draw low temperature label
      if (lowIndex >= 0 && validTemps.length > 0) {
        const lowPoint = chartData[lowIndex];
        const lowX = xAxis.getPixelForValue(lowPoint.x);
        const lowY = yAxis.getPixelForValue(lowPoint.y);

        ctx.save();
        ctx.fillStyle = "rgba(54, 162, 235, 1)";
        ctx.font = "bold 16px Arial";
        ctx.textAlign = "center";
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 3;
        ctx.strokeText(`${lowTemp}°F`, lowX, lowY + 30);
        ctx.fillText(`${lowTemp}°F`, lowX, lowY + 30);
        ctx.font = "bold 12px Arial";
        ctx.strokeText("LOW", lowX, lowY + 45);
        ctx.fillText("LOW", lowX, lowY + 45);
        ctx.restore();
      }
    }, 100);

    // Make sure the chart displays correctly
    canvas.style.height = "300px";
    canvas.style.width = "100%";

    // Store the chart reference
    charts[dayIndex] = currentChart;

    // Restore scroll position to prevent page jumping
    if (typeof currentScrollY !== "undefined") {
      setTimeout(() => window.scrollTo(currentScrollX, currentScrollY), 0);
    }
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
    try {
      if (!hourlyData || hourlyData.length === 0) {
        return [];
      }

      // Use local timezone for consistent date comparison
      const targetDateLocal = new Date(
        targetDate.getFullYear(),
        targetDate.getMonth(),
        targetDate.getDate(),
      );

      const targetDateStr = targetDateLocal.toLocaleDateString("en-CA"); // YYYY-MM-DD format

      console.debug("[DEBUG] Target date:", targetDate);
      console.debug(`[DEBUG] User timezone: ${userTimezone}`);
      console.debug("[DEBUG] Target date in local timezone:", targetDateLocal);
      console.debug("[DEBUG] Target date string:", targetDateStr);
      console.debug("[DEBUG] Total hourly data items:", hourlyData.length);
      console.debug(
        "[DEBUG] First few hourly data items:",
        hourlyData.slice(0, 3),
      );
      const targetDateDay = targetDate.getDate();
      const targetMonth = targetDate.getMonth() + 1; // JavaScript months are 0-indexed

      // Filter data by comparing dates in local timezone
      console.debug("[DEBUG] About to start filtering with .filter() method");
      let filteredData = hourlyData.filter((item) => {
        try {
          if (!item.time) return false;

          // Parse the date from the time field - assume it might be UTC
          const itemDate = new Date(item.time);

          // Check if it's a valid date
          if (isNaN(itemDate.getTime())) {
            console.debug("[DEBUG] Invalid date:", item.time);
            return false;
          }

          // Convert to local timezone for comparison
          const localItemDate = new Date(
            itemDate.toLocaleString("en-US", { timeZone: userTimezone }),
          );

          // Create date strings for comparison (local timezone)
          const itemDateStr = localItemDate.toLocaleDateString("en-CA"); // YYYY-MM-DD format
          const matchesDateStr = itemDateStr === targetDateStr;

          // Compare by day and month as fallback (in local timezone)
          const matchesDay =
            localItemDate.getDate() === targetDateDay &&
            localItemDate.getMonth() + 1 === targetMonth;

          // Only log matches to reduce console spam
          if (matchesDateStr || matchesDay) {
            console.debug(
              `[DEBUG] MATCH: ${item.time}, Item date str: ${itemDateStr}, Target: ${targetDateStr}`,
            );
          }

          return matchesDateStr || matchesDay;
        } catch (e) {
          console.debug("[DEBUG] Error parsing date:", e, item);
          return false;
        }
      });

      console.debug("[DEBUG] Filter method completed successfully");
      console.debug(
        `[DEBUG] Filtered ${filteredData.length} items for ${targetDateStr}`,
      );
      console.debug("[DEBUG] Filtered data items:", filteredData);

      if (filteredData.length === 0) {
        console.debug(
          "[DEBUG] No data found after filtering - checking sample dates:",
        );
        hourlyData.slice(0, 5).forEach((item, index) => {
          if (item.time) {
            const itemDate = new Date(item.time);
            const localItemDate = new Date(
              itemDate.toLocaleString("en-US", { timeZone: userTimezone }),
            );
            const itemDateStr = localItemDate.toLocaleDateString("en-CA");
            console.debug(
              `[DEBUG] Sample ${index}: ${item.time} -> ${itemDateStr} (target: ${targetDateStr})`,
            );
          }
        });
      }

      // If we got results, ensure they're sorted by time and fill gaps for 24-hour coverage
      if (filteredData.length > 0) {
        console.debug(
          `[DEBUG] Successfully filtered ${filteredData.length} data points for date ${targetDateStr}`,
        );

        // Sort by time to ensure proper order
        filteredData.sort((a, b) => new Date(a.time) - new Date(b.time));

        // Ensure we have 24-hour coverage centered around noon
        console.debug(
          "[DEBUG] About to call ensureFullDayCoverage with filtered data:",
          filteredData,
        );
        const fullDayData = ensureFullDayCoverage(filteredData, targetDate);
        console.debug("[DEBUG] ensureFullDayCoverage returned:", fullDayData);
        console.debug(
          `[DEBUG] Returning ${fullDayData ? fullDayData.length : "null"} data points to chart function`,
        );
        return fullDayData;
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

      // Third attempt: if we're showing today (day 0), show the first 24 hours of data
      const localToday = new Date();
      const todayStr = localToday.toLocaleDateString("en-CA");
      if (targetDateStr === todayStr) {
        console.debug(`[DEBUG] Showing today's data (${todayStr})`);
        const dayData = hourlyData.slice(0, Math.min(24, hourlyData.length));
        return ensureFullDayCoverage(dayData, targetDate);
      }

      // Fourth attempt: if we're showing day N, show hours (N*24) through ((N+1)*24)
      // But first convert all times to local timezone to find the right slice
      const dayDiff = Math.floor(
        (targetDate - localToday) / (24 * 60 * 60 * 1000),
      );
      if (dayDiff >= 0 && dayDiff < 5) {
        console.debug(
          `[DEBUG] Attempting day offset method for day difference: ${dayDiff}`,
        );
        const startIndex = Math.min(dayDiff * 24, hourlyData.length - 1);
        const endIndex = Math.min(startIndex + 24, hourlyData.length);
        const dayData = hourlyData.slice(startIndex, endIndex);
        return ensureFullDayCoverage(dayData, targetDate);
      }

      // If all else fails, return empty array
      return [];
    } catch (error) {
      console.error("[ERROR] Exception in filterHourlyDataByDate:", error);
      console.error("[ERROR] Stack trace:", error.stack);
      return [];
    }
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
          console.debug(
            `[DEBUG] Hour ${hour}: Checking item ${item.time} -> itemHour: ${itemHour}, looking for hour: ${hour}, match: ${itemHour === hour}`,
          );
          return itemHour === hour;
        });
      }

      if (existingData) {
        // Use existing data but ensure proper time format
        fullDayData.push({
          time: hourDate.toISOString(),
          temperature: existingData.temperature,
          condition: existingData.condition || "Clear",
          precipitation: existingData.precipitation || 0,
        });
        console.debug(
          `[DEBUG] Hour ${hour}: using existing data (${existingData.temperature}°F, ${existingData.precipitation}% precip)`,
        );
      } else {
        // Create realistic placeholder data
        const baseTemp = 65;
        // Create temperature curve: lowest at 6 AM, highest at 2 PM
        const hourlyVariation = Math.sin(((hour - 14) * Math.PI) / 12) * 15;
        const temperature = Math.round(baseTemp + hourlyVariation);

        fullDayData.push({
          time: hourDate.toISOString(),
          temperature: temperature,
          condition: "Forecast Unavailable",
          precipitation: 0,
        });
        console.debug(
          `[DEBUG] Hour ${hour}: created placeholder (${temperature}°F, 0% precip)`,
        );
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
