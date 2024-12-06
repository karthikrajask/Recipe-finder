// Declare a global variable to store recipe data
let recipes = [];

// DOM elements
const searchInput = document.querySelector('#searchInput');
const resultsList = document.querySelector('#results');
const searchButton = document.querySelector("#searchButton");
const messageDiv = document.querySelector("#message");  // Ensure this references the message div

// Replace with your Edamam API credentials
const APP_ID = 'f545a297';  // Your App ID
const APP_KEY = '1c1bc6e486559526452b56cfbe6a3e78';  // Your App Key

// Event listener for search button click
searchButton.addEventListener('click', (e) => {
    e.preventDefault();
    searchRecipes();
});

// Function to fetch and display recipes
async function searchRecipes() {
    const searchValue = searchInput.value.trim();

    // Clear previous results and messages
    resultsList.innerHTML = '';
    messageDiv.textContent = '';  // Clear any previous messages

    // Input validation
    if (searchValue === '') {
        messageDiv.textContent = 'Please enter a food or ingredient to search.';
        return;
    }

    // Show loading message
    messageDiv.textContent = 'Searching...';

    try {
        const response = await fetch(`https://api.edamam.com/search?q=${searchValue}&app_id=${APP_ID}&app_key=${APP_KEY}&from=0&to=20`);
        if (!response.ok) throw new Error('Network response was not ok');
        
        const data = await response.json();

        // Store fetched recipes in the global variable
        recipes = data.hits;

        // Check if any recipes were found
        if (recipes.length === 0) {
            messageDiv.textContent = 'No recipes found. Please try a different search term.';
        } else {
            displayRecipes(recipes);
            messageDiv.textContent = '';  // Clear the loading message
        }
    } catch (error) {
        messageDiv.textContent = 'An error occurred while fetching recipes. Please try again.';
        console.error('Error fetching recipes:', error);
    }
}

// Function to display recipes
function displayRecipes(recipes) {
    let html = '';

    recipes.forEach((recipe, index) => {
        html += `
        <li class="recipe-item">
            <div>
                <img src="${recipe.recipe.image}" alt="${recipe.recipe.label}">
                <h3>${recipe.recipe.label}</h3>
            </div>
            <div class="recipe-link">
                <a href="${recipe.recipe.url}" target="_blank">View Recipe</a>
            </div>
            <div class="recipe-instructions">
                <button class="get-instructions" data-index="${index}">Get Instructions</button>
            </div>
        </li>
        `;
    });

    resultsList.innerHTML = html;

    // Attach event listeners to all "Get Instructions" buttons
    document.querySelectorAll('.get-instructions').forEach(button => {
        button.addEventListener('click', () => getInstructions(button.getAttribute('data-index')));
    });
}

// Function to fetch instructions and store in session storage
async function getInstructions(index) {
    const recipe = recipes[index].recipe;

    // Store basic recipe details in sessionStorage
    sessionStorage.setItem('recipeImage', recipe.image);
    sessionStorage.setItem('recipeLabel', recipe.label);
    sessionStorage.setItem('recipeIngredients', JSON.stringify(recipe.ingredientLines));

    try {
        // Fetch detailed instructions from your backend server
        const response = await fetch(`/get-instructions?recipeLabel=${encodeURIComponent(recipe.label)}`);
        const data = await response.json();

        sessionStorage.setItem('recipeInstructions', JSON.stringify([data.instructions]));

        // Redirect to the instruction page
        window.location.href = '/recipe';
    } catch (error) {
        console.error('Error fetching recipe instructions:', error);
        sessionStorage.setItem('recipeInstructions', JSON.stringify(['Instructions not available.']));
        window.location.href = '/recipe';
    }
}

