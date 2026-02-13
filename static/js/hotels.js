const container = document.getElementById("hotelContainer");
const destinationId = DESTINATION_ID; // pass from template

fetch(`/api/hotels/${destinationId}`)
.then(res => res.json())
.then(data => {

    if (data.length === 0) {
        container.innerHTML = "<p>No hotels found</p>";
        return;
    }

    container.innerHTML = "";

    data.forEach(hotel => {

      let imageHTML = `
    <img src="/static/images/hotel_default.jpg" 
         class="hotel-img" 
         alt="hotel image">
`;

        let amenitiesHTML = hotel.amenities.length > 0
            ? hotel.amenities.join(", ")
            : "Basic Amenities";

        const card = document.createElement("div");
        card.className = "hotel-card";

        card.innerHTML = `
            <div class="image-wrapper">
                ${imageHTML}
            </div>

            <div class="hotel-info">
                <h3>${hotel.hotel}</h3>
                <p>⭐ ${hotel.stars} Rating</p>
                <p>💰 ₹${hotel.price} per night</p>
                <p>🛏 ${hotel.available_rooms} Rooms Available</p>
                <p>🏨 ${amenitiesHTML}</p>

                <a href="/book-hotel/${hotel.id}" class="book-btn">
                    Book Now
                </a>
            </div>
        `;

        container.appendChild(card);
    });

})
.catch(err => {
    console.error(err);
    container.innerHTML = "<p>Error loading hotels</p>";
});
