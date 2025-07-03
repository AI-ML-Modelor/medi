import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [activeSection, setActiveSection] = useState('home');
  const [currentSession, setCurrentSession] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);
  const [uploadedDoc, setUploadedDoc] = useState(null);
  const [medicineQuery, setMedicineQuery] = useState('');
  const [exerciseQuery, setExerciseQuery] = useState('');
  const [medicineResults, setMedicineResults] = useState(null);
  const [exerciseResults, setExerciseResults] = useState(null);
  const [medicineSuggestions, setMedicineSuggestions] = useState([]);
  const [exerciseSuggestions, setExerciseSuggestions] = useState([]);
  const [showMedicineSuggestions, setShowMedicineSuggestions] = useState(false);
  const [showExerciseSuggestions, setShowExerciseSuggestions] = useState(false);
  const [allConditions, setAllConditions] = useState([]);

  const startDiagnosis = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/start-diagnosis`);
      setCurrentSession(response.data);
      setShowResults(false);
      setDiagnosis(null);
      setActiveSection('diagnosis');
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

  const handleFileUpload = async (file) => {
    if (!file) return;
    
    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/upload-medical-document`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadedDoc(response.data);
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const searchMedicine = async () => {
    if (!medicineQuery.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/get-medicine-suggestions`, {
        disease_name: medicineQuery
      });
      setMedicineResults(response.data);
    } catch (error) {
      console.error('Error searching medicine:', error);
      alert('Failed to get medicine suggestions.');
    } finally {
      setIsLoading(false);
    }
  };

  const searchExercise = async () => {
    if (!exerciseQuery.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post(`${API}/get-exercise-suggestions`, {
        condition: exerciseQuery
      });
      setExerciseResults(response.data);
    } catch (error) {
      console.error('Error searching exercise:', error);
      alert('Failed to get exercise suggestions.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetToHome = () => {
    setActiveSection('home');
    setCurrentSession(null);
    setShowResults(false);
    setDiagnosis(null);
    setUploadedDoc(null);
    setMedicineResults(null);
    setExerciseResults(null);
    setMedicineQuery('');
    setExerciseQuery('');
  };

  const NavigationBar = () => (
    <nav className="bg-white shadow-lg border-b-4 border-blue-500">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <div className="text-2xl font-bold text-blue-600">🩺 Medical AI Assistant</div>
          </div>
          <div className="flex space-x-8 items-center">
            <button 
              onClick={() => setActiveSection('home')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeSection === 'home' ? 'text-blue-600 bg-blue-50' : 'text-gray-700 hover:text-blue-600'}`}
            >
              🏠 Home
            </button>
            <button 
              onClick={() => setActiveSection('diagnosis')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeSection === 'diagnosis' ? 'text-blue-600 bg-blue-50' : 'text-gray-700 hover:text-blue-600'}`}
            >
              🤔 AI Diagnosis
            </button>
            <button 
              onClick={() => setActiveSection('upload')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeSection === 'upload' ? 'text-blue-600 bg-blue-50' : 'text-gray-700 hover:text-blue-600'}`}
            >
              📄 Upload Report
            </button>
            <button 
              onClick={() => setActiveSection('medicine')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeSection === 'medicine' ? 'text-blue-600 bg-blue-50' : 'text-gray-700 hover:text-blue-600'}`}
            >
              💊 Medicines
            </button>
            <button 
              onClick={() => setActiveSection('exercise')}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${activeSection === 'exercise' ? 'text-blue-600 bg-blue-50' : 'text-gray-700 hover:text-blue-600'}`}
            >
              🏃‍♂️ Exercise & Diet
            </button>
          </div>
        </div>
      </div>
    </nav>
  );

  const HomeScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 pt-16">
      <div className="max-w-6xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <img 
            src="https://images.unsplash.com/photo-1576091160550-2173dba999ef" 
            alt="Medical AI Assistant" 
            className="mx-auto rounded-2xl shadow-2xl mb-8 w-full max-w-4xl h-80 object-cover"
          />
          
          <h1 className="text-6xl font-bold text-gray-800 mb-6">
            🩺 Enhanced Medical AI Assistant
          </h1>
          
          <p className="text-xl text-gray-600 mb-8 max-w-4xl mx-auto">
            Your comprehensive medical companion! Get AI-powered diagnosis through intelligent questioning, 
            upload medical reports for analysis, find medicine recommendations, and get personalized exercise & diet plans.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-12">
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-shadow cursor-pointer" onClick={() => setActiveSection('diagnosis')}>
            <div className="text-5xl mb-4 text-center">🤔</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3 text-center">AI Diagnosis</h3>
            <p className="text-gray-600 text-center">Akinator-style medical diagnosis through intelligent questions</p>
          </div>
          
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-shadow cursor-pointer" onClick={() => setActiveSection('upload')}>
            <div className="text-5xl mb-4 text-center">📄</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3 text-center">Upload Reports</h3>
            <p className="text-gray-600 text-center">Upload PDF/image medical reports for AI analysis</p>
          </div>
          
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-shadow cursor-pointer" onClick={() => setActiveSection('medicine')}>
            <div className="text-5xl mb-4 text-center">💊</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3 text-center">Medicine Guide</h3>
            <p className="text-gray-600 text-center">Get medicine suggestions with dosages and precautions</p>
          </div>
          
          <div className="bg-white rounded-2xl p-8 shadow-xl hover:shadow-2xl transition-shadow cursor-pointer" onClick={() => setActiveSection('exercise')}>
            <div className="text-5xl mb-4 text-center">🏃‍♂️</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3 text-center">Exercise & Diet</h3>
            <p className="text-gray-600 text-center">Personalized exercise and diet recommendations</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-xl mb-8">
          <h2 className="text-3xl font-semibold text-gray-800 mb-6 text-center">Enhanced Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl mb-3">🧠</div>
              <h3 className="font-semibold text-gray-700 mb-2">Advanced AI Analysis</h3>
              <p className="text-gray-600">Powered by Google Gemini 2.0 Flash for accurate medical insights</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">📋</div>
              <h3 className="font-semibold text-gray-700 mb-2">Comprehensive Database</h3>
              <p className="text-gray-600">10+ medical conditions with detailed treatment plans</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">🔍</div>
              <h3 className="font-semibold text-gray-700 mb-2">OCR Document Analysis</h3>
              <p className="text-gray-600">Upload and analyze medical reports with AI-powered OCR</p>
            </div>
          </div>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 mb-8">
          <p className="text-yellow-800 font-medium text-center">
            ⚠️ Medical Disclaimer: This AI assistant is for educational and informational purposes only. 
            Always consult with qualified healthcare professionals for actual medical advice, diagnosis, and treatment.
          </p>
        </div>
        
        <div className="text-center">
          <button 
            onClick={startDiagnosis}
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-full text-xl transition-colors duration-200 disabled:opacity-50 mr-4"
          >
            {isLoading ? 'Starting...' : 'Start AI Diagnosis 🚀'}
          </button>
          <button 
            onClick={() => setActiveSection('upload')}
            className="bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-8 rounded-full text-xl transition-colors duration-200"
          >
            Upload Report 📄
          </button>
        </div>
      </div>
    </div>
  );

  const DiagnosisScreen = () => {
    if (showResults) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 pt-16">
          <div className="max-w-4xl mx-auto px-4 py-8">
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
                          <li key={index} className="text-green-700 flex items-start">
                            <span className="mr-2 mt-1">•</span>
                            {medicine}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                      <h4 className="text-lg font-semibold text-purple-800 mb-3">🏃‍♂️ Recommended Exercises</h4>
                      <ul className="space-y-2">
                        {diagnosis.recommendations.exercises?.map((exercise, index) => (
                          <li key={index} className="text-purple-700 flex items-start">
                            <span className="mr-2 mt-1">•</span>
                            {exercise}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    {diagnosis.recommendations.diet && (
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
                        <h4 className="text-lg font-semibold text-orange-800 mb-3">🥗 Dietary Guidelines</h4>
                        <ul className="space-y-2">
                          {diagnosis.recommendations.diet?.map((diet, index) => (
                            <li key={index} className="text-orange-700 flex items-start">
                              <span className="mr-2 mt-1">•</span>
                              {diet}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                      <h4 className="text-lg font-semibold text-blue-800 mb-3">👨‍⚕️ Doctor Specialization</h4>
                      <p className="text-blue-700">{diagnosis.recommendations.doctor_specialization}</p>
                      <div className="mt-3">
                        <h5 className="font-medium text-blue-800">Description:</h5>
                        <p className="text-blue-700 text-sm">{diagnosis.recommendations.description}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
                <p className="text-red-800 font-medium">
                  {diagnosis?.recommendations?.disclaimer}
                </p>
              </div>
              
              <div className="text-center space-x-4">
                <button 
                  onClick={() => {
                    setCurrentSession(null);
                    setShowResults(false);
                    setDiagnosis(null);
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-full transition-colors duration-200"
                >
                  🔄 New Diagnosis
                </button>
                <button 
                  onClick={resetToHome}
                  className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-full transition-colors duration-200"
                >
                  🏠 Back to Home
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    if (currentSession) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100 pt-16">
          <div className="max-w-3xl mx-auto px-4 py-8">
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
              
              <div className="mt-8 text-center space-x-4">
                <button 
                  onClick={() => {
                    setCurrentSession(null);
                    setShowResults(false);
                    setDiagnosis(null);
                  }}
                  className="text-gray-600 hover:text-gray-800 font-medium transition-colors duration-200"
                >
                  🔄 Start Over
                </button>
                <button 
                  onClick={resetToHome}
                  className="text-gray-600 hover:text-gray-800 font-medium transition-colors duration-200"
                >
                  🏠 Back to Home
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 pt-16">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-white rounded-2xl shadow-2xl p-8 text-center">
            <div className="text-6xl mb-6">🤔</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-6">AI Medical Diagnosis</h2>
            <p className="text-xl text-gray-600 mb-8">
              Start your intelligent medical consultation. Our AI will ask strategic questions to help diagnose your condition.
            </p>
            <button 
              onClick={startDiagnosis}
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-full text-xl transition-colors duration-200 disabled:opacity-50"
            >
              {isLoading ? 'Starting...' : 'Begin Diagnosis 🚀'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  const UploadScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 pt-16">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">📄</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Upload Medical Report</h2>
            <p className="text-gray-600">Upload PDF or image files of medical reports for AI analysis</p>
          </div>

          <div className="border-2 border-dashed border-blue-300 rounded-xl p-8 mb-8 text-center">
            <input
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => handleFileUpload(e.target.files[0])}
              className="hidden"
              id="file-upload"
              disabled={isLoading}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="text-4xl mb-4">📤</div>
              <p className="text-xl text-gray-700 mb-2">Click to upload medical report</p>
              <p className="text-gray-500">Supports PDF, PNG, JPG, JPEG files</p>
            </label>
          </div>

          {uploadedDoc && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-green-800 mb-4">📋 Analysis Results</h3>
              
              <div className="mb-4">
                <h4 className="font-medium text-gray-800 mb-2">File: {uploadedDoc.filename}</h4>
              </div>

              <div className="mb-6">
                <h4 className="font-medium text-gray-800 mb-2">🔍 AI Analysis:</h4>
                <div className="bg-white p-4 rounded border">
                  <p className="text-gray-700">{uploadedDoc.analysis?.analysis || 'Analysis completed'}</p>
                </div>
              </div>

              {uploadedDoc.recommendations && (
                <div className="mb-6">
                  <h4 className="font-medium text-gray-800 mb-2">💡 AI Recommendations:</h4>
                  <div className="bg-blue-50 p-4 rounded border">
                    <p className="text-gray-700">{uploadedDoc.recommendations.ai_recommendations}</p>
                  </div>
                </div>
              )}

              <div className="mb-4">
                <h4 className="font-medium text-gray-800 mb-2">📝 Extracted Text:</h4>
                <textarea
                  value={uploadedDoc.extracted_text}
                  readOnly
                  rows={8}
                  className="w-full p-3 border rounded-lg bg-gray-50 text-sm"
                />
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                <p className="text-yellow-800 text-sm">
                  ⚠️ {uploadedDoc.recommendations?.disclaimer || 'This analysis is for informational purposes. Consult your doctor.'}
                </p>
              </div>
            </div>
          )}

          <div className="text-center">
            <button 
              onClick={resetToHome}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-full transition-colors duration-200"
            >
              🏠 Back to Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const MedicineScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-blue-100 pt-16">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">💊</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Medicine Suggestions</h2>
            <p className="text-gray-600">Search for medicine recommendations by disease or condition name</p>
          </div>

          <div className="flex gap-4 mb-8">
            <input
              type="text"
              value={medicineQuery}
              onChange={(e) => setMedicineQuery(e.target.value)}
              placeholder="Enter disease name (e.g., cold, headache, diabetes)"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              onClick={searchMedicine}
              disabled={isLoading || !medicineQuery.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200 disabled:opacity-50"
            >
              {isLoading ? 'Searching...' : '🔍 Search'}
            </button>
          </div>

          {medicineResults && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <h3 className="text-xl font-semibold text-green-800 mb-4">
                💊 Medicine Suggestions for: {medicineResults.disease}
              </h3>
              
              {medicineResults.medicines && (
                <div className="mb-4">
                  <h4 className="font-medium text-gray-800 mb-3">Recommended Medicines:</h4>
                  <ul className="space-y-2">
                    {medicineResults.medicines.map((medicine, index) => (
                      <li key={index} className="bg-white p-3 rounded border-l-4 border-green-400">
                        <span className="text-green-700 font-medium">{medicine}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {medicineResults.ai_suggestions && (
                <div className="mb-4">
                  <h4 className="font-medium text-gray-800 mb-3">AI Suggestions:</h4>
                  <div className="bg-white p-4 rounded border">
                    <p className="text-gray-700">{medicineResults.ai_suggestions}</p>
                  </div>
                </div>
              )}

              {medicineResults.description && (
                <div className="mb-4">
                  <h4 className="font-medium text-gray-800 mb-2">About the Condition:</h4>
                  <p className="text-gray-700">{medicineResults.description}</p>
                </div>
              )}

              {medicineResults.doctor_specialization && (
                <div className="mb-4">
                  <h4 className="font-medium text-gray-800 mb-2">👨‍⚕️ Consult:</h4>
                  <p className="text-blue-700">{medicineResults.doctor_specialization}</p>
                </div>
              )}

              <div className="bg-red-50 border border-red-200 rounded p-3">
                <p className="text-red-800 text-sm">
                  ⚠️ {medicineResults.disclaimer}
                </p>
              </div>
            </div>
          )}

          <div className="text-center">
            <button 
              onClick={resetToHome}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-full transition-colors duration-200"
            >
              🏠 Back to Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const ExerciseScreen = () => (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-100 pt-16">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">🏃‍♂️</div>
            <h2 className="text-3xl font-bold text-gray-800 mb-4">Exercise & Diet Plans</h2>
            <p className="text-gray-600">Get personalized exercise and diet recommendations for your condition</p>
          </div>

          <div className="flex gap-4 mb-8">
            <input
              type="text"
              value={exerciseQuery}
              onChange={(e) => setExerciseQuery(e.target.value)}
              placeholder="Enter condition (e.g., diabetes, hypertension, arthritis)"
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
            <button
              onClick={searchExercise}
              disabled={isLoading || !exerciseQuery.trim()}
              className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200 disabled:opacity-50"
            >
              {isLoading ? 'Searching...' : '🔍 Search'}
            </button>
          </div>

          {exerciseResults && (
            <div className="space-y-6">
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                <h3 className="text-xl font-semibold text-purple-800 mb-4">
                  🏃‍♂️ Exercise & Diet Plan for: {exerciseResults.condition}
                </h3>
                
                {exerciseResults.exercises && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-800 mb-3">🏋️‍♂️ Recommended Exercises:</h4>
                    <div className="grid md:grid-cols-2 gap-3">
                      {exerciseResults.exercises.map((exercise, index) => (
                        <div key={index} className="bg-white p-3 rounded border-l-4 border-purple-400">
                          <span className="text-purple-700">{exercise}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {exerciseResults.diet && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-800 mb-3">🥗 Diet Recommendations:</h4>
                    <div className="grid md:grid-cols-2 gap-3">
                      {exerciseResults.diet.map((dietItem, index) => (
                        <div key={index} className="bg-white p-3 rounded border-l-4 border-green-400">
                          <span className="text-green-700">{dietItem}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {exerciseResults.ai_suggestions && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-800 mb-3">🤖 AI Recommendations:</h4>
                    <div className="bg-white p-4 rounded border">
                      <p className="text-gray-700">{exerciseResults.ai_suggestions}</p>
                    </div>
                  </div>
                )}

                {exerciseResults.description && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-800 mb-2">About the Condition:</h4>
                    <p className="text-gray-700">{exerciseResults.description}</p>
                  </div>
                )}

                <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                  <p className="text-yellow-800 text-sm">
                    ⚠️ {exerciseResults.disclaimer}
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="text-center">
            <button 
              onClick={resetToHome}
              className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-3 px-6 rounded-full transition-colors duration-200"
            >
              🏠 Back to Home
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="App">
      <NavigationBar />
      {activeSection === 'home' && <HomeScreen />}
      {activeSection === 'diagnosis' && <DiagnosisScreen />}
      {activeSection === 'upload' && <UploadScreen />}
      {activeSection === 'medicine' && <MedicineScreen />}
      {activeSection === 'exercise' && <ExerciseScreen />}
    </div>
  );
};

export default App;