# kaggle-capstone-project2
HR and Recruitment Assistant
An AI-powered HR and recruitment management system that helps streamline the hiring process, from candidate sourcing to interview scheduling.

## Key Features

- **Candidate Management**: Store and manage candidate profiles with detailed information
- **Job Position Tracking**: Create and track open positions with requirements and status
- **Advanced Search**: Find candidates based on skills, experience, education, and more
- **Interview Scheduling**: Schedule and manage interviews with automated notifications
- **Matching Algorithm**: Intelligent candidate-position matching based on skills and requirements
- **Data Persistence**: Save all data locally in JSON format

## Installation

1. Ensure you have Python 3.7 or higher installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Initialize the HR Assistant
```python
from hr_assistant import HRAssistant, Candidate, JobPosition, Skill, ExperienceLevel, JobStatus

# Initialize with optional SMTP configuration for email notifications
hr = HRAssistant(
    data_dir="hr_data",
    smtp_config={
        'server': 'smtp.example.com',
        'port': 587,
        'username': 'your_email@example.com',
        'password': 'your_password',
        'from_email': 'hr@yourcompany.com'
    }
)
```

### Add a New Job Position
```python
job = JobPosition(
    position_id=f"POS-{str(uuid.uuid4())[:8].upper()}",
    title="Senior Python Developer",
    department="Engineering",
    location="Remote",
    experience_level=ExperienceLevel.SENIOR,
    description="We are looking for an experienced Python developer...",
    required_skills=[
        Skill(name="Python", years_experience=5, proficiency=5),
        Skill(name="Django", years_experience=3, proficiency=4),
    ],
    status=JobStatus.OPEN
)
hr.positions[job.position_id] = job
```

### Search for Candidates
```python
# Search for senior Python developers
results = hr.search_candidates(
    skills=['Python', 'Django'],
    min_experience=5,
    education='Computer Science',
    status='APPLIED',
    min_salary=90000,
    max_salary=150000,
    sort_by='experience'
)
```

### Schedule an Interview
```python
interview = hr.schedule_interview(
    candidate_id='CAN-123',
    position_id='POS-456',
    interviewer='Sarah Johnson',
    scheduled_time='2023-12-15 14:00',
    interview_type='TECHNICAL',
    location='Zoom Meeting',
    duration=90
)
```

## Data Storage

All data is stored in the specified `data_dir` (default: `hr_data/`) with the following files:
- `candidates.json`: Stores all candidate information
- `positions.json`: Stores all job positions
- `interviews.json`: Stores interview scheduling information
- `resumes/`: Directory for storing candidate resumes

## Requirements

- Python 3.7+
- Required packages (install via `pip install -r requirements.txt`):
  - pandas
  - python-dateutil
  - python-dotenv
  - PyYAML
  - tqdm
  - python-magic
  - python-docx
  - pdfminer.six
  - openpyxl

## License

This project is licensed under the MIT License - see the LICENSE file for details.
