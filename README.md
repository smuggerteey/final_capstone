# Africcase - Intelligent Platform for Promoting Creative Works in Africa

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Installation Guide](#installation-guide)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [API Endpoints](#api-endpoints)
8. [Collaboration Features](#collaboration-features)
9. [Payment Integration](#payment-integration)
10. [Security Considerations](#security-considerations)
11. [Deployment](#deployment)
12. [Contributing](#contributing)
13. [License](#license)
14. [Acknowledgements](#acknowledgements)

## Project Overview

Africcase is an intelligent web platform designed to empower young African artists by providing tools for showcasing, collaborating on, and monetizing their creative works. The platform addresses key challenges artists face in gaining visibility, finding collaboration opportunities, and accessing monetization avenues.

Developed as a capstone project by Nicholas Tafadzwa Mutsaka and Tinotenda Chagaka at Ashesi University, Africcase integrates advanced features including AI-driven recommendations, gamification elements, and secure payment processing.

## Key Features

### Core Functionality
- **Artist Profiles**: Comprehensive profiles with portfolio display
- **Digital Marketplace**: For buying and selling artworks
- **Collaboration Tools**: Real-time whiteboarding, document editing, and project management
- **Gamification**: Badges, leaderboards, and challenges to encourage engagement

### Technical Highlights
- **AI Integration**: Content recommendations and intelligent search
- **File Authentication**: Cryptographic hashing for art authenticity
- **Microservices Architecture**: For scalability and resilience
- **Real-time Communication**: WebSocket-based chat and notifications

## Technology Stack

### Backend
- **Python 3.9+**
- **Flask** (Web framework)
- **Flask-Login** (Authentication)
- **Flask-SocketIO** (Real-time features)
- **MySQL** (Database)
- **PyTorch** (AI model integration)

### Frontend
- **HTML5, CSS3, JavaScript**
- **Bootstrap** (Responsive design)
- **jQuery** (DOM manipulation)
- **Chart.js** (Data visualization)

### Third-Party Integrations
- **Paystack** (Payment processing)
- **Twilio** (Notifications)
- **LaMini-T5-738M** (AI model for recommendations)

## Installation Guide

### Prerequisites
- Python 3.9+
- MySQL 8.0+
- Node.js (for frontend dependencies)
- Git

### Setup Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/smuggerteey/final_capstone.git
   cd africcase
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your configuration values.

## Configuration

### Essential Configuration Variables
```ini
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=africcase_db

# Flask Configuration
SECRET_KEY=your-secret-key-here
UPLOAD_FOLDER=static/uploads
PROFILE_PICS_FOLDER=static/profile_pics

# Paystack Integration
PAYSTACK_SECRET_KEY=your-paystack-secret-key

# AI Model
MODEL_NAME=MBZUAI/LaMini-T5-738M
```

## Database Setup

1. Create the database:
   ```sql
   CREATE DATABASE africcase_db;
   ```

2. Import the schema:
   ```bash
   mysql -u root -p africcase_db < database/schema.sql
   ```

3. For development, you can seed sample data:
   ```bash
   mysql -u root -p africcase_db < database/seed_data.sql
   ```

## API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | POST | User authentication |
| `/register` | POST | New user registration |
| `/logout` | GET | Session termination |

### Artwork Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/artworks` | GET | List all artworks |
| `/api/artworks` | POST | Upload new artwork |
| `/api/artworks/<id>` | GET | Get artwork details |
| `/api/artworks/<id>` | DELETE | Remove artwork |

### Collaboration Features
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/collaboration` | GET | Collaboration hub |
| `/collaboration/create` | POST | Create new room |
| `/collaboration/<room_id>` | GET | Join collaboration room |

## Collaboration Features

Africcase provides several real-time collaboration tools:

1. **Whiteboard Collaboration**
   - Real-time drawing synchronization
   - Version history
   - Export to image/PDF

2. **Document Collaboration**
   - Rich text editing
   - Comment threads
   - Revision tracking

3. **Project Management**
   - Task boards
   - Deadline tracking
   - File sharing

## Payment Integration

The platform integrates with Paystack for secure payment processing:

- Credit card payments
- Mobile money (M-Pesa, MTN Mobile Money)
- Bank transfers
- Secure transaction recording

## Security Considerations

1. **Data Protection**
   - Password hashing with Werkzeug
   - Secure session management
   - CSRF protection

2. **File Uploads**
   - File type verification
   - Virus scanning
   - Secure storage

3. **API Security**
   - Rate limiting
   - Input validation
   - Authentication middleware

## Deployment

### Production Deployment with Gunicorn and Nginx

1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Create a WSGI entry point:
   ```python
   # wsgi.py
   from app import create_app
   application = create_app()
   ```

3. Run with Gunicorn:
   ```bash
   gunicorn --bind 0.0.0.0:8000 wsgi:application
   ```

4. Configure Nginx as a reverse proxy (sample configuration):
   ```nginx
   server {
       listen 80;
       server_name africcase.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static {
           alias /path/to/africcase/static;
       }
   }
   ```

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Ashesi University for academic support
- Our project supervisor, Prof. Joseph Kwame Adjei
- The open source community for valuable tools and libraries
- All the artists who contributed to testing and feedback