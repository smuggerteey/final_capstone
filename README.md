# Creative Showcase Platform

## Overview
The **Creative Showcase Platform** is a web application designed to empower student artists by providing a digital space to exhibit, collaborate, and sell their artistic works. Built using Flask, this platform integrates key functionalities such as secure user authentication, an interactive marketplace, real-time collaboration, and blockchain-based artwork verification.

## Features
- **User Authentication**: Secure registration and login using Flask-Login.
- **Artwork Upload**: Artists can upload their artworks with detailed descriptions and pricing.
- **Marketplace**: A dynamic marketplace where users can browse and purchase artworks.
- **Real-time Chat**: Powered by Flask-SocketIO for instant messaging and collaboration.
- **Payment Processing**: Secure transactions through PayPal integration.
- **Blockchain Verification**: Ensures artwork authenticity using Ethereum blockchain integration.
- **Leaderboards & Challenges**: Gamified experience through challenges and a points-based leaderboard.

## Technologies Used
- **Backend**: Flask, Flask-SQLAlchemy, Flask-Login
- **Database**: MySQL
- **Blockchain**: Web3.js for Ethereum interactions
- **Payment Processing**: PayPal SDK
- **Real-time Communication**: Flask-SocketIO
- **AI Integration**: Chatbot functionality using `MBZUAI/LaMini-T5-738M`

## Installation & Setup

### Prerequisites
Ensure you have the following installed:
- Python 3.x
- MySQL Server
- Node.js (for managing dependencies)
- An Etherscan API key and Infura Project ID (for blockchain integration)

### Steps to Install
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   - Create a MySQL database.
   - Update `db_config` in the application with your database credentials.
   - Run the necessary SQL scripts to set up tables.

4. **Configure Environment Variables**
   - Set up your `.env` file with the required API keys and configurations:
     ```ini
     ETHERSCAN_API_KEY=your_etherscan_api_key
     INFURA_PROJECT_ID=your_infura_project_id
     PAYPAL_CLIENT_ID=your_paypal_client_id
     PAYPAL_SECRET=your_paypal_secret
     ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Platform**
   Open your browser and go to: `http://127.0.0.1:5000`

## Usage Guide
### User Flow
- **Register/Login**: Create an account to access the platform.
- **Dashboard**: View challenges, upload artworks, and manage profiles.
- **Marketplace**: Browse and purchase available artworks.
- **Chat & Collaborate**: Connect with other artists in real-time.
- **Verify Artwork**: Use blockchain integration to authenticate digital pieces.

### File Uploads
Ensure the following directories exist for proper media handling:
- `static/uploads` → Stores uploaded artwork.
- `static/profile_pics` → Stores user profile pictures.
- If missing, the application will automatically create these directories.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch (`feature-new-functionality`).
3. Commit your changes and push them.
4. Open a pull request for review.

## License
This project is licensed under the **MIT License**. See the `LICENSE` file for details.

## Contact & Support
For any inquiries or support, please contact the project maintainers.

