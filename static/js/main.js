window.addEventListener("DOMContentLoaded", function () {
  console.log("DOMContentLoaded");
  // save theme
  document.querySelectorAll(".theme-controller").forEach((el) => {
    el.addEventListener("change", (e) => {
      console.log("change", e.target.value);
      const theme = e.target.value;
      document.documentElement.setAttribute("data-theme", theme);
      localStorage.setItem("theme", theme);
      console.log("saved theme", theme);
    });
  });

  // load theme
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme) {
    console.log("loaded theme", savedTheme);
    document.documentElement.setAttribute("data-theme", savedTheme);
    document.querySelector(".theme-controller").value = savedTheme;
  }
});
