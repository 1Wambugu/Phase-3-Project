import argparse
import pyfiglet
from simple_chalk import chalk
import requests
import sqlite3

# Add the following constants
API_KEY = "05259ef00cb050bde695717630c0c454"

WEATHER_ICONS = {
    "01d": "☀️",
    "02d": "⛅️",
    "03d": "☁️",
    "04d": "☁️",
    "09d": "🌧",
    "10d": "🌦",
    "11d": "⛈",
    "13d": "🌨",
    "50d": "🌫",
    "01n": "🌙",
    "02n": "☁️",
    "03n": "☁️",
    "04n": "☁️",
    "09n": "🌧",
    "10n": "🌦",
    "11n": "⛈",
    "13n": "🌨",
    "50n": "🌫",
}

class WeatherDatabase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.create_tables()

    def create_tables(self):
        # Create necessary tables: cities, weather_data
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY,
                name TEXT,
                country TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_data (
                id INTEGER PRIMARY KEY,
                city_id INTEGER,
                temperature REAL,
                feels_like REAL,
                description TEXT,
                icon TEXT,
                FOREIGN KEY(city_id) REFERENCES cities(id)
            )
        ''')
        self.conn.commit()

    def add_city(self, name, country):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO cities (name, country) VALUES (?, ?)", (name, country))
        self.conn.commit()
        return cursor.lastrowid

    def add_weather_data(self, city_id, temperature, feels_like, description, icon):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO weather_data (city_id, temperature, feels_like, description, icon) VALUES (?, ?, ?, ?, ?)",
                       (city_id, temperature, feels_like, description, icon))
        self.conn.commit()

    def get_city_id(self, name, country):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM cities WHERE name = ? AND country = ?", (name, country))
        city = cursor.fetchone()
        return city[0] if city else None

    def get_weather_data(self, city_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM weather_data WHERE city_id = ?", (city_id,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()

class WeatherApp:
    def __init__(self, db_file, api_key):
        self.db = WeatherDatabase(db_file)
        self.api_key = api_key
        self.BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def fetch_weather_data(self, city_name):
        url = f"{self.BASE_URL}?q={city_name}&appid={self.api_key}&units=metric"
        response = requests.get(url)
        if response.status_code != 200:
            print(chalk.red("Error: Unable to retrieve weather information."))
            return None
        return response.json()

    def run(self, city_name):
        city_data = self.fetch_weather_data(city_name)
        if not city_data:
            return

        city = city_data["name"]
        country = city_data["sys"]["country"]
        temperature = city_data["main"]["temp"]
        feels_like = city_data["main"]["feels_like"]
        description = city_data["weather"][0]["description"]
        icon = city_data["weather"][0]["icon"]

        city_id = self.db.get_city_id(city, country)
        if not city_id:
            city_id = self.db.add_city(city, country)

        self.db.add_weather_data(city_id, temperature, feels_like, description, icon)

        weather_icon = WEATHER_ICONS.get(icon, "")
        output = f"{pyfiglet.figlet_format(city)}, {country}\n\n"
        output += f"{weather_icon} {description}\n"
        output += f"Temperature: {temperature}°C\n"
        output += f"Feels like: {feels_like}°C\n"
        print(chalk.green(output))

    def close(self):
        self.db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check the weather for a certain country/city.")
    parser.add_argument("city_name", help="the city to check the weather for")
    args = parser.parse_args()

    api_key = "05259ef00cb050bde695717630c0c454"
    db_file = "weather_data.db"
    app = WeatherApp(db_file, api_key)
    app.run(args.city_name)
    app.close()
