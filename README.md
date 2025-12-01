<<<<<<< HEAD
# Remote Work Monitor

A comprehensive full-stack Python web application for office remote work monitoring with face recognition, task management, and analytics.

## Features

### 🔐 Authentication & Security
- **Face Recognition Login**: Secure authentication using facial recognition technology
- **Periodic Face Verification**: Continuous monitoring during work hours
- **User Management**: Admin panel for user account management

### 📹 Live Monitoring
- **Real-time Webcam Monitoring**: Continuous face detection and recognition
- **Activity Tracking**: Monitor user presence and activity levels
- **Security Alerts**: Detect unauthorized access and inactivity

### 📋 Task Management
- **Trello-like Board**: Drag-and-drop task management interface
- **Task Status Tracking**: Todo, In Progress, Completed, Overdue
- **Priority Levels**: Low, Medium, High, Urgent
- **Due Date Management**: Track deadlines and overdue tasks

### 📊 Analytics & Performance
- **Performance Scoring**: Multi-factor performance evaluation
- **Work Hours Tracking**: Monitor daily and weekly work hours
- **Analytics Dashboard**: Visual charts and performance metrics
- **Historical Data**: Track performance over time

### 🔔 Notifications
- **Real-time Alerts**: WebSocket-based instant notifications
- **System Notifications**: Admin-generated alerts and announcements
- **Activity Alerts**: Inactivity and security notifications

## Technology Stack

### Backend
- **Python 3.8+**
- **Flask**: Web framework with MVC architecture
- **Flask-SQLAlchemy**: Database ORM
- **Flask-SocketIO**: Real-time WebSocket communication
- **Flask-Login**: User session management
- **Face Recognition**: OpenCV + face_recognition library
- **DeepFace**: Advanced face recognition capabilities

### Frontend
- **HTML5 + CSS3**
- **Tailwind CSS**: Utility-first CSS framework
- **JavaScript (ES6+)**: Interactive frontend functionality
- **Chart.js**: Data visualization
- **Socket.IO**: Real-time communication

### Database
- **SQLite**: Primary database (no external setup required)
- **MySQL/PostgreSQL**: Optional for production deployment

## Installation

### Prerequisites
- Python 3.8 or higher
- Webcam for face recognition
- Modern web browser
- No external database required (uses SQLite)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd meeting_app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment (optional)**
   ```bash
   cp env_example.txt .env
   # Edit .env if you want to customize settings
   ```

5. **Initialize database**
   ```bash
   python init_db.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open your browser and go to `http://localhost:5000`
   - Login with admin credentials (admin/admin123)
   - Change the admin password immediately

## Configuration

### Database Setup

#### SQLite (Default - No Setup Required)
The application uses SQLite by default, which requires no external database setup. The database file will be created automatically.

#### MySQL (Optional for Production)
```sql
CREATE DATABASE remote_work_monitor;
CREATE USER 'monitor_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON remote_work_monitor.* TO 'monitor_user'@'localhost';
FLUSH PRIVILEGES;
```

#### PostgreSQL (Optional for Production)
```sql
CREATE DATABASE remote_work_monitor;
CREATE USER monitor_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE remote_work_monitor TO monitor_user;
```

### Environment Variables

Copy `env_example.txt` to `.env` and configure:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///remote_work_monitor.db
FACE_TOLERANCE=0.6
WORK_HOURS_START=9
WORK_HOURS_END=17
```

## Usage

### User Registration
1. Navigate to the registration page
2. Provide username, email, and password
3. Upload a clear photo of your face
4. Complete registration

### Face Recognition Login
1. Enter username and password
2. Allow camera access when prompted
3. Look directly at the camera
4. System will verify your identity

### Task Management
1. Access the task board from the dashboard
2. Create new tasks with titles, descriptions, and due dates
3. Drag tasks between columns or use action buttons
4. Set priority levels and track progress

### Admin Functions
1. Monitor all users in real-time
2. View analytics and performance reports
3. Manage notifications and alerts
4. Access system logs and activity history

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login with face recognition
- `POST /auth/verify_face` - Periodic face verification
- `GET /auth/logout` - User logout

### Tasks
- `GET /tasks/` - Task board
- `POST /tasks/create` - Create new task
- `PUT /tasks/<id>/update_status` - Update task status
- `DELETE /tasks/<id>/delete` - Delete task

### Monitoring
- `GET /monitoring/live` - Live monitoring interface
- `POST /monitoring/start_monitoring` - Start monitoring
- `POST /monitoring/stop_monitoring` - Stop monitoring
- `GET /monitoring/status` - Get monitoring status

### Analytics
- `GET /analytics/` - Analytics dashboard
- `GET /analytics/api/performance_chart` - Performance data
- `GET /analytics/api/work_hours_chart` - Work hours data

## Security Considerations

### Face Recognition
- Face encodings are stored securely in the database
- No raw images are stored, only mathematical encodings
- Configurable tolerance levels for recognition accuracy

### Data Protection
- All passwords are hashed using bcrypt
- Sensitive data is encrypted in transit
- Regular security updates recommended

### Privacy
- Users are notified about monitoring
- Face data can be deleted upon request
- Compliance with privacy regulations

## Troubleshooting

### Common Issues

1. **Camera not working**
   - Ensure camera permissions are granted
   - Check if another application is using the camera
   - Try refreshing the page

2. **Face recognition failing**
   - Ensure good lighting on your face
   - Look directly at the camera
   - Remove sunglasses or face coverings
   - Try re-registering with a clearer photo

3. **Database connection errors**
   - Verify database credentials in .env
   - Ensure database server is running
   - Check network connectivity

4. **Performance issues**
   - Close unnecessary browser tabs
   - Check system resources
   - Consider using a more powerful server

### Logs
- Application logs are written to the console
- Check browser developer tools for frontend errors
- Database logs can be found in your database management tool

## Development

### Project Structure
```
meeting_app/
├── app.py                 # Main application file
├── config.py             # Configuration settings
├── init_db.py            # Database initialization
├── requirements.txt      # Python dependencies
├── models/               # Database models
│   ├── user.py
│   ├── task.py
│   ├── performance.py
│   └── ...
├── controllers/          # MVC controllers
│   ├── auth_controller.py
│   ├── task_controller.py
│   └── ...
├── templates/            # HTML templates
│   ├── base.html
│   ├── auth/
│   ├── dashboard/
│   └── ...
└── static/              # Static files
    └── uploads/         # File uploads
```

### Adding New Features
1. Create model in `models/` directory
2. Add controller in `controllers/` directory
3. Create templates in `templates/` directory
4. Update routes in `app.py`
5. Add database migration if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

## Roadmap

### Planned Features
- [ ] Mobile app support
- [ ] Advanced analytics
- [ ] Integration with calendar systems
- [ ] Team collaboration features
- [ ] Advanced reporting
- [ ] API rate limiting
- [ ] Multi-language support

### Version History
- **v1.0.0**: Initial release with core features
- **v1.1.0**: Enhanced analytics and reporting
- **v1.2.0**: Mobile responsiveness improvements
- **v2.0.0**: Advanced monitoring and AI features

---

**Note**: This application is designed for legitimate workplace monitoring with proper user consent and compliance with applicable privacy laws and regulations.
=======
# 3d-office
>>>>>>> 08a7d7fbc74e7fcff8bc25fe080d4874ef012e99
