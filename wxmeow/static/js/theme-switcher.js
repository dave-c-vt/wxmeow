/**
 * Theme Switcher for wxmeow
 *
 * Handles theme switching between light and dark modes and saves
 * user preferences to localStorage.
 */

document.addEventListener("DOMContentLoaded", function () {
  // Get theme toggle checkbox
  const themeToggle = document.getElementById("theme-toggle");
  if (!themeToggle) return;

  // Get theme from cookie
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
    return null;
  }

  // Check for saved user preference, if any
  const savedTheme = getCookie("theme");
  const prefersDark =
    window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;

  // Set initial theme based on preference or system setting
  if (savedTheme === "dark" || (!savedTheme && prefersDark)) {
    document.documentElement.setAttribute("data-theme", "dark");
    themeToggle.checked = true;
  } else {
    document.documentElement.setAttribute("data-theme", "light");
    themeToggle.checked = false;
  }

  // Listen for toggle change
  themeToggle.addEventListener("change", function () {
    const theme = this.checked ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", theme);

    // Update cookie via API endpoint
    fetch(`/set-theme/${theme}`).catch((error) =>
      console.error("Error setting theme:", error),
    );

    updateToggleIcons(theme);
  });

  // Update the toggle icons based on theme
  function updateToggleIcons(theme) {
    const sunIcon = document.getElementById("theme-icon-sun");
    const moonIcon = document.getElementById("theme-icon-moon");

    if (theme === "dark") {
      if (sunIcon) sunIcon.style.opacity = "0.5";
      if (moonIcon) moonIcon.style.opacity = "1";
    } else {
      if (sunIcon) sunIcon.style.opacity = "1";
      if (moonIcon) moonIcon.style.opacity = "0.5";
    }
  }

  // Set initial icon states
  updateToggleIcons(
    savedTheme === "dark" || (!savedTheme && prefersDark) ? "dark" : "light",
  );

  // Update theme if system preference changes
  if (window.matchMedia) {
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", (e) => {
        if (!getCookie("theme")) {
          // Only if user hasn't set preference
          const theme = e.matches ? "dark" : "light";
          document.documentElement.setAttribute("data-theme", theme);
          themeToggle.checked = e.matches;
          updateToggleIcons(theme);

          // Update cookie via API endpoint
          fetch(`/set-theme/${theme}`).catch((error) =>
            console.error("Error setting theme:", error),
          );
        }
      });
  }
});
