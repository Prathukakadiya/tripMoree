const container = document.getElementById("destinations-container");
const searchInput = document.getElementById("searchInput");

/* Load all on page load */
document.addEventListener("DOMContentLoaded", loadAllDestinations);

/* Load by vacation type */
function loadDestinations(type) {
    container.innerHTML = "<p class='loading'>Loading...</p>";

    fetch(`/api/destinations?type=${type}`)   // ✅ CHANGE HERE
        .then(res => res.json())
        .then(renderCards);
}

/* Load all */
function loadAllDestinations() {
    container.innerHTML = "<p class='loading'>Loading...</p>";

    fetch("/api/destinations")
        .then(res => res.json())
        .then(renderCards);
}

/* Search */
function searchDestinations() {
    const query = searchInput.value.toLowerCase();

    fetch("/api/destinations")
        .then(res => res.json())
        .then(data => {
            const filtered = data.filter(d =>
                d.name.toLowerCase().includes(query)
            );
            renderCards(filtered);
        });
}

/* Render cards */
function renderCards(data) {
    container.innerHTML = "";

    if (!data.length) {
        container.innerHTML = "<p class='no-results'>No destinations found</p>";
        return;
    }

    data.forEach(dest => {
        const card = document.createElement("div");
        card.className = "destination-card";

        card.style.cursor = "pointer";
        card.addEventListener("click", () => {
            window.location.href = `/hotels/${dest.id}`;
        });

        card.innerHTML = `
            <div class="image-wrapper">
                <img src="${dest.image}" alt="${dest.name}">
            </div>

            <div class="destination-info">
                <div class="location">
                    <span>📍 ${dest.name}</span>
                    <span class="rating">⭐ ${dest.rating}</span>
                </div>

                <div class="best-time">
                    Best Time: ${dest.best_time}
                </div>

                <div class="tags">
                    ${dest.category} • ${dest.country_type} • ${dest.vacation_type}
                </div>
            </div>
        `;

        container.appendChild(card);
    });
}
