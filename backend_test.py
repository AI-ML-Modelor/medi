#!/usr/bin/env python3
import requests
import json
import time
import unittest
import os
import sys
import base64
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from frontend/.env to get the backend URL
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL has the /api prefix
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

class MedicalDiagnosisBackendTest(unittest.TestCase):
    """Test suite for the Medical Diagnosis Backend API"""

    def test_01_medical_conditions_endpoint(self):
        """Test the /conditions endpoint to verify medical knowledge base"""
        print("\n=== Testing Medical Conditions Endpoint ===")
        response = requests.get(f"{API_URL}/conditions")
        
        self.assertEqual(response.status_code, 200, "Failed to get medical conditions")
        
        conditions = response.json()
        self.assertIsInstance(conditions, list, "Conditions should be a list")
        self.assertGreaterEqual(len(conditions), 5, "Should have at least 5 medical conditions")
        
        # Verify condition structure
        for condition in conditions:
            self.assertIn("name", condition, "Condition should have a name")
            self.assertIn("symptoms", condition, "Condition should have symptoms")
            self.assertIn("medicines", condition, "Condition should have medicines")
            self.assertIn("exercises", condition, "Condition should have exercises")
            self.assertIn("doctor_specialization", condition, "Condition should have doctor specialization")
            
        print(f"✅ Successfully retrieved {len(conditions)} medical conditions")
        return conditions

    def test_02_start_diagnosis(self):
        """Test the /start-diagnosis endpoint to start a new diagnosis session"""
        print("\n=== Testing Start Diagnosis Endpoint ===")
        response = requests.post(f"{API_URL}/start-diagnosis")
        
        self.assertEqual(response.status_code, 200, "Failed to start diagnosis")
        
        data = response.json()
        self.assertIn("session_id", data, "Response should contain session_id")
        self.assertIn("question", data, "Response should contain a question")
        self.assertIsNotNone(data["question"], "Question should not be None")
        self.assertFalse(data["is_complete"], "Diagnosis should not be complete at start")
        
        print(f"✅ Successfully started diagnosis session: {data['session_id']}")
        print(f"Initial question: {data['question']}")
        
        return data["session_id"], data["question"]

    def test_03_answer_question_flow(self):
        """Test the /answer-question endpoint with a multi-turn conversation flow"""
        print("\n=== Testing Answer Question Flow ===")
        
        # Start a new diagnosis
        session_id, first_question = self.test_02_start_diagnosis()
        
        # Simulate a conversation with 3-5 turns
        answers = ["yes", "no", "maybe", "unsure", "yes"]
        conversation_history = [f"Q: {first_question}"]
        
        for i, answer in enumerate(answers[:3]):  # Use first 3 answers for testing
            print(f"\nTurn {i+1}: Answering '{answer}' to question")
            
            response = requests.post(
                f"{API_URL}/answer-question",
                json={"session_id": session_id, "answer": answer}
            )
            
            self.assertEqual(response.status_code, 200, f"Failed to process answer on turn {i+1}")
            
            data = response.json()
            self.assertIn("session_id", data, "Response should contain session_id")
            
            if data["is_complete"]:
                print(f"Diagnosis completed after {i+1} turns")
                self.assertIn("final_diagnosis", data, "Complete diagnosis should have final_diagnosis")
                self.assertIn("recommendations", data, "Complete diagnosis should have recommendations")
                
                # Verify recommendations structure
                recommendations = data["recommendations"]
                self.assertIn("medicines", recommendations, "Recommendations should include medicines")
                self.assertIn("exercises", recommendations, "Recommendations should include exercises")
                self.assertIn("doctor_specialization", recommendations, "Recommendations should include doctor specialization")
                self.assertIn("disclaimer", recommendations, "Recommendations should include medical disclaimer")
                
                print(f"Final diagnosis: {data['final_diagnosis']}")
                print(f"Recommended medicines: {recommendations['medicines']}")
                print(f"Recommended exercises: {recommendations['exercises']}")
                print(f"Doctor specialization: {recommendations['doctor_specialization']}")
                break
            else:
                self.assertIn("question", data, "Response should contain next question")
                self.assertIsNotNone(data["question"], "Question should not be None")
                conversation_history.append(f"A: {answer}")
                conversation_history.append(f"Q: {data['question']}")
                print(f"Next question: {data['question']}")
        
        return session_id

    def test_04_session_persistence(self):
        """Test session persistence in MongoDB by retrieving a session"""
        print("\n=== Testing Session Persistence ===")
        
        # First create a session through the normal flow
        session_id = self.test_03_answer_question_flow()
        
        # Now retrieve the session directly
        response = requests.get(f"{API_URL}/session/{session_id}")
        
        self.assertEqual(response.status_code, 200, "Failed to retrieve session")
        
        session_data = response.json()
        self.assertEqual(session_data["session_id"], session_id, "Retrieved session ID should match")
        self.assertIn("user_responses", session_data, "Session should contain user_responses")
        self.assertGreater(len(session_data["user_responses"]), 0, "Session should have recorded responses")
        
        print(f"✅ Successfully retrieved session {session_id} from database")
        print(f"Session contains {len(session_data['user_responses'])} user responses")
        
        return session_data

    def test_05_error_handling(self):
        """Test API error handling for invalid requests"""
        print("\n=== Testing Error Handling ===")
        
        # Test invalid session ID
        invalid_session_id = "invalid-session-id"
        response = requests.get(f"{API_URL}/session/{invalid_session_id}")
        self.assertEqual(response.status_code, 404, "Should return 404 for invalid session ID")
        
        # Test invalid answer format
        response = requests.post(
            f"{API_URL}/answer-question",
            json={"session_id": invalid_session_id}  # Missing 'answer' field
        )
        self.assertNotEqual(response.status_code, 200, "Should not accept request with missing fields")
        
        print("✅ Error handling tests passed")

    def test_06_gemini_integration(self):
        """Test Gemini LLM integration by verifying response quality"""
        print("\n=== Testing Gemini LLM Integration ===")
        
        # Start a new diagnosis
        session_id, first_question = self.test_02_start_diagnosis()
        
        # Check if the first question is meaningful and related to medical diagnosis
        self.assertGreater(len(first_question), 20, "Question should be substantial")
        
        medical_keywords = ["symptom", "pain", "feel", "experience", "health", "medical", "condition"]
        has_medical_context = any(keyword in first_question.lower() for keyword in medical_keywords)
        self.assertTrue(has_medical_context, "Question should have medical context")
        
        # Test a follow-up question to check conversation continuity
        response = requests.post(
            f"{API_URL}/answer-question",
            json={"session_id": session_id, "answer": "yes"}
        )
        
        self.assertEqual(response.status_code, 200, "Failed to get follow-up question")
        
        data = response.json()
        follow_up_question = data.get("question")
        
        if follow_up_question:  # If not yet complete
            self.assertNotEqual(first_question, follow_up_question, "Follow-up should be different from first question")
            self.assertGreater(len(follow_up_question), 20, "Follow-up question should be substantial")
            
            # Check if follow-up builds on the previous answer
            context_keywords = ["mentioned", "said", "indicated", "reported", "earlier", "previous"]
            has_context_awareness = any(keyword in follow_up_question.lower() for keyword in context_keywords)
            
            print(f"First question: {first_question}")
            print(f"Follow-up question: {follow_up_question}")
            print(f"Context awareness detected: {has_context_awareness}")
        else:
            # If diagnosis completed after one question (unlikely but possible)
            self.assertTrue(data["is_complete"], "Should be marked as complete if no follow-up question")
            print("Diagnosis completed after single question (unusual but possible)")
        
        print("✅ Gemini LLM integration test passed")

def run_tests():
    """Run all tests in sequence"""
    test_suite = unittest.TestSuite()
    test_suite.addTest(MedicalDiagnosisBackendTest('test_01_medical_conditions_endpoint'))
    test_suite.addTest(MedicalDiagnosisBackendTest('test_02_start_diagnosis'))
    test_suite.addTest(MedicalDiagnosisBackendTest('test_03_answer_question_flow'))
    test_suite.addTest(MedicalDiagnosisBackendTest('test_04_session_persistence'))
    test_suite.addTest(MedicalDiagnosisBackendTest('test_05_error_handling'))
    test_suite.addTest(MedicalDiagnosisBackendTest('test_06_gemini_integration'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)

if __name__ == "__main__":
    run_tests()