import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [currentSession, setCurrentSession] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);

  const startDiagnosis = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/start-diagnosis`);
      setCurrentSession(response.data);
      setShowResults(false);
      setDiagnosis(null);
    } catch (error) {
      console.error('Error starting diagnosis:', error);
      alert('Failed to start diagnosis. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const answerQuestion = async (answer) => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/answer-question`, {
        session_id: currentSession.session_id,
        answer: answer
      });
      
      if (response.data.is_complete) {
        setDiagnosis(response.data);
        setShowResults(true);
      } else {
        setCurrentSession(response.data);
      }
    } catch (error) {
      console.error('Error answering question:', error);
      alert('Failed to process your answer. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetDiagnosis = () => {
    setCurrentSession(null);
    setShowResults(false);
    setDiagnosis(null);
  };

  const WelcomeScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="max-w-4xl w-full text-center">
        <div className="mb-8">
          <img 
            src="https://images.unsplash.com/photo-1576091160550-2173dba999ef" 
            alt="Medical AI Assistant" 
            className="mx-auto rounded-2xl shadow-2xl mb-8 w-full max-w-2xl h-64 object-cover"
          />
        </div>
        
        <h1 className="text-5xl font-bold text-gray-800 mb-6">
          🩺 Medical AI Assistant
        </h1>
        
        <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
          I'm your intelligent medical diagnosis assistant, similar to Akinator but for health conditions! 
          I'll ask you strategic questions to help identify your medical issues and provide recommendations.
        </p>
        
        <div className="bg-white rounded-2xl p-8 shadow-xl mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-4xl mb-3">🤔</div>
              <h3 className="font-semibold text-gray-700">Smart Questions</h3>
              <p className="text-gray-600">I'll ask intelligent yes/no questions about your symptoms</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">🧠</div>
              <h3 className="font-semibold text-gray-700">AI Analysis</h3>
              <p className="text-gray-600">AI analyzes your responses to narrow down possibilities</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">💊</div>
              <h3 className="font-semibold text-gray-700">Recommendations</h3>
              <p className="text-gray-600">Get medicine, exercise, and doctor recommendations</p>
            </div>
          </div>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
          <p className="text-yellow-800 font-medium">
            ⚠️ Medical Disclaimer: This is an AI assistant for educational purposes. 
            Always consult with qualified healthcare professionals for actual medical advice.
          </p>
        </div>
        
        <button 
          onClick={startDiagnosis}
          disabled={isLoading}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-full text-xl transition-colors duration-200 disabled:opacity-50"
        >
          {isLoading ? 'Starting...' : 'Start Diagnosis 🚀'}
        </button>
      </div>
    </div>
  );

  const QuestionScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100 flex items-center justify-center px-4">
      <div className="max-w-3xl w-full">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🤔</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Medical Question</h2>
            <div className="bg-gray-200 rounded-full h-4 mb-6">
              <div 
                className="bg-blue-600 h-4 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(currentSession?.confidence_score * 100, 100)}%` }}
              ></div>
            </div>
            <p className="text-gray-600">Confidence: {Math.round(currentSession?.confidence_score * 100)}%</p>
          </div>
          
          <div className="mb-8">
            <div className="bg-blue-50 border-l-4 border-blue-400 p-6 rounded-r-lg">
              <p className="text-xl text-gray-800 font-medium">{currentSession?.question}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button 
              onClick={() => answerQuestion('yes')}
              disabled={isLoading}
              className="bg-green-500 hover:bg-green-600 text-white font-bold py-4 px-6 rounded-xl transition-colors duration-200 disabled:opacity-50"
            >
              ✅ Yes
            </button>
            <button 
              onClick={() => answerQuestion('no')}
              disabled={isLoading}
              className="bg-red-500 hover:bg-red-600 text-white font-bold py-4 px-6 rounded-xl transition-colors duration-200 disabled:opacity-50"
            >
              ❌ No
            </button>
            <button 
              onClick={() => answerQuestion('maybe')}
              disabled={isLoading}
              className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-4 px-6 rounded-xl transition-colors duration-200 disabled:opacity-50"
            >
              🤷 Maybe
            </button>
            <button 
              onClick={() => answerQuestion('unsure')}
              disabled={isLoading}
              className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-4 px-6 rounded-xl transition-colors duration-200 disabled:opacity-50"
            >
              ❓ Unsure
            </button>
          </div>
          
          <div className="mt-8 text-center">
            <button 
              onClick={resetDiagnosis}
              className="text-gray-600 hover:text-gray-800 font-medium transition-colors duration-200"
            >
              🔄 Start Over
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const ResultsScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 flex items-center justify-center px-4">
      <div className="max-w-4xl w-full">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🎯</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Diagnosis Complete!</h2>
            <div className="bg-green-200 rounded-full h-4 mb-4">
              <div 
                className="bg-green-600 h-4 rounded-full transition-all duration-300"
                style={{ width: `${Math.round(diagnosis?.confidence_score * 100)}%` }}
              ></div>
            </div>
            <p className="text-gray-600">Confidence: {Math.round(diagnosis?.confidence_score * 100)}%</p>
          </div>
          
          <div className="mb-8">
            <div className="bg-blue-50 border-l-4 border-blue-400 p-6 rounded-r-lg mb-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-2">🏥 Diagnosis</h3>
              <p className="text-gray-700">{diagnosis?.final_diagnosis}</p>
            </div>
            
            {diagnosis?.recommendations && (
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-green-800 mb-3">💊 Recommended Medicines</h4>
                  <ul className="space-y-2">
                    {diagnosis.recommendations.medicines?.map((medicine, index) => (
                      <li key={index} className="text-green-700 flex items-center">
                        <span className="mr-2">•</span>
                        {medicine}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-purple-800 mb-3">🏃‍♂️ Recommended Exercises</h4>
                  <ul className="space-y-2">
                    {diagnosis.recommendations.exercises?.map((exercise, index) => (
                      <li key={index} className="text-purple-700 flex items-center">
                        <span className="mr-2">•</span>
                        {exercise}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-blue-800 mb-3">👨‍⚕️ Doctor Specialization</h4>
                  <p className="text-blue-700">{diagnosis.recommendations.doctor_specialization}</p>
                </div>
                
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">ℹ️ Description</h4>
                  <p className="text-gray-700">{diagnosis.recommendations.description}</p>
                </div>
              </div>
            )}
          </div>
          
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 font-medium">
              {diagnosis?.recommendations?.disclaimer}
            </p>
          </div>
          
          <div className="text-center">
            <button 
              onClick={resetDiagnosis}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-full text-xl transition-colors duration-200 mr-4"
            >
              🔄 New Diagnosis
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  if (showResults) {
    return <ResultsScreen />;
  }
  
  if (currentSession) {
    return <QuestionScreen />;
  }
  
  return <WelcomeScreen />;
};

export default App;