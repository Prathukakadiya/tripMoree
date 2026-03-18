// JS loaded check
document.addEventListener("DOMContentLoaded", () => {
    console.log("destinations.js loaded successfully");
});

// vacation type click પર destinations load થાય
function loadDestinations(vacationType) {
    const container = document.getElementById("destinations-container");

    container.innerHTML = "<p class='loading'>Loading destinations...</p>";

    fetch(`/api/destinations?vacation_type=${vacationType}`)
        .then(response => response.json())
        .then(data => {
            container.innerHTML = "";

            if (data.length === 0) {
                container.innerHTML = "<p class='no-results'>No destinations found</p>";
                return;
            }

            data.forEach(dest => {
                const card = document.createElement("div");
                card.className = "destination-card";

                card.innerHTML = `
                    <img src="/static/${dest.image}" alt="${dest.name}">
                    <div class="destination-info">
                        <h2>${dest.name}</h2>
                        <p><b>Category:</b> ${dest.category}</p>
                        <p><b>Country:</b> ${dest.country_type}</p>
                        <p><b>Vacation:</b> ${dest.vacation_type}</p>
                        <a href="/login" class="explore-btn">Explore</a>
                    </div>
                `;

                container.appendChild(card);
            });
        })
        .catch(error => {
            console.error(error);
            container.innerHTML = "<p>Error loading destinations</p>";
        });
}
