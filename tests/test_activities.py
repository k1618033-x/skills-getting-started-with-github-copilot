"""
Test suite for FastAPI endpoints in src/app.py
"""

import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client: TestClient) -> None:
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities

    def test_get_activities_has_correct_structure(self, client: TestClient) -> None:
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_includes_participants(self, client: TestClient) -> None:
        """Test that activities include their current participants"""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client: TestClient) -> None:
        """Test successful signup for a new participant"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "signed up" in data["message"].lower()
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_new_participant_updates_participants(self, client: TestClient) -> None:
        """Test that signup actually adds participant to activity"""
        # Signup new participant
        client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        assert "newstudent@mergington.edu" in chess_club["participants"]

    def test_signup_duplicate_participant_fails(self, client: TestClient) -> None:
        """Test that duplicate signup returns 400 error"""
        # Try to signup already registered participant
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already" in data["detail"].lower()

    def test_signup_invalid_activity_fails(self, client: TestClient) -> None:
        """Test that signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_signup_multiple_activities(self, client: TestClient) -> None:
        """Test that same student can signup for different activities"""
        email = "multistudent@mergington.edu"
        
        # Signup for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Signup for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify both signups succeeded
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_participant_success(self, client: TestClient) -> None:
        """Test successful unregistration of participant"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "unregistered" in data["message"].lower()

    def test_unregister_participant_removes_from_activity(self, client: TestClient) -> None:
        """Test that unregister actually removes participant from activity"""
        # Unregister participant
        client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        assert "michael@mergington.edu" not in chess_club["participants"]

    def test_unregister_not_enrolled_fails(self, client: TestClient) -> None:
        """Test that unregistering non-enrolled participant returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notstudent@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()

    def test_unregister_invalid_activity_fails(self, client: TestClient) -> None:
        """Test that unregister for non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_unregister_then_signup_again(self, client: TestClient) -> None:
        """Test that participant can signup again after unregistering"""
        email = "student@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Verify unregistered
        activities = client.get("/activities").json()
        assert email not in activities[activity]["participants"]
        
        # Signup again
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signed up again
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]


class TestRoot:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static(self, client: TestClient) -> None:
        """Test that root path redirects to static index page"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code in [301, 302, 307, 308]  # Redirect status codes
        assert "location" in response.headers
