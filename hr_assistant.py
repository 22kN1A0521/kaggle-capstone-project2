import json
import os
import re
import smtplib
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Union
import pandas as pd
import random
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Literal
import uuid
from enum import Enum

# Enums for different types
experience_level = Enum('ExperienceLevel', ['ENTRY', 'MID', 'SENIOR', 'LEAD', 'EXECUTIVE'])
job_status = Enum('JobStatus', ['DRAFT', 'OPEN', 'INTERVIEWING', 'OFFERED', 'FILLED', 'CANCELLED'])
candidate_status = Enum('CandidateStatus', 
                       ['APPLIED', 'SCREENING', 'INTERVIEW_SCHEDULED', 'INTERVIEWED', 
                        'OFFERED', 'HIRED', 'REJECTED', 'WITHDRAWN'])

@dataclass
class Skill:
    name: str
    years_experience: float
    proficiency: int  # 1-5 scale

@dataclass
class Education:
    degree: str
    field: str
    institution: str
    year_completed: int
    gpa: Optional[float] = None

@dataclass
class WorkExperience:
    title: str
    company: str
    start_date: str
    end_date: Optional[str]  # None for current position
    description: str
    achievements: List[str] = field(default_factory=list)

@dataclass
class Candidate:
    candidate_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    skills: List[Skill]
    education: List[Education]
    experience: List[WorkExperience]
    status: candidate_status = candidate_status.APPLIED
    application_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    notes: List[Dict[str, str]] = field(default_factory=list)  # For recruiter notes
    resume_path: Optional[str] = None

@dataclass
class JobPosition:
    position_id: str
    title: str
    department: str
    location: str
    experience_level: experience_level
    description: str
    required_skills: List[Skill]
    preferred_skills: List[Skill] = field(default_factory=list)
    status: job_status = job_status.DRAFT
    hiring_manager: Optional[str] = None
    salary_range: Optional[Dict[str, float]] = None
    open_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    close_date: Optional[str] = None
    
    def to_dict(self):
        return {
            'position_id': self.position_id,
            'title': self.title,
            'department': self.department,
            'location': self.location,
            'experience_level': self.experience_level.name,
            'status': self.status.name,
            'open_date': self.open_date,
            'close_date': self.close_date or ""
        }

class HRAssistant:
    def __init__(self, data_dir: str = "hr_data", smtp_config: Optional[Dict] = None):
        """
        Initialize the HR Assistant with data directory and optional email configuration
        
        Args:
            data_dir: Directory to store HR data
            smtp_config: Dictionary containing SMTP configuration for email notifications
                        {
                            'server': 'smtp.example.com',
                            'port': 587,
                            'username': 'your_email@example.com',
                            'password': 'your_password',
                            'from_email': 'hr@yourcompany.com'
                        }
        """
        self.data_dir = data_dir
        self.candidates: Dict[str, Candidate] = {}
        self.positions: Dict[str, JobPosition] = {}
        self.interviews: List[Dict] = []
        self.smtp_config = smtp_config
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "resumes"), exist_ok=True)
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON files"""
        candidates_path = os.path.join(self.data_dir, "candidates.json")
        positions_path = os.path.join(self.data_dir, "positions.json")
        
        if os.path.exists(candidates_path):
            with open(candidates_path, 'r') as f:
                candidates_data = json.load(f)
                # Convert dict to Candidate objects
                self.candidates = {cid: Candidate(**data) for cid, data in candidates_data.items()}
        
        if os.path.exists(positions_path):
            with open(positions_path, 'r') as f:
                positions_data = json.load(f)
                # Convert dict to JobPosition objects
                self.positions = {pid: JobPosition(**data) for pid, data in positions_data.items()}
    
    def _save_data(self):
        """Save data to JSON files"""
        candidates_path = os.path.join(self.data_dir, "candidates.json")
        positions_path = os.path.join(self.data_dir, "positions.json")
        
        # Convert objects to dicts
        candidates_data = {cid: self._candidate_to_dict(cand) for cid, cand in self.candidates.items()}
        positions_data = {pid: self._position_to_dict(pos) for pid, pos in self.positions.items()}
        
        with open(candidates_path, 'w') as f:
            json.dump(candidates_data, f, indent=2)
        
        with open(positions_path, 'w') as f:
            json.dump(positions_data, f, indent=2)
    
    def _candidate_to_dict(self, candidate: 'Candidate') -> Dict:
        """Convert Candidate object to dictionary with proper status handling"""
        # Handle status - it might be an enum or a string
        status = candidate.status
        if hasattr(status, 'name'):  # It's an enum
            status_str = status.name
        else:  # It's already a string
            status_str = str(status)
            
        # Safely get attributes with defaults
        return {
            'candidate_id': getattr(candidate, 'candidate_id', ''),
            'first_name': getattr(candidate, 'first_name', ''),
            'last_name': getattr(candidate, 'last_name', ''),
            'email': getattr(candidate, 'email', ''),
            'phone': getattr(candidate, 'phone', ''),
            'status': status_str,
            'application_date': getattr(candidate, 'application_date', ''),
            'resume_path': getattr(candidate, 'resume_path', ''),
            'notes': getattr(candidate, 'notes', []),
            'skills': [{'name': getattr(s, 'name', ''), 
                       'years_experience': getattr(s, 'years_experience', 0), 
                       'proficiency': getattr(s, 'proficiency', 0)} 
                      for s in getattr(candidate, 'skills', [])],
            'education': [{'degree': getattr(e, 'degree', ''), 
                          'field': getattr(e, 'field', ''), 
                          'institution': getattr(e, 'institution', ''), 
                          'year_completed': getattr(e, 'year_completed', 0), 
                          'gpa': getattr(e, 'gpa', None)} 
                         for e in getattr(candidate, 'education', [])],
            'experience': [{'title': getattr(exp, 'title', ''), 
                           'company': getattr(exp, 'company', ''), 
                           'start_date': getattr(exp, 'start_date', ''),
                           'end_date': getattr(exp, 'end_date', '') or "", 
                           'description': getattr(exp, 'description', ''),
                           'achievements': getattr(exp, 'achievements', [])}
                          for exp in getattr(candidate, 'experience', [])]
        }
    
    def _position_to_dict(self, position: 'JobPosition') -> Dict:
        """Convert JobPosition object to dictionary with proper type handling"""
        # Handle experience_level - it might be an enum or a string
        exp_level = position.experience_level
        if hasattr(exp_level, 'name'):  # It's an enum
            exp_level_str = exp_level.name
        else:  # It's already a string
            exp_level_str = str(exp_level)
        # Handle status - it might be an enum or a string
        status = position.status
        if hasattr(status, 'name'):  # It's an enum
            status_str = status.name
        else:  # It's already a string
            status_str = str(status)
        
        # Safely get attributes with defaults
        return {
            'position_id': getattr(position, 'position_id', ''),
            'title': getattr(position, 'title', ''),
            'department': getattr(position, 'department', ''),
            'location': getattr(position, 'location', ''),
            'experience_level': exp_level_str,
            'description': getattr(position, 'description', ''),
            'required_skills': [{'name': getattr(s, 'name', ''), 
                               'years_experience': getattr(s, 'years_experience', 0), 
                               'proficiency': getattr(s, 'proficiency', 0)}
                              for s in getattr(position, 'required_skills', [])],
            'preferred_skills': [{'name': getattr(s, 'name', ''), 
                                'years_experience': getattr(s, 'years_experience', 0), 
                                'proficiency': getattr(s, 'proficiency', 0)}
                               for s in getattr(position, 'preferred_skills', [])],
            'status': status_str,
            'hiring_manager': getattr(position, 'hiring_manager', '') or "",
            'salary_range': getattr(position, 'salary_range', None) or {},
            'open_date': getattr(position, 'open_date', ''),
            'close_date': getattr(position, 'close_date', '') or ""
        }
    
    def add_candidate(self, candidate_data: Dict) -> str:
        """Add a new candidate to the system"""
        candidate_id = f"CAN-{str(uuid.uuid4())[:8].upper()}"
        candidate = Candidate(
            candidate_id=candidate_id,
            **candidate_data
        )
        self.candidates[candidate_id] = candidate
        self._save_data()
        return candidate_id
    
    def create_job_position(self, position_data: Dict) -> str:
        """Create a new job position"""
        position_id = f"POS-{str(uuid.uuid4())[:8].upper()}"
        position = JobPosition(
            position_id=position_id,
            **position_data
        )
        self.positions[position_id] = position
        self._save_data()
        return position_id
    
    def get_candidate_matches(self, position_id: str, top_n: int = 5) -> List[Dict]:
        """Find the best matching candidates for a position"""
        if position_id not in self.positions:
            return []
        
        position = self.positions[position_id]
        required_skills = {s.name.lower() for s in position.required_skills}
        
        matches = []
        
        for candidate in self.candidates.values():
            if candidate.status not in [candidate_status.APPLIED, candidate_status.SCREENING]:
                continue
                
            candidate_skills = {s.name.lower(): s for s in candidate.skills}
            
            # Calculate match score
            match_score = 0
            matched_skills = []
            
            # Check required skills
            for req_skill in position.required_skills:
                skill_name = req_skill.name.lower()
                if skill_name in candidate_skills:
                    candidate_skill = candidate_skills[skill_name]
                    # Higher score for better proficiency and more experience
                    skill_score = (candidate_skill.proficiency / 5) * 0.6
                    skill_score += min(candidate_skill.years_experience / 10, 1) * 0.4
                    match_score += skill_score
                    matched_skills.append({
                        'skill': skill_name,
                        'match': f"{int(skill_score * 100)}%",
                        'years': candidate_skill.years_experience,
                        'proficiency': candidate_skill.proficiency
                    })
            
            # Only consider candidates who have at least one required skill
            if matched_skills:
                # Normalize score to 0-100
                normalized_score = (match_score / len(position.required_skills)) * 100
                
                matches.append({
                    'candidate_id': candidate.candidate_id,
                    'name': f"{candidate.first_name} {candidate.last_name}",
                    'email': candidate.email,
                    'match_score': round(normalized_score, 1),
                    'matched_skills': matched_skills,
                    'status': candidate.status.name,
                    'application_date': candidate.application_date
                })
        
        # Sort by match score in descending order
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matches[:top_n]
    
    def schedule_interview(self, candidate_id: str, position_id: str, 
                          interviewer: str, scheduled_time: str) -> bool:
        """Schedule an interview for a candidate"""
        if candidate_id not in self.candidates or position_id not in self.positions:
            return False
        
        # In a real app, you would integrate with a calendar API here
        interview_id = f"INT-{str(uuid.uuid4())[:8].upper()}"
        interview = {
            'interview_id': interview_id,
            'candidate_id': candidate_id,
            'position_id': position_id,
            'interviewer': interviewer,
            'scheduled_time': scheduled_time,
            'status': 'SCHEDULED',
            'notes': '',
            'created_at': datetime.now().isoformat()
        }
        
        self.interviews.append(interview)
        self.candidates[candidate_id].status = candidate_status.INTERVIEW_SCHEDULED
        self._save_data()
        
        # In a real app, send calendar invites here
        print(f"Interview scheduled for {self.candidates[candidate_id].first_name} "
              f"with {interviewer} on {scheduled_time}")
        
        return True

def main():
    """Example usage of the HR Assistant"""
    # Initialize the HR Assistant
    hr = HRAssistant()
    
    # Example: Create a job position
    job_data = {
        'title': 'Senior Software Engineer',
        'department': 'Engineering',
        'location': 'Remote',
        'experience_level': experience_level.SENIOR,
        'description': 'We are looking for an experienced software engineer...',
        'required_skills': [
            Skill(name='Python', years_experience=5, proficiency=4),
            Skill(name='Django', years_experience=3, proficiency=4),
            Skill(name='REST APIs', years_experience=3, proficiency=4),
        ],
        'preferred_skills': [
            Skill(name='AWS', years_experience=2, proficiency=3),
            Skill(name='Docker', years_experience=2, proficiency=3),
        ],
        'status': job_status.OPEN,
        'hiring_manager': 'John Doe',
        'salary_range': {'min': 120000, 'max': 150000}
    }
    
    position_id = hr.create_job_position(job_data)
    print(f"Created job position: {position_id}")
    
    # Example: Add a candidate
    candidate_data = {
        'first_name': 'Jane',
        'last_name': 'Smith',
        'email': 'jane.smith@example.com',
        'phone': '555-123-4567',
        'skills': [
            Skill(name='Python', years_experience=6, proficiency=5),
            Skill(name='Django', years_experience=4, proficiency=5),
            Skill(name='REST APIs', years_experience=4, proficiency=4),
            Skill(name='AWS', years_experience=2, proficiency=3),
            Skill(name='JavaScript', years_experience=3, proficiency=4),
        ],
        'education': [
            Education(
                degree='BSc',
                field='Computer Science',
                institution='Tech University',
                year_completed=2015,
                gpa=3.8
            )
        ],
        'experience': [
            WorkExperience(
                title='Senior Software Engineer',
                company='Tech Solutions Inc.',
                start_date='2019-01-01',
                end_date=None,  # Current position
                description='Leading development of web applications...',
                achievements=[
                    'Reduced API response time by 40%',
                    'Mentored 3 junior developers'
                ]
            ),
            WorkExperience(
                title='Software Engineer',
                company='WebDev Co.',
                start_date='2015-06-01',
                end_date='2018-12-31',
                description='Developed and maintained web applications...',
                achievements=[
                    'Implemented CI/CD pipeline reducing deployment time by 60%'
                ]
            )
        ],
        'status': candidate_status.APPLIED
    }
    
    candidate_id = hr.add_candidate(candidate_data)
    print(f"Added candidate: {candidate_id}")
    
    # Find matching candidates for the position
    print("\nFinding matching candidates...")
    matches = hr.get_candidate_matches(position_id)
    
    if matches:
        print("\nTop matching candidates:")
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match['name']} ({match['email']}) - {match['match_score']}% match")
            print(f"   Status: {match['status']}")
            print(f"   Matched skills:")
            for skill in match['matched_skills']:
                print(f"   - {skill['skill']}: {skill['match']} "
                      f"({skill['years']} years, proficiency: {skill['proficiency']}/5)")
        
        # Schedule an interview with the top candidate
        top_candidate = matches[0]
        interview_time = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d 10:00")
        
        if hr.schedule_interview(
            candidate_id=top_candidate['candidate_id'],
            position_id=position_id,
            interviewer='John Doe',
            scheduled_time=interview_time
        ):
            print(f"\nSuccessfully scheduled interview for {top_candidate['name']}")
    else:
        print("No matching candidates found.")

if __name__ == "__main__":
    main()
