# Toyota Bil Analyzer

## Overview
The Toyota Bil Analyzer is a web application built using Streamlit that allows users to analyze car data from Finn.no. It fetches car listings, parses the relevant information, and provides insights and recommendations based on the data. The application also integrates AI analysis to enhance user experience and provide valuable recommendations.

## Project Structure
```
toyota-bil-analyzer
├── app.py                # Main application logic for the Streamlit interface
├── main.py               # Functions for fetching and parsing car data
├── requirements.txt      # Python dependencies for the project
├── .env                  # Environment variables, including API keys
├── Dockerfile            # Docker image definition for the application
├── docker-compose.yaml    # Configuration for multi-container Docker applications
├── .gitignore            # Files and directories to be ignored by Git
└── README.md             # Documentation for the project
```

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Docker and Docker Compose installed

### Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd toyota-bil-analyzer
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the root directory and add your API keys and other sensitive information.

### Running the Application
To run the application locally, use the following command:
```
streamlit run app.py
```

### Docker Deployment
To deploy the application using Docker, follow these steps:

1. Build the Docker image:
   ```
   docker build -t toyota-bil-analyzer .
   ```

2. Run the application using Docker Compose:
   ```
   docker-compose up
   ```

## Usage
- Open your web browser and navigate to `http://localhost:8501` to access the application.
- Enter a Finn.no URL in the sidebar to fetch and analyze car data.
- View parsed data and AI analysis results in the main interface.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.