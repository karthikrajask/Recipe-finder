from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
import datetime
import re
import os
import requests
from bson.objectid import ObjectId

app = Flask(__name__)

# Secret key for session management
app.secret_key = os.urandom(24)

# MongoDB configurations
app.config['MONGO_URI'] = 'mongodb+srv://recipe:admin123@recipe.z5tsy.mongodb.net/recipe?retryWrites=true&w=majority'
mongo = PyMongo(app)

# API credentials
GROQ_API_KEY = "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"
APP_ID = "f545a297"
APP_KEY = "1c1bc6e486559526452b56cfbe6a3e78"

# Test MongoDB connection route
@app.route('/test_connection')
def test_connection():
    try:
        sample_data = mongo.db.recipe.find_one()
        if sample_data:
            return f"Connection successful! Sample data: {sample_data}"
        else:
            return "Connection successful! But no data found in the 'recipe' collection."
    except Exception as e:
        return f"Error connecting to MongoDB: {e}"

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Route to handle contact form submission
@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    # Store or process the form data as needed
    print(f"Received contact form submission from {name} ({email}): {message}")
    return redirect(url_for('contact'))


# Route for viewing user history
@app.route('/history')
def history():
    if 'loggedin' in session:
        user_id = session['id']  # Get the user ID from the session
        history_records = mongo.db.recipe_history.find({'user_id': user_id}).sort('viewed_at', -1)
        viewed_recipes = [
            {
                'recipe_name': record['recipe_name'],
                'viewed_at': record['viewed_at'].strftime('%Y-%m-%d %H:%M:%S')
            }
            for record in history_records
        ]
        return render_template('history.html', viewed_recipes=viewed_recipes, user_id=user_id)  # Pass user_id to the template
    return redirect(url_for('login'))


# Route for recording a viewed recipe in history
@app.route('/view_recipe', methods=['POST'])
def view_recipe():
    if 'loggedin' in session:
        recipe_id = request.json.get('recipe_id')
        user_id = session['id']

        recipe_data = mongo.db.recipes.find_one({'_id': ObjectId(recipe_id)})
        
        if recipe_data:
            mongo.db.recipe_history.insert_one({
                'user_id': user_id,
                'recipe_name': recipe_data['name'],
                'viewed_at': datetime.datetime.now()
            })
            return jsonify(success=True)
    
    return jsonify(success=False, error="Unauthorized or recipe not found"), 403

# User login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        print(f"Attempting login with username: {username} and password: {password}")
        
        user = mongo.db.users.find_one({'username': username, 'password': password})
        if user:
            session['loggedin'] = True
            session['id'] = str(user['_id'])
            session['username'] = user['username']
            print("Login successful. Redirecting to home.")
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username or password!'
            print("Login failed. Incorrect credentials.")
    return render_template('login.html', msg=msg)

# User signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        existing_user = mongo.db.users.find_one({'username': username})
        
        if existing_user:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        else:
            mongo.db.users.insert_one({'username': username, 'email': email, 'password': password})
            return redirect(url_for('login'))
    return render_template('signup.html', msg=msg)

# User logout route
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# Home route
@app.route('/')
def home():
    if 'loggedin' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))

# Pantry route
@app.route('/pantry')
def pantry():
    if 'loggedin' in session:
        return render_template('pantry.html')
    return redirect(url_for('login'))

# Recipe route
@app.route('/recipe')
def recipe():
    if 'loggedin' in session:
        return render_template('recipe.html')
    return redirect(url_for('login'))

# Fetch a static list of ingredients for the pantry feature
@app.route('/get_ingredients', methods=['GET'])
def get_ingredients():
    if 'loggedin' in session:
        ingredients_list = ["rice", "tomato", "potato", "honey", "onion", "garlic", "chicken"]
        return jsonify({"ingredients": ingredients_list})
    return jsonify({"error": "Unauthorized"}), 403

# Fetch recipes based on ingredients and optional diet preference
@app.route('/get_recipes', methods=['POST'])
def get_recipes():
    if 'loggedin' in session:
        ingredients = request.json.get('ingredients', [])
        diet = request.json.get('diet', '')
        api_url = f"https://api.edamam.com/search?q={','.join(ingredients)}&app_id={APP_ID}&app_key={APP_KEY}&from=0&to=20"
        if diet:
            api_url += f"&health={diet}"
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching recipes: {e}")
            return jsonify({"error": "Unable to fetch recipes"}), 500
    return jsonify({"error": "Unauthorized"}), 403

# Fetch instructions from the Groq API for a specific recipe
@app.route('/get-instructions', methods=['GET'])
def get_instructions():
    if 'loggedin' in session:
        recipe_label = request.args.get('recipeLabel')
        try:
            groq_api_url = 'https://api.groq.com/v1/chat/completions'
            response = requests.post(
                groq_api_url,
                json={
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Provide cooking instructions for the recipe: {recipe_label}"
                        }
                    ],
                    "model": "llama3-8b-8192"
                },
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}'
                }
            )
            if response.status_code == 200:
                data = response.json()
                instructions = data.get('choices', [{}])[0].get('message', {}).get('content', 'Instructions not available.')
                return jsonify(instructions=instructions)
            else:
                return jsonify(instructions='Instructions not available'), 500
        except Exception as e:
            print(f"Error fetching from Groq API: {e}")
            return jsonify(instructions='Instructions not available'), 500
    return jsonify({"error": "Unauthorized"}), 403

if __name__ == '__main__':
    app.run(debug=True, port=5001)
