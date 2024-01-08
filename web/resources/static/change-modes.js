function changeMode(selectElement) {
    var selectedMode = selectElement.value;

    if (selectedMode === "auto") {
      window.location.href = "index.html";
    } else if (selectedMode === "manual") {
      window.location.href = "manual.html";
    }
  }