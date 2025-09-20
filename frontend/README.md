# RAG-AGENT Frontend

A modern, scalable frontend for the RAG-AGENT system built with Python and NiceGUI. Transform GitHub repositories into intelligent RAG systems with an intuitive web interface.

## Features

### 🔐 Authentication System
- User login and registration
- Role-based access control (Admin/User)
- Session management
- Profile management

### 🏠 Main Dashboard
- Repository overview
- Quick statistics
- Recent activity feed
- Direct access to chat and admin features

### 📁 Repository Management
- Repository selection and browsing
- Sync status monitoring
- Member management (Admin)
- Repository settings and configuration

### 👤 Account Settings
- Profile information management
- Password changes
- Account preferences
- Data export options

### ⚙️ Admin Features
- Repository options and configuration
- Member role management
- Sync settings and controls
- Repository logs and monitoring
- Danger zone operations

### 🗄️ Vector Database Management
- Collection overview and statistics
- Entity browser and search
- Collection management (create, delete, rebuild)
- Performance metrics
- Import/export capabilities

### 💬 RAG Chat System
- Multi-room chat interface
- Real-time messaging
- Context-aware responses
- Source citations
- Chat history management

## Tech Stack

- **Framework**: NiceGUI (Python-based web framework)
- **Backend**: FastAPI integration
- **Styling**: Custom CSS with modern design system
- **Architecture**: Modular component-based structure

## Getting Started

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

4. Open your browser and navigate to:
```
http://localhost:8080
```

## Demo Accounts

The application comes with pre-configured demo accounts:

### Admin Account
- **Email**: admin@ragagent.com
- **Password**: admin123
- **Features**: Full access to all admin features

### User Account
- **Email**: user@ragagent.com
- **Password**: user123
- **Features**: Standard user access

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── header.py       # Navigation header
│   │   └── __init__.py
│   ├── pages/              # Page components
│   │   ├── auth_page.py    # Login/signup pages
│   │   ├── main_page.py    # Dashboard
│   │   ├── repository_settings_page.py
│   │   ├── account_settings_page.py
│   │   ├── repository_options_page.py
│   │   ├── vectordb_page.py
│   │   ├── chat_page.py    # RAG chat interface
│   │   └── __init__.py
│   ├── services/           # Business logic services
│   │   ├── auth_service.py # Authentication logic
│   │   ├── navigation_service.py
│   │   └── __init__.py
│   ├── data/               # Data management
│   │   ├── dummy_data.py   # Mock data for demo
│   │   └── __init__.py
│   ├── utils/              # Utility functions
│   │   ├── theme.py        # CSS styling and themes
│   │   └── __init__.py
│   └── __init__.py
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Key Features

### Responsive Design
- Modern, clean interface
- Mobile-friendly responsive layout
- Consistent design system
- Professional business appearance

### Scalable Architecture
- Modular component structure
- Service-based business logic
- Easy to extend and maintain
- Production-ready architecture

### Mock Data Integration
- Comprehensive dummy data
- Realistic demo scenarios
- Easy to replace with real API calls
- Complete feature demonstration

## Development Notes

### Adding New Features
1. Create new page components in `src/pages/`
2. Add business logic to `src/services/`
3. Register routes in `main.py`
4. Update navigation in header component

### Styling
- All styles are defined in `src/utils/theme.py`
- Uses CSS custom properties for theming
- Consistent spacing and color schemes
- Easy to customize and extend

### Mock Data
- All dummy data is in `src/data/dummy_data.py`
- Replace with actual API calls for production
- Maintains realistic data structures
- Easy to extend with new entities

## Integration Points

The frontend is designed to integrate with:
- **Gateway API**: For authentication and routing
- **Vector Database**: For embeddings and search
- **RAG Engine**: For intelligent responses
- **Repository Sync**: For GitHub integration

## Production Deployment

For production deployment:
1. Replace dummy data with real API services
2. Configure environment variables
3. Set up proper authentication backend
4. Configure SSL/HTTPS
5. Set up monitoring and logging
6. Scale with load balancer if needed

## Contributing

1. Follow the existing code structure
2. Add proper error handling
3. Include appropriate comments
4. Test all functionality
5. Update documentation as needed