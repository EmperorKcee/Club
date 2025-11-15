<div align="center">
  <h1>⚽ Football Club Management System</h1>
  <p>
    <em>A comprehensive, secure web-based management system for football clubs built with Flask</em>
  </p>
  
  [![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Flask](https://img.shields.io/badge/Flask-2.0.1-000000.svg?logo=flask)](https://flask.palletsprojects.com/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
  
  <img src="static/img/dashboard-preview.png" alt="Dashboard Preview" width="800">
</div>

A comprehensive, secure web-based management system for football clubs built with Flask. This system provides complete player management, match scheduling, financial tracking, and administrative tools with professional PDF generation and dual-interface support for both staff and players.

## ✨ Features

### 🏠 Admin Dashboard
- **Real-time Statistics**: Total players, matches, goals, and performance metrics
- **Top Scorers Leaderboard**: Dynamic player rankings with statistics
- **Match Overview**: Recent results and upcoming fixtures
- **Financial Summary**: Income, expenses, and profit/loss tracking
- **Quick Actions**: Direct access to common tasks

### 👥 Advanced Player Management
- **Complete Player Profiles**: Photos, personal info, and contract details
- **Statistics Tracking**: Goals, assists, cards, minutes played, clean sheets
- **Smart Filtering**: Position-based, status, and search functionality
- **Contract Management**: Expiration tracking and status monitoring
- **PDF Profile Generation**: Professional player profiles with photos
- **Account Management**: Secure player portal access
- **Bulk Operations**: Mass account creation and management
- **Export/Print**: CSV export and print-friendly formats

### 🎮 Player Portal
- **Dedicated Dashboard**: Personalized interface for players
- **Profile Management**: View and update personal information
- **Statistics View**: Personal performance metrics and history
- **Training Schedule**: Access to training sessions and schedules
- **Team News**: Club announcements and updates
- **Squad Overview**: Team roster and player information

### ⚽ Match Management
- **Complete Match Scheduling**: Date, time, venue, and opponent management
- **Opponent Database**: Team information with logos and details
- **Match Results**: Score tracking and result management
- **Competition Categories**: League, cup, friendly classifications
- **Status Tracking**: Scheduled, ongoing, completed, postponed
- **PDF Match Flyers**: Professional match promotional materials
- **Venue Management**: Home/away designation and location details

### 💰 Financial Management
- **Transaction Tracking**: Comprehensive income and expense management
- **Category Management**: Organized financial categorization
- **Monthly/Annual Reports**: Detailed financial analysis
- **Profit/Loss Calculations**: Automated financial summaries
- **Trend Analysis**: Visual financial performance tracking
- **Export Capabilities**: Financial data export for accounting

### 👔 Staff Management
- **Staff Profiles**: Complete employee information management
- **Role Assignment**: Department and position tracking
- **Contact Management**: Phone, email, and address information
- **Salary Tracking**: Compensation and contract management
- **Profile Pictures**: Professional staff photo management

### ⚙️ Dynamic Team Settings
- **Team Branding**: Logo, colors, and visual identity
- **Contact Information**: Club details and communication
- **Customizable Interface**: Team-specific branding throughout system
- **About Section**: Club history and information management
- **Login Customization**: Branded login experience

### 🔒 Security & Authentication
- **CSRF Protection**: Complete form security implementation
- **Dual Authentication**: Separate admin and player login systems
- **Session Management**: Secure user session handling
- **Role-based Access**: Admin and player permission levels
- **Password Security**: Encrypted password storage and validation

### 📊 Reports & Analytics
- **Player Performance**: Detailed statistics and performance metrics
- **Match Analysis**: Results tracking and team performance
- **Financial Reports**: Comprehensive financial summaries
- **PDF Generation**: Professional reports with team branding
- **Export Options**: CSV, PDF, and print-friendly formats
- **Data Visualization**: Charts and graphs for key metrics

## 🛠️ Technology Stack

- **Backend**: Flask (Python) with Blueprint architecture
- **Database**: SQLite with SQLAlchemy ORM and Flask-Migrate
- **Security**: Flask-WTF with CSRF protection, Flask-Login authentication
- **Frontend**: Bootstrap 5, HTML5, CSS3, Vanilla JavaScript
- **PDF Generation**: ReportLab with custom styling and branding
- **Email**: Flask-Mail for notifications and communications
- **File Handling**: Secure file uploads with validation
- **Charts**: Chart.js for data visualization
- **Icons**: Font Awesome 6 for modern iconography
- **Forms**: Flask-WTF for secure form handling

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (for version control)
- SQLite (included with Python)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/football-club-management.git
   cd football-club-management
   ```

2. **Set up a virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with your configuration:
   ```env
   # Application Settings
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=your-secure-secret-key-here
   
   # Database Configuration
   DATABASE_URL=sqlite:///club.db
   
   # File Uploads
   UPLOAD_FOLDER=static/uploads
   MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
   ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'}
   
   # Security
   WTF_CSRF_ENABLED=True
   SESSION_COOKIE_SECURE=True
   SESSION_COOKIE_HTTPONLY=True
   SESSION_COOKIE_SAMESITE='Lax'
   
   # Email Configuration (optional, for password resets)
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-email-password
   MAIL_DEFAULT_SENDER=your-email@example.com
   ```

5. **Initialize the database**
   ```bash
   # Set up database migrations
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   
   # Create default admin user
   python create_admin.py
   ```

6. **Run the application**
   ```bash
   # Development server
   flask run
   
   # Or for production (with Gunicorn)
   # pip install gunicorn
   # gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

7. **Access the application**
   Open your web browser and navigate to `http://localhost:5000`

### Default Admin Account

- **Email**: admin@example.com
- **Password**: admin123

> ⚠️ **Security Notice**: Change the default admin password immediately after first login!

## 🔧 Configuration

### File Structure

```
football-club-management/
├── app/                      # Application package
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── auth/                # Authentication blueprints
│   ├── admin/               # Admin panel blueprints
│   ├── player/              # Player portal blueprints
│   ├── static/              # Static files (CSS, JS, images)
│   │   ├── css/
│   │   ├── js/
│   │   └── uploads/         # User uploaded files
│   └── templates/           # HTML templates
├── migrations/              # Database migrations
├── tests/                   # Test suite
├── .env                    # Environment variables
├── config.py               # Configuration settings
├── requirements.txt        # Dependencies
└── app.py                 # Application entry point
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Main application module | `app.py` |
| `FLASK_ENV` | Environment (development/production) | `development` |
| `SECRET_KEY` | Secret key for session management | *Required* |
| `DATABASE_URL` | Database connection URL | `sqlite:///club.db` |
| `UPLOAD_FOLDER` | Path for file uploads | `static/uploads` |
| `MAX_CONTENT_LENGTH` | Max file upload size | `16777216` (16MB) |
| `MAIL_*` | Email configuration (optional) | - |

### Database Setup

The application uses SQLite by default for development. For production, consider using PostgreSQL or MySQL:

```env
# PostgreSQL example
DATABASE_URL=postgresql://username:password@localhost/fcms

# MySQL example
DATABASE_URL=mysql+pymysql://username:password@localhost/fcms
```

### File Uploads

- **Supported Formats**: PNG, JPG, JPEG, GIF
- **Size Limit**: 16MB per file
- **Storage**: Files are stored in the `static/uploads/` directory with the following structure:
  - `players/` - Player profile pictures
  - `teams/` - Team logos and images
  - `opponents/` - Opponent team logos
  - `documents/` - Other uploaded documents

### Email Configuration

For password reset functionality, configure your email settings in the `.env` file:

```env
# Example for Gmail
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use App Password for Gmail
```

> **Note**: For Gmail, you may need to enable "Less secure app access" or use an App Password if 2FA is enabled.

## Usage

### Getting Started

#### For Administrators
1. **Login** with the default admin credentials at `/login`
2. **Update team settings** with your club information and branding
3. **Add players** to your roster with complete profiles
4. **Create player accounts** for portal access
5. **Schedule matches** against opponents
6. **Track finances** and manage staff
7. **Generate reports** and PDFs as needed

#### For Players
1. **Receive login credentials** from your club administrator
2. **Access player portal** at `/login` (same page, auto-detects user type)
3. **View personal dashboard** with statistics and information
4. **Update profile** information and view team news
5. **Check training schedules** and squad information
6. **Download personal** performance reports

#### Dual Interface System
The system automatically detects user type on login:
- **Admin users** → Full management dashboard
- **Player users** → Player-specific portal
- **Unified login** → Single entry point for all users
- **Role-based access** → Appropriate features for each user type

### Key Workflows

#### Adding a New Player
1. Navigate to **Players → Add Player**
2. Fill in **required information**:
   - First Name and Last Name
   - Date of Birth (YYYY-MM-DD format)
   - Position and Jersey Number
3. Add **optional details**:
   - Player photo upload
   - Contract information and salary
   - Contact details and biography
4. **Save** the player profile
5. **Create player account** (optional) for portal access

#### Managing Player Accounts
1. Go to **Players → Player Accounts**
2. **Create accounts** for players to access the player portal
3. **Generate credentials** automatically or set custom passwords
4. **Bulk operations** for multiple account creation
5. **Export credentials** for distribution to players

#### Scheduling a Match
1. Navigate to **Matches → Add Match**
2. Enter **opponent information** and upload logo
3. Set **match details**:
   - Date, time, and venue
   - Competition type and status
4. **Generate match flyer** PDF for promotion
5. **Update results** after the match

#### Managing Finances
1. Access **Finances** from the main menu
2. **Add transactions** with proper categorization
3. **View reports** for monthly and annual summaries
4. **Export data** for external accounting
5. **Track trends** with visual analytics

#### Team Customization
1. Go to **Settings → Team Settings**
2. **Upload team logo** and set brand colors
3. **Configure contact information** and club details
4. **Customize login page** with team branding
5. **Update about section** with club history

## File Structure

```
football-club-management/
├── app.py                 # Main Flask application
├── models.py             # Database models
├── utils.py              # Utility functions
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── static/              # Static assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   ├── img/            # Images and icons
│   └── uploads/        # User uploaded files
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── dashboard.html  # Dashboard page
│   ├── players/        # Player templates
│   ├── matches/        # Match templates
│   └── ...            # Other templates
└── instance/           # Instance-specific files
    └── club.db         # SQLite database
```

## 🔗 API Endpoints

### Authentication & Security
- `GET /login` - Unified login page (admin/player)
- `POST /login` - Process login with CSRF protection
- `GET /player/login` - Player-specific login (redirects to unified)
- `POST /player/login` - Process player login
- `GET /logout` - Secure logout with session cleanup

### Player Management
- `GET /players` - List players with filtering and search
- `GET /players/add` - Add player form with validation
- `POST /players/add` - Create player with CSRF protection
- `GET /players/<id>` - View detailed player profile
- `GET /players/<id>/edit` - Edit player with pre-filled data
- `POST /players/<id>/edit` - Update player with validation
- `POST /players/<id>/delete` - Delete player with confirmation
- `GET /players/<id>/download` - Generate PDF with player photo

### Player Portal
- `GET /player/dashboard` - Player-specific dashboard
- `GET /player/profile` - Player profile management
- `GET /player/training` - Training schedule access
- `GET /player/squad` - Team roster view
- `GET /player/news` - Club news and announcements

### Player Account Management
- `GET /admin/player-accounts` - Account management dashboard
- `POST /admin/create-player-account/<id>` - Create player account
- `POST /admin/edit-player-account/<id>` - Edit player account
- `POST /admin/delete-player-account/<id>` - Delete player account
- `POST /admin/reset-player-password/<id>` - Reset player password
- `POST /admin/bulk-create-player-accounts` - Bulk account creation

### Match Management
- `GET /matches` - List matches with status filtering
- `GET /matches/add` - Add match form
- `POST /matches/add` - Create match with validation
- `GET /matches/<id>` - View match details
- `GET /matches/<id>/edit` - Edit match form
- `POST /matches/<id>/edit` - Update match
- `POST /matches/<id>/delete` - Delete match with confirmation
- `GET /match/<id>/flyer` - Generate branded match flyer PDF

### Financial Management
- `GET /finances` - Financial dashboard with analytics
- `GET /transaction/add` - Add transaction form
- `POST /transaction/add` - Create transaction with validation
- `GET /transaction/<id>/edit` - Edit transaction
- `POST /transaction/<id>/edit` - Update transaction
- `POST /transaction/<id>/delete` - Delete transaction

### Team Settings & Customization
- `GET /settings` - Team settings management
- `POST /settings` - Update team settings with file upload
- `GET /contact` - Contact page with team information
- `POST /contact` - Process contact form submissions

## 🧪 Testing & Maintenance

### Included Test Scripts
The system includes comprehensive testing and maintenance tools:

**Validation & Debugging:**
- `debug_player_saving.py` - Test player creation and database constraints
- `test_csrf_fix.py` - Verify CSRF protection is working
- `test_login_csrf.py` - Test login form security
- `verify_delete_functionality.py` - Test delete operations

**Photo & PDF Management:**
- `test_player_pdf_photos.py` - Verify PDF photo generation
- `fix_player_photo_urls.py` - Fix broken player photo URLs
- `check_player_photos.py` - Validate player photo files

**System Verification:**
- `verify_player_system.py` - Complete player system test
- `test_unified_login.py` - Test dual login system
- `verify_interface_separation.py` - Test admin/player separation

**Database Maintenance:**
- `fix_database_integrity.py` - Fix database relationship issues
- `migrate_database.py` - Handle database migrations
- `check_users.py` - Verify user accounts

### Running Tests
```bash
# Test player saving functionality
python debug_player_saving.py

# Verify CSRF protection
python test_csrf_fix.py

# Check PDF photo generation
python test_player_pdf_photos.py

# Fix broken photo URLs
python fix_player_photo_urls.py
```

## 🤝 Contributing

We welcome contributions from the community! Whether you're fixing bugs, improving documentation, or adding new features, your help is appreciated.

### How to Contribute

1. **Fork the repository** and create your feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Set up the development environment**
   ```bash
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Set up pre-commit hooks
   pre-commit install
   ```

3. **Make your changes** following our coding standards
   - Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code
   - Use type hints for better code documentation
   - Write docstrings for all public functions and classes
   - Keep lines under 88 characters (PEP 8 recommendation)

4. **Write tests** for your changes
   ```bash
   # Run all tests
   pytest
   
   # Run tests with coverage report
   pytest --cov=app tests/
   ```

5. **Update documentation** as needed
   - Update docstrings for any new or modified functions
   - Update README.md if you've changed installation or usage instructions
   - Add comments for complex logic

6. **Commit your changes** with a descriptive message
   ```bash
   git commit -m "feat: add amazing feature"
   ```
   
   We follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `style:` for formatting changes
   - `refactor:` for code changes that neither fix bugs nor add features
   - `test:` for adding tests
   - `chore:` for maintenance tasks

7. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

8. **Open a Pull Request**
   - Provide a clear title and description
   - Reference any related issues
   - Include screenshots if applicable

### Development Guidelines

#### Code Style
- Use 4 spaces for indentation
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for better code documentation
- Write docstrings for all public functions and classes
- Keep functions small and focused on a single task

#### Security
- Always validate and sanitize user input
- Use parameterized queries to prevent SQL injection
- Implement CSRF protection for all forms
- Follow the principle of least privilege
- Never commit sensitive information to version control

#### Testing
- Write unit tests for new functionality
- Aim for good test coverage (80%+)
- Test edge cases and error conditions
- Update tests when changing functionality

#### Documentation
- Keep documentation up-to-date
- Add comments for complex logic
- Document API endpoints and their parameters
- Include examples where helpful

### Code Review Process
1. Pull requests are reviewed by maintainers
2. Automated tests must pass
3. Code must meet our quality standards
4. At least one approving review is required before merging
5. All feedback should be addressed before merging

### Reporting Issues
Found a bug or have a feature request? Please open an issue with:
- A clear description of the problem
- Steps to reproduce the issue
- Expected vs actual behavior
- Screenshots if applicable
- Your environment details

### Community
Join our community to get help and discuss development:
- [Discord Server](https://discord.gg/your-invite-link)
- [GitHub Discussions](https://github.com/yourusername/football-club-management/discussions)
- [Issue Tracker](https://github.com/yourusername/football-club-management/issues)

## 🔒 Security Features

### Built-in Security
- **CSRF Protection**: All forms protected against cross-site request forgery
- **Input Validation**: Comprehensive server-side validation for all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Session Security**: Secure session management with Flask-Login
- **Password Hashing**: Werkzeug password hashing for secure storage
- **File Upload Security**: Validated file types and secure storage paths

### Security Best Practices
- **Change default credentials** immediately after installation
- **Use strong passwords** with mixed characters, numbers, and symbols
- **Enable HTTPS** in production environments
- **Regular backups** of database and uploaded files
- **Keep dependencies updated** with `pip install -U -r requirements.txt`
- **Monitor access logs** for suspicious activity
- **Validate user permissions** before sensitive operations

### Access Control
- **Role-based Access**: Separate admin and player interfaces
- **Protected Routes**: Login required for all sensitive operations
- **CSRF Tokens**: Automatic token generation and validation
- **Session Timeout**: Automatic logout after inactivity
- **Permission Checks**: Admin-only access to management functions

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License

```
MIT License

Copyright (c) 2023 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- Built with ❤️ using Flask and modern web technologies
- Inspired by real-world football club management needs
- Thanks to all contributors who have helped improve this project
- Special thanks to the Flask and Python communities for their amazing tools and libraries

## 📞 Support

If you need help or have questions:

- [Open an issue](https://github.com/yourusername/football-club-management/issues) for bug reports or feature requests
- Email: support@example.com
- Join our [Discord community](https://discord.gg/your-invite-link)

## 🌟 Stargazers and Forks

[![Stargazers](https://img.shields.io/github/stars/yourusername/football-club-management?style=social)](https://github.com/yourusername/football-club-management/stargazers)
[![Forks](https://img.shields.io/github/forks/yourusername/football-club-management?style=social)](https://github.com/yourusername/football-club-management/network/members)
[![Watchers](https://img.shields.io/github/watchers/yourusername/football-club-management?style=social)](https://github.com/yourusername/football-club-management/watchers)

## 📊 Project Activity

![GitHub last commit](https://img.shields.io/github/last-commit/yourusername/football-club-management)
![GitHub issues](https://img.shields.io/github/issues/yourusername/football-club-management)
![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/football-club-management)

## 🤝 Contributors

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!

## Support

For support and questions:
- Create an issue in the repository
- Review the documentation

## Acknowledgments

- Flask community for the excellent framework
- Bootstrap team for the responsive UI components
- ReportLab for PDF generation capabilities
- Font Awesome for the icon library

## 🆕 Recent Updates & Fixes

### Version 2.0.0 - October 2024

**🔒 Security Enhancements**
- ✅ Complete CSRF protection implementation
- ✅ Enhanced form validation and error handling
- ✅ Secure player account management system
- ✅ Improved authentication flow

**👥 Player Management Improvements**
- ✅ Fixed player saving errors with comprehensive validation
- ✅ Enhanced player account creation and management
- ✅ Bulk operations for player accounts
- ✅ Improved contract tracking and validation

**📸 PDF & Photo Enhancements**
- ✅ Player photos now included in PDF downloads
- ✅ Automatic photo URL fixing and validation
- ✅ Professional PDF layouts with team branding
- ✅ Improved image handling and fallbacks

**🎮 Player Portal**
- ✅ Dedicated player dashboard interface
- ✅ Unified login system for admin and players
- ✅ Player-specific features and access control
- ✅ Personalized player experience

**🧹 Code Quality & Performance**
- ✅ JavaScript cleanup and optimization
- ✅ Removed duplicate code and improved maintainability
- ✅ Enhanced error logging and debugging tools
- ✅ Comprehensive testing suite

**🎨 UI/UX Improvements**
- ✅ Dynamic team branding throughout interface
- ✅ Improved responsive design
- ✅ Enhanced user feedback and notifications
- ✅ Professional styling and animations

---

**Version**: 2.0.0  
**Last Updated**: November 2025  
**Status**: Production Ready ✅