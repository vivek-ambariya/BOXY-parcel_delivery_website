# Boxy - Parcel Delivery Website

A modern, responsive parcel delivery website built with Flask, Bootstrap 5, and vanilla JavaScript.

## Project Structure

```
quickparcel/
│
├── app.py                 # Flask application
├── requirements.txt        # Python dependencies
├── templates/
│   ├── base.html          # Base template with Bootstrap 5
│   └── index.html         # Home page template
├── static/
│   ├── css/
│   │   └── style.css      # Custom styles
│   ├── js/
│   │   └── main.js        # Custom JavaScript
│   └── images/            # Image assets
└── README.md              # This file
```

## Features

- **Modern Design**: Clean, professional logistics/SaaS look
- **Responsive**: Mobile-first design with Bootstrap 5
- **Smooth Animations**: Card hover effects and scroll animations
- **Interactive Navbar**: Active link highlighting and smooth scrolling
- **Google Maps Integration**: 
  - Address autocomplete for faster input
  - Visual map display for tracking deliveries
  - Route visualization for multi-stop deliveries
  - Partner navigation interface
- **Sections Included**:
  - Hero section with stats
  - Why Choose Boxy (features)
  - How It Works (3-step process)
  - Services section
  - Trust statistics
  - Call-to-action sections
  - Partner section
  - Footer with links and contact info

## Installation & Setup

1. **Install Python 3.10+** (if not already installed)

2. **Navigate to the project directory**:
   ```bash
   cd quickparcel
   ```

3. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   **If you get errors, try these solutions:**
   
   - **"No module named 'requests'"**: `pip install requests`
   - **"No module named 'mysql'"**: `pip install mysql-connector-python`
   - **Permission errors**: Use virtual environment (see below)
   - **pip not found**: Use `pip3` or `python3 -m pip`
   
   **Using virtual environment (Recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Set up Google Maps API** (Optional but Recommended):
   
   To enable Google Maps features (address autocomplete, map visualization, route display, and pricing calculations):
   
   a. **Get a Google Maps API Key**:
      - Go to [Google Cloud Console](https://console.cloud.google.com/)
      - Create a new project or select an existing one
      - Enable these APIs (all use the same API key):
        - **Maps JavaScript API** - For map display and visualization
        - **Places API** - For address autocomplete
        - **Geocoding API** - For converting addresses to coordinates
        - **Directions API** - For route visualization
        - **Distance Matrix API** - For calculating distances for pricing
      - Create credentials (API Key)
      - Restrict the API key to your domain (recommended for production)
   
   b. **Add API Key to Environment**:
      - Create a `.env` file in the project root directory
      - Add your API key (one key works for all Google Maps features):
        ```
        GOOGLE_MAPS_API_KEY=your_api_key_here
        ```
      - Or set it as an environment variable:
        ```bash
        export GOOGLE_MAPS_API_KEY=your_api_key_here
        ```
   
   **Note**: 
   - Without the API key, the application will work but Google Maps features will be disabled
   - The same API key is used for both frontend (maps, autocomplete) and backend (distance calculations for pricing)
   - All 5 APIs listed above must be enabled for full functionality

6. **Run the application**:
   ```bash
   python app.py
   ```

7. **Open your browser** and navigate to:
   ```
   http://localhost:8000
   ```

## Technologies Used

- **Backend**: Python 3.10+, Flask 3.0.0
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Framework**: Bootstrap 5.3.2 (via CDN)
- **Icons**: Font Awesome 6.5.1 (via CDN)
- **Maps**: Google Maps JavaScript API (with Places, Geocoding, Directions, Distance Matrix)

## Development

The application runs in debug mode by default. To disable debug mode, edit `app.py` and change:
```python
app.run(debug=True, host='0.0.0.0', port=8000)
```
to:
```python
app.run(debug=False, host='0.0.0.0', port=8000)
```

## Customization

- **Colors**: Edit CSS variables in `static/css/style.css` (root `:root` selector)
- **Content**: Edit `templates/index.html` for page content
- **Styles**: Edit `static/css/style.css` for custom styling
- **Interactions**: Edit `static/js/main.js` for JavaScript functionality

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

© 2025 Boxy. All rights reserved.

