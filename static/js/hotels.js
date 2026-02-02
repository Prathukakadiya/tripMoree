const container = document.getElementById("hotelContainer");

// Goa destination_id = 1
fetch("/api/compare_hotels/1")
.then(res => res.json())
.then(data => {

    if (data.length === 0) {
        container.innerHTML = "<p>No hotels found</p>";
        return;
    }

    data.forEach(hotel => {

        let imagesHTML = "";
        hotel.images.forEach(img => {
            imagesHTML += `<img src="${img}" alt="hotel image">`;
        });

        let amenitiesHTML = hotel.amenities.join(", ");

        container.innerHTML += `
            <div class="hotel-card">
                <div class="hotel-images">
                    ${imagesHTML}
                </div>

                <div class="hotel-info">
                    <h3>${hotel.hotel}</h3>
                    <p>⭐ Rating: ${hotel.rating}</p>
                    <p>💰 Price: ₹${hotel.price}</p>
                    <p>🛏 Available Rooms: ${hotel.available_rooms}</p>
                    <p>🏨 Amenities: ${amenitiesHTML}</p>
                    <p class="score">Score: ${hotel.score}</p>
                </div>
            </div>
        `;
    });
})
.catch(err => {
    console.error(err);
    container.innerHTML = "<p>Error loading hotels</p>";
});
