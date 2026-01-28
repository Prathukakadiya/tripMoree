let DEST_CACHE = {};
const container = document.getElementById("destinations-container");
const searchInput = document.getElementById("searchInput");

// Load by vacation type
function loadDestinations(vacationType) {

    if (DEST_CACHE[vacationType]) {
        renderDestinations(DEST_CACHE[vacationType]);
        return;
    }

    container.innerHTML = "<p class='loading'>Loading destinations...</p>";

    fetch(`/api/destinations?vacation_type=${vacationType}`)
        .then(res => res.json())
        .then(data => {
            DEST_CACHE[vacationType] = data;
            renderDestinations(data);
        })
        .catch(() => {
            container.innerHTML = "<p>Error loading destinations</p>";
        });
}

// Load all destinations
function loadAllDestinations() {
    container.innerHTML = "<p class='loading'>Loading destinations...</p>";

    fetch("/api/destinations")
        .then(res => res.json())
        .then(data => {
            DEST_CACHE["all"] = data;
            renderDestinations(data);
        });
}

// Search
function searchDestinations() {
    const query = searchInput.value.toLowerCase();

    fetch("/api/destinations")
        .then(res => res.json())
        .then(data => {
            const filtered = data.filter(dest =>
                dest.name.toLowerCase().includes(query)
            );
            renderDestinations(filtered);
        });
}

// Render cards
function renderDestinations(data) {
    container.innerHTML = "";

    if (data.length === 0) {
        container.innerHTML = "<p class='no-results'>No destinations found</p>";
        return;
    }

    data.forEach(dest => {
        const card = document.createElement("div");
        card.className = "destination-card";

        card.innerHTML = `
            <div class="image-wrapper">
                <img src="${dest.image}" alt="${dest.name}">
                <div class="overlay">
                    <h2>${dest.name}</h2>
                </div>
            </div>
            <div class="destination-info">
                <p><b>Category:</b> ${dest.category}</p>
                <p><b>Country:</b> ${dest.country_type}</p>
                <p><b>Vacation:</b> ${dest.vacation_type}</p>
                <a href="/login" class="explore-btn">Explore</a>
            </div>
        `;

        container.appendChild(card);
    });
}

// Initial load
document.addEventListener("DOMContentLoaded", loadAllDestinations);
