"""
Test suite for Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Basketball": {
            "description": "Team-based basketball games and skill development",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["alex@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis techniques and compete in matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:00 PM",
            "max_participants": 10,
            "participants": ["james@mergington.edu"]
        },
        "Art Studio": {
            "description": "Painting, drawing, and mixed media art projects",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["grace@mergington.edu"]
        },
        "Drama Club": {
            "description": "Theater productions, improv, and performance arts",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 25,
            "participants": ["noah@mergington.edu", "ava@mergington.edu"]
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    yield


class TestRoot:
    """Tests for root endpoint"""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for getting activities list"""

    def test_get_all_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball" in data
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activities_structure(self, client):
        """Test that activities have correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Basketball"]
        
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)

    def test_initial_participants(self, client):
        """Test that initial participants are correctly set"""
        response = client.get("/activities")
        data = response.json()
        
        assert "alex@mergington.edu" in data["Basketball"]["participants"]
        assert "james@mergington.edu" in data["Tennis Club"]["participants"]
        assert len(data["Drama Club"]["participants"]) == 2


class TestSignupForActivity:
    """Tests for signing up for activities"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_reflects_in_activity_list(self, client):
        """Test that signup updates the activity list"""
        # Sign up
        response = client.post(
            "/activities/Tennis%20Club/signup?email=newsignup@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify in activities list
        response = client.get("/activities")
        data = response.json()
        assert "newsignup@mergington.edu" in data["Tennis Club"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/NonExistent/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_duplicate_signup(self, client):
        """Test that student cannot sign up twice for same activity"""
        # First signup
        response = client.post(
            "/activities/Basketball/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 200
        
        # Try to sign up again
        response = client.post(
            "/activities/Basketball/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_already_registered_student(self, client):
        """Test that already registered student cannot sign up again"""
        response = client.post(
            "/activities/Basketball/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_multiple_signups_different_activities(self, client):
        """Test that same student can sign up for multiple activities"""
        student_email = "multiactivity@mergington.edu"
        
        # Sign up for Basketball
        response1 = client.post(
            f"/activities/Basketball/signup?email={student_email}"
        )
        assert response1.status_code == 200
        
        # Sign up for Chess Club
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={student_email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        data = response.json()
        assert student_email in data["Basketball"]["participants"]
        assert student_email in data["Chess Club"]["participants"]

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with email containing special characters"""
        response = client.post(
            "/activities/Art%20Studio/signup?email=student.test@mergington.edu"
        )
        assert response.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert "student.test@mergington.edu" in data["Art Studio"]["participants"]

    def test_signup_activity_name_with_spaces(self, client):
        """Test signup for activity names with spaces"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=coder@mergington.edu"
        )
        assert response.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert "coder@mergington.edu" in data["Programming Class"]["participants"]


class TestActivityConstraints:
    """Tests for activity constraints and validations"""

    def test_activity_max_participants(self, client):
        """Test that activity structure includes max participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert activity_data["max_participants"] > 0

    def test_participant_count(self, client):
        """Test that participant count matches actual participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            participants = activity_data["participants"]
            assert len(participants) > 0  # All activities start with at least one participant
