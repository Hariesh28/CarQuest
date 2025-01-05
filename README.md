# CarQuest

CarQuest is a web-based project designed to scrape data about cars and store it in a MySQL database. The goal is to create a streamlined solution for managing and filtering car listings. Additionally, a Streamlit UI is planned for visualizing and filtering the car data, along with a chatbot for enhanced interaction.

## Features

- **Web Scraping**: Collects car data from various sources.
- **Database Storage**: Stores car data in a MySQL database.
- **Streamlit UI**: Provides a user-friendly interface for filtering and viewing car data.
- **AI Chatbot**: Assists users in querying the database and suggesting car options.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Hariesh28/CarQuest.git
   cd CarQuest
   ```

2. **Set up the MySQL Database**:
   - Ensure MySQL is installed and a database is created.
   - Update the database credentials in the `config.py` file.

3. **Dependencies**:
   - Install the required Python packages:
     ```bash
     pip install -r requirements.txt
     ```

4. **Run the Web Scraper**:
   - Execute the scraping script to collect car data:
     ```bash
     python scrape_data.py
     ```

5. **Run the Streamlit App**:
   - Launch the Streamlit app for UI interaction:
     ```bash
     streamlit run app.py
     ```

6. **AI Chatbot**:
   - Train and deploy the AI chatbot to interact with the database:
     ```bash
     python chatbot.py

## Usage

1. **Scraping**:
   - Scrape car data using the specified scraping script.

2. **Database Interaction**:
   - Use SQL queries to manage and retrieve car data from the MySQL database.

3. **Streamlit UI**:
   - Access the Streamlit application to filter and view car listings.

4. **AI Chatbot**:
   - Engage with the chatbot to filter cars and suggest options based on user preferences.

## Contributing

Contributions to CarQuest are welcome! Feel free to fork the repository, create branches, and submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
