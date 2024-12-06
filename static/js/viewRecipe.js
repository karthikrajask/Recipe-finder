// Function to add a recipe to the user's history
function addToHistory(userId, recipe) {
    fetch('/add_to_history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: userId,
            name: recipe.label,
            thumbnail: recipe.image,
            url: recipe.url
        })
    })
    .then(response => response.json())
    .then(data => console.log(data.message))
    .catch(error => console.error('Error adding to history:', error));
}

// Function to fetch and display the user's recipe history
function displayHistory(userId) {
    fetch(`/get_history/${userId}`)
        .then(response => response.json())
        .then(history => {
            const historyContainer = document.getElementById('historyContainer');
            historyContainer.innerHTML = '';  // Clear previous content
            
            if (history.length > 0) {
                history.forEach(item => {
                    const recipeDiv = document.createElement('div');
                    recipeDiv.classList.add('history-item');
                    
                    recipeDiv.innerHTML = `
                        <img src="${item.thumbnail}" alt="${item.name}" class="history-thumbnail">
                        <h3>${item.name}</h3>
                        <a href="${item.url}" target="_blank">View Recipe</a>
                        <p>Viewed on: ${new Date(item.timestamp).toLocaleString()}</p>
                    `;
                    
                    historyContainer.appendChild(recipeDiv);
                });
            } else {
                historyContainer.innerHTML = `<p>No history found.</p>`;
            }
        })
        .catch(error => console.error('Error fetching history:', error));
}

// Call this function when the history page loads
document.addEventListener('DOMContentLoaded', () => {
    displayHistory(userId);  // Now uses the dynamic userId
});
