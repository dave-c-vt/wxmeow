/**
 * Location Autocomplete
 *
 * Provides autocomplete functionality for location input fields.
 * Queries the server for location suggestions as the user types.
 */

document.addEventListener("DOMContentLoaded", function () {
  // Get the location input element
  const locationInput = document.getElementById("location");
  if (!locationInput) return;

  // Create and append the dropdown container
  const dropdownContainer = document.createElement("div");
  dropdownContainer.id = "location-dropdown";
  dropdownContainer.className = "autocomplete-dropdown";
  locationInput.parentNode.appendChild(dropdownContainer);

  // Keep track of the currently selected suggestion
  let currentSelection = -1;
  // Minimum characters before suggestions appear
  const minChars = 3;
  // Delay between keystrokes before sending API request (ms)
  const debounceDelay = 300;
  let debounceTimer;

  // Function to fetch location suggestions
  async function fetchSuggestions(query) {
    try {
      if (query.length < minChars) {
        hideDropdown();
        return;
      }

      const response = await fetch(
        `/api/locations/suggest?q=${encodeURIComponent(query)}`,
      );
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const suggestions = await response.json();
      displaySuggestions(suggestions);
    } catch (error) {
      console.error("Error fetching location suggestions:", error);
      hideDropdown();
    }
  }

  // Function to display suggestions in the dropdown
  function displaySuggestions(suggestions) {
    // Clear previous suggestions
    dropdownContainer.innerHTML = "";

    // Add debug info to console
    console.debug(
      `Got ${suggestions ? suggestions.length : 0} suggestions for query: "${locationInput.value}"`,
    );
    if (suggestions && suggestions.length > 0) {
      console.debug("First suggestion:", suggestions[0]);
    }

    // Hide dropdown if no suggestions
    if (!suggestions || suggestions.length === 0) {
      hideDropdown();
      return;
    }

    // Create and append suggestion items
    suggestions.forEach((suggestion, index) => {
      const item = document.createElement("div");
      item.className = "autocomplete-item";
      item.textContent = suggestion.label;
      item.setAttribute("data-value", suggestion.value);
      item.setAttribute("data-lat", suggestion.lat);
      item.setAttribute("data-lon", suggestion.lon);

      // Handle click on suggestion
      item.addEventListener("click", () => {
        locationInput.value = suggestion.label;
        hideDropdown();
      });

      // Handle mouse hover
      item.addEventListener("mouseover", () => {
        clearSelection();
        currentSelection = index;
        item.classList.add("selected");
      });

      dropdownContainer.appendChild(item);
    });

    // Show dropdown
    dropdownContainer.style.display = "block";

    // Position the dropdown
    positionDropdown();
  }

  // Function to position the dropdown below the input
  function positionDropdown() {
    const inputRect = locationInput.getBoundingClientRect();
    dropdownContainer.style.width = `${inputRect.width}px`;
    dropdownContainer.style.top = `${inputRect.bottom}px`;
    dropdownContainer.style.left = `${inputRect.left}px`;
  }

  // Function to hide the dropdown
  function hideDropdown() {
    dropdownContainer.style.display = "none";
    currentSelection = -1;
    console.debug("Hiding autocomplete dropdown");
  }

  // Function to clear selection highlighting
  function clearSelection() {
    const items = dropdownContainer.querySelectorAll(".autocomplete-item");
    items.forEach((item) => {
      item.classList.remove("selected");
    });
  }

  // Function to select a suggestion by index
  function selectSuggestion(index) {
    clearSelection();

    const items = dropdownContainer.querySelectorAll(".autocomplete-item");
    if (index >= 0 && index < items.length) {
      currentSelection = index;
      const selectedItem = items[index];
      selectedItem.classList.add("selected");
      // Ensure the selected item is visible in the dropdown
      selectedItem.scrollIntoView({ block: "nearest" });
    }
  }

  // Function to handle input changes with debounce
  function handleInput() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const query = locationInput.value.trim();
      if (query.length >= minChars) {
        console.debug(`Searching for: "${query}"`);
        fetchSuggestions(query);
      } else {
        hideDropdown();
      }
    }, debounceDelay);
  }

  // Function to handle keyboard navigation
  function handleKeydown(e) {
    const items = dropdownContainer.querySelectorAll(".autocomplete-item");

    // If dropdown is not displayed, don't handle navigation keys
    if (dropdownContainer.style.display !== "block") return;

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        selectSuggestion(
          currentSelection < items.length - 1 ? currentSelection + 1 : 0,
        );
        break;

      case "ArrowUp":
        e.preventDefault();
        selectSuggestion(
          currentSelection > 0 ? currentSelection - 1 : items.length - 1,
        );
        break;

      case "Enter":
        e.preventDefault();
        if (currentSelection >= 0 && currentSelection < items.length) {
          const selectedItem = items[currentSelection];
          locationInput.value = selectedItem.textContent;
          hideDropdown();
        }
        break;

      case "Escape":
        hideDropdown();
        break;
    }
  }

  // Add event listeners
  locationInput.addEventListener("input", handleInput);
  locationInput.addEventListener("keydown", handleKeydown);
  locationInput.addEventListener("focus", handleInput);

  // Close dropdown when clicking outside
  document.addEventListener("click", (e) => {
    if (
      e.target !== locationInput &&
      e.target !== dropdownContainer &&
      !dropdownContainer.contains(e.target)
    ) {
      hideDropdown();
    }
  });

  // Handle window resize
  window.addEventListener("resize", () => {
    if (dropdownContainer.style.display === "block") {
      positionDropdown();
    }
  });
});
