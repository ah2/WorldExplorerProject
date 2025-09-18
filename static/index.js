document.addEventListener("DOMContentLoaded", async () => {
  const countrySelect = document.getElementById("country-select");
  const citySelect = document.getElementById("city-select");
  const startBtn = document.getElementById("start-btn");
  const userSpan = document.getElementById("user-span");

  let selectedCity = null;

  // --- Load logged-in user ---
  async function loadUser() {
    try {
      const res = await fetch("/api/session");
      const data = await res.json();
      userSpan.textContent = data.user || "Guest";
    } catch (err) {
      console.error("Error fetching user:", err);
    }
  }

  // --- Fetch countries ---
  async function loadCountries() {
    try {
      const res = await fetch("/api/countries");
      const data = await res.json();
      data.forEach(country => {
        const opt = document.createElement("option");
        opt.value = country.iso_code;
        opt.textContent = country.name;
        countrySelect.appendChild(opt);
      });
    } catch (err) {
      console.error("Error fetching countries:", err);
    }
  }

  // --- Fetch cities ---
  async function loadCities(countryCode) {
    citySelect.innerHTML = '<option value="">-- Select a city --</option>';
    citySelect.disabled = true;

    try {
      const res = await fetch(`/api/cities?country=${countryCode}`);
      const data = await res.json();

      data.forEach(city => {
        const opt = document.createElement("option");
        opt.value = JSON.stringify({
          name: city.name,
          lat: city.lat,
          lng: city.lng
        });
        opt.textContent = city.name;
        citySelect.appendChild(opt);
      });

      citySelect.disabled = false;
    } catch (err) {
      console.error("Error fetching cities:", err);
    }
  }

  // --- Event listeners ---
  countrySelect.addEventListener("change", e => {
    if (e.target.value) {
      loadCities(e.target.value);
    } else {
      citySelect.innerHTML = '<option value="">-- Select a city --</option>';
      citySelect.disabled = true;
    }
    startBtn.disabled = true;
  });

  citySelect.addEventListener("change", e => {
    if (e.target.value) {
      selectedCity = JSON.parse(e.target.value);
      startBtn.disabled = false;
    } else {
      selectedCity = null;
      startBtn.disabled = true;
    }
  });

  startBtn.addEventListener("click", async () => {
    if (!selectedCity) return;
    const res = await fetch("/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(selectedCity)
    });
    const data = await res.json();
    console.log("Game started at:", data);
    // optionally redirect to /map
    window.location.href = "/map";
  });

  // --- Init ---
  loadUser();
  loadCountries();
});
