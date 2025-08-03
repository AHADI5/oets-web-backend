OETS
Here's the complete `README.md` content ready to copy-paste:

```markdown
# OETS Web Platform (Original English Training School)

## Development Team

| Role | Name | Contact |
|------|------|---------|
| **Backend Developer** | Robert KULE | [https://github.com/RobertKule](mailto:kulewakangitsirobert@gmail.com) |
| **Frontend Developer** | Heritier AMURI | [https://github.com/HeritierAMURI](mailto:heritieramuritcha@gmail.com) |
| **Project Maintainer** | Gloire AHADI | [https://github.com/AHADI5](mailto:kulewakangitsirobert@gmail.com) |

## Table of Contents
- [Project Overview](#-project-overview)
- [Repository Structure](#-repository-structure)
- [Technology Stack](#-technology-stack)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [API Documentation](#-api-documentation)
- [Data Model](#-data-model)
- [Contribution Guidelines](#-contribution-guidelines)
- [License](#-license)
- [Contact](#-contact)

## 🎯 Project Overview

The OETS Web Platform is a comprehensive management system for the Original English Training School in Goma, DR Congo. This digital solution modernizes the school's operations by providing:

- **For Students**:
  - Online course registration
  - Document submission (CVs, motivation letters)
  - Enrollment tracking
  - Testimonial sharing

- **For Teachers**:
  - Course management
  - Student progress tracking
  - Schedule management

- **For Administrators**:
  - Complete school management
  - Content updates
  - User management
  - Reporting

## 🌟 Key Features

| Feature | Description |
|---------|-------------|
| Multi-Role System | Secure access for students, teachers, and admin |
| Course Catalog | Filterable list of available language courses |
| Online Registration | Digital enrollment with file uploads |
| Custom Requests | Special training program inquiries |
| CMS | Dynamic content management for school info |
| Notifications | Automated email confirmations |

## 📂 Repository Structure

**Branches**:
- `main`: Production-ready stable code
- `main-development`: Active development branch

**Important Files**:
- `oets/settings.py`: Main configuration
- `core/models.py`: Database models
- `core/views.py`: API endpoints
- `requirements.txt`: Dependencies

## 🛠️ Technology Stack

### Backend
    on the repository https://github.com/AHADI5/oets-web-backend.git
- Python 3.9+
- Django 3.2
- Django REST Framework
- PostgreSQL (production)
- SQLite (development)
- JWT Authentication

### Frontend (Separate Repo)
    on the repository https://github.com/AHADI5/oets-app.git    
- React.js
- Redux Toolkit
- Material-UI
- Axios for API calls

## ⚙️ Configuration

### 1. Clone Repository
```bash
git clone https://github.com/AHADI5/oets-web-backend.git
cd oets-web-backend
```

### 2. Set Up Environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create `.env` file:
```ini
DEBUG=True
DJANGO_SECRET_KEY=your-secure-key-here
DATABASE_URL=sqlite:///db.sqlite3  # Default for development
```

For PostgreSQL:
```ini
DATABASE_URL=postgres://user:password@localhost:5432/oets_db
```

### 5. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

## 🚀 Deployment

### Production Requirements
1. Set `DEBUG=False` in `.env`
2. Configure:
   ```ini
   ALLOWED_HOSTS=yourdomain.com
   SECURE_SSL_REDIRECT=True
   ```
3. Set up:
   - PostgreSQL database
   - Static files (run `collectstatic`)
   - Media file storage (S3 recommended)

## 🔍 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/` | POST | Create student account |
| `/api/courses/` | GET | List all courses |
| `/api/enrollments/` | POST | Register for course |
| `/api/departments/` | GET | List language departments |
| 'etc................'

Access docs at:
- `http://localhost:8000/swagger/`
- `http://localhost:8000/redoc/`

## 🤝 How to Contribute

1. Fork the repository
2. Create feature branch:
   ```bash
   git checkout -b feature/new-feature
   ```
3. Commit changes:
   ```bash
   git commit -m "[FEAT] the_branch: message is Add new feature"
   ```
4. Push to branch:
   ```bash
   git push origin feature/new-feature
   ```
5. Open pull request to `main-development`

## 📜 License
MIT License - See LICENSE file for details

## 📞 Contact
**Technical Support**:  
AHADI Gloire - [gloireahadi9@gmail.com](mailto:gloireahadi9@gmail.com)

**devellopers**:
Robert KULE - [kulewakangitsirobert@gmail.com](mailto:kulewakangitsirobert@gmail.com)
Heritier AMURI - [heritieramuritcha@gmail.com](mailto:heritieramuritcha@gmail.com)

**School Administration**:  
OETS Goma - [our contact](mailto:our contact)
