"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    activities.clear()
    activities.update({
        "Soccer": {
            "description": "Team sport focusing on soccer skills and competitive play",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
            "participants": ["alex@mergington.edu"]
        },
        "Basketball": {
            "description": "Basketball training and intramural games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu", "sarah@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore various art mediums including painting, drawing, and sculpture",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": ["isabella@mergington.edu"]
        },
        "Music Ensemble": {
            "description": "Join the school orchestra and perform in concerts",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 25,
            "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and critical thinking skills through competitive debate",
            "schedule": "Mondays and Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 10,
            "participants": ["andrew@mergington.edu"]
        },
        "Math Club": {
            "description": "Solve challenging math problems and prepare for competitions",
            "schedule": "Saturdays, 10:00 AM - 11:30 AM",
            "max_participants": 18,
            "participants": ["ryan@mergington.edu", "grace@mergington.edu"]
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


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Soccer" in activities
        assert "Basketball" in activities

    def test_get_activities_has_correct_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        activities = response.json()
        soccer = activities["Soccer"]
        
        assert "description" in soccer
        assert "schedule" in soccer
        assert "max_participants" in soccer
        assert "participants" in soccer
        assert isinstance(soccer["participants"], list)

    def test_get_activities_includes_existing_participants(self, client):
        """Test that activities include existing participants"""
        response = client.get("/activities")
        activities = response.json()
        
        assert "alex@mergington.edu" in activities["Soccer"]["participants"]
        assert "james@mergington.edu" in activities["Basketball"]["participants"]


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Soccer/signup?email=newuser@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up newuser@mergington.edu for Soccer" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        client.post("/activities/Soccer/signup?email=newuser@mergington.edu")
        
        response = client.get("/activities")
        activities = response.json()
        assert "newuser@mergington.edu" in activities["Soccer"]["participants"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up with a duplicate email fails"""
        response = client.post(
            "/activities/Soccer/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/Nonexistent/signup?email=newuser@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_signup_at_capacity_fails(self, client):
        """Test that signing up for a full activity fails"""
        # Debate Team has max 10 and only 1 participant
        from app import activities
        # Fill it up
        for i in range(9):
            activities["Debate Team"]["participants"].append(f"user{i}@mergington.edu")
        
        response = client.post(
            "/activities/Debate Team/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "full capacity" in data["detail"]

    def test_signup_decreases_availability(self, client):
        """Test that signup decreases available spots"""
        response_before = client.get("/activities")
        soccer_before = response_before.json()["Soccer"]
        spots_before = soccer_before["max_participants"] - len(soccer_before["participants"])
        
        client.post("/activities/Soccer/signup?email=newuser@mergington.edu")
        
        response_after = client.get("/activities")
        soccer_after = response_after.json()["Soccer"]
        spots_after = soccer_after["max_participants"] - len(soccer_after["participants"])
        
        assert spots_after == spots_before - 1


class TestUnregister:
    """Test the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, client):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Soccer/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered alex@mergington.edu from Soccer" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        client.delete("/activities/Soccer/unregister?email=alex@mergington.edu")
        
        response = client.get("/activities")
        activities = response.json()
        assert "alex@mergington.edu" not in activities["Soccer"]["participants"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from a non-existent activity fails"""
        response = client.delete(
            "/activities/Nonexistent/unregister?email=someone@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"]

    def test_unregister_not_signed_up_fails(self, client):
        """Test that unregistering a non-participant fails"""
        response = client.delete(
            "/activities/Soccer/unregister?email=notasignup@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_increases_availability(self, client):
        """Test that unregister increases available spots"""
        response_before = client.get("/activities")
        soccer_before = response_before.json()["Soccer"]
        spots_before = soccer_before["max_participants"] - len(soccer_before["participants"])
        
        client.delete("/activities/Soccer/unregister?email=alex@mergington.edu")
        
        response_after = client.get("/activities")
        soccer_after = response_after.json()["Soccer"]
        spots_after = soccer_after["max_participants"] - len(soccer_after["participants"])
        
        assert spots_after == spots_before + 1


class TestRootRedirect:
    """Test the root endpoint"""

    def test_root_redirects_to_static(self, client):
        """Test that root URL redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
