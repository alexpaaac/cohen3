import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const RiskHuntBuilder = () => {
  const [activeTab, setActiveTab] = useState('builder');
  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState(null);
  const [gameSession, setGameSession] = useState(null);
  const [riskZones, setRiskZones] = useState([]);
  const [currentTool, setCurrentTool] = useState('circle');
  const [isDrawing, setIsDrawing] = useState(false);
  const [loading, setLoading] = useState(false);
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  // Load images on component mount
  useEffect(() => {
    loadImages();
    loadGames();
  }, []);

  const loadImages = async () => {
    try {
      const response = await axios.get(`${API}/images`);
      setImages(response.data);
    } catch (error) {
      console.error('Error loading images:', error);
    }
  };

  const loadGames = async () => {
    try {
      const response = await axios.get(`${API}/games`);
      setGames(response.data);
    } catch (error) {
      console.error('Error loading games:', error);
    }
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', file.name);

    try {
      await axios.post(`${API}/images/upload`, formData);
      loadImages();
    } catch (error) {
      console.error('Error uploading image:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectImage = async (imageId) => {
    try {
      const response = await axios.get(`${API}/images/${imageId}`);
      setSelectedImage(response.data);
      setRiskZones(response.data.risk_zones || []);
    } catch (error) {
      console.error('Error selecting image:', error);
    }
  };

  const handleCanvasClick = (event) => {
    if (!selectedImage || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (currentTool === 'circle') {
      const newRiskZone = {
        id: Date.now().toString(),
        type: 'circle',
        coordinates: [x, y, 30], // x, y, radius
        description: 'Safety Risk',
        difficulty: 'medium',
        points: 1,
        explanation: 'Describe the safety risk here'
      };
      setRiskZones([...riskZones, newRiskZone]);
    } else if (currentTool === 'rectangle') {
      const newRiskZone = {
        id: Date.now().toString(),
        type: 'rectangle',
        coordinates: [x - 25, y - 25, 50, 50], // x, y, width, height
        description: 'Safety Risk',
        difficulty: 'medium',
        points: 1,
        explanation: 'Describe the safety risk here'
      };
      setRiskZones([...riskZones, newRiskZone]);
    }
  };

  const saveRiskZones = async () => {
    if (!selectedImage) return;

    try {
      await axios.put(`${API}/images/${selectedImage.id}/risk-zones`, riskZones);
      alert('Risk zones saved successfully!');
    } catch (error) {
      console.error('Error saving risk zones:', error);
    }
  };

  const createGame = async () => {
    const gameName = prompt('Enter game name:');
    if (!gameName) return;

    const gameConfig = {
      name: gameName,
      description: 'Risk Hunt Game',
      time_limit: 300,
      max_clicks: 17,
      target_risks: 15,
      images: [selectedImage?.id].filter(Boolean)
    };

    try {
      await axios.post(`${API}/games`, gameConfig);
      loadGames();
      alert('Game created successfully!');
    } catch (error) {
      console.error('Error creating game:', error);
    }
  };

  const startGame = async (gameId) => {
    const playerName = prompt('Enter your name:');
    if (!playerName) return;

    const session = {
      game_id: gameId,
      player_name: playerName,
      team_name: 'Default Team',
      time_remaining: 300
    };

    try {
      const response = await axios.post(`${API}/sessions`, session);
      setGameSession(response.data);
      setActiveTab('play');
    } catch (error) {
      console.error('Error starting game:', error);
    }
  };

  const handleGameClick = async (event) => {
    if (!gameSession || !selectedImage) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    try {
      const response = await axios.post(`${API}/sessions/${gameSession.id}/click`, { x, y });
      
      if (response.data.hit) {
        alert(`Great! You found a risk: ${response.data.risk_zone.description}`);
      }
      
      setGameSession(prev => ({
        ...prev,
        clicks_used: response.data.clicks_used,
        score: response.data.score
      }));
    } catch (error) {
      console.error('Error handling click:', error);
    }
  };

  const drawRiskZones = () => {
    if (!canvasRef.current || !selectedImage) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw risk zones
    riskZones.forEach(zone => {
      ctx.strokeStyle = '#ff0000';
      ctx.lineWidth = 2;
      ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
      
      if (zone.type === 'circle') {
        const [x, y, radius] = zone.coordinates;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.stroke();
        ctx.fill();
      } else if (zone.type === 'rectangle') {
        const [x, y, width, height] = zone.coordinates;
        ctx.strokeRect(x, y, width, height);
        ctx.fillRect(x, y, width, height);
      }
    });
  };

  useEffect(() => {
    drawRiskZones();
  }, [riskZones, selectedImage]);

  const renderBuilder = () => (
    <div className="builder-container">
      <div className="builder-header">
        <h2 className="text-2xl font-bold mb-6">Risk Hunt Game Builder</h2>
        
        {/* Image Upload */}
        <div className="mb-6">
          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
            id="image-upload"
          />
          <label
            htmlFor="image-upload"
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer mr-4"
          >
            Upload Image
          </label>
          {loading && <span className="text-blue-500">Uploading...</span>}
        </div>

        {/* Image Gallery */}
        <div className="image-gallery mb-6">
          <h3 className="text-lg font-semibold mb-4">Select Image</h3>
          <div className="grid grid-cols-3 gap-4">
            {images.map(image => (
              <div
                key={image.id}
                className={`cursor-pointer border-2 rounded-lg p-2 ${
                  selectedImage?.id === image.id ? 'border-blue-500' : 'border-gray-300'
                }`}
                onClick={() => selectImage(image.id)}
              >
                {image.image_data.startsWith('http') ? (
                  <img src={image.image_data} alt={image.name} className="w-full h-32 object-cover rounded" />
                ) : (
                  <img src={`data:image/jpeg;base64,${image.image_data}`} alt={image.name} className="w-full h-32 object-cover rounded" />
                )}
                <p className="text-sm mt-2">{image.name}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedImage && (
        <div className="image-editor">
          <div className="tools mb-4">
            <button
              onClick={() => setCurrentTool('circle')}
              className={`px-4 py-2 mr-2 rounded ${
                currentTool === 'circle' ? 'bg-blue-500 text-white' : 'bg-gray-200'
              }`}
            >
              Circle Tool
            </button>
            <button
              onClick={() => setCurrentTool('rectangle')}
              className={`px-4 py-2 mr-2 rounded ${
                currentTool === 'rectangle' ? 'bg-blue-500 text-white' : 'bg-gray-200'
              }`}
            >
              Rectangle Tool
            </button>
            <button
              onClick={saveRiskZones}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mr-2"
            >
              Save Risk Zones
            </button>
            <button
              onClick={createGame}
              className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded"
            >
              Create Game
            </button>
          </div>

          <div className="relative">
            {selectedImage.image_data.startsWith('http') ? (
              <img
                ref={imageRef}
                src={selectedImage.image_data}
                alt={selectedImage.name}
                className="max-w-full h-auto"
                onLoad={() => {
                  if (canvasRef.current && imageRef.current) {
                    canvasRef.current.width = imageRef.current.width;
                    canvasRef.current.height = imageRef.current.height;
                    drawRiskZones();
                  }
                }}
              />
            ) : (
              <img
                ref={imageRef}
                src={`data:image/jpeg;base64,${selectedImage.image_data}`}
                alt={selectedImage.name}
                className="max-w-full h-auto"
                onLoad={() => {
                  if (canvasRef.current && imageRef.current) {
                    canvasRef.current.width = imageRef.current.width;
                    canvasRef.current.height = imageRef.current.height;
                    drawRiskZones();
                  }
                }}
              />
            )}
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0 cursor-crosshair"
              onClick={handleCanvasClick}
            />
          </div>

          <div className="risk-zones-list mt-6">
            <h3 className="text-lg font-semibold mb-4">Risk Zones ({riskZones.length})</h3>
            <div className="grid grid-cols-1 gap-2">
              {riskZones.map(zone => (
                <div key={zone.id} className="bg-gray-100 p-3 rounded">
                  <p><strong>Type:</strong> {zone.type}</p>
                  <p><strong>Description:</strong> {zone.description}</p>
                  <p><strong>Difficulty:</strong> {zone.difficulty}</p>
                  <p><strong>Points:</strong> {zone.points}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderGames = () => (
    <div className="games-container">
      <h2 className="text-2xl font-bold mb-6">Available Games</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {games.map(game => (
          <div key={game.id} className="bg-white rounded-lg shadow-md p-6 border">
            <h3 className="text-xl font-semibold mb-2">{game.name}</h3>
            <p className="text-gray-600 mb-4">{game.description}</p>
            <div className="text-sm text-gray-500 mb-4">
              <p>Time Limit: {game.time_limit}s</p>
              <p>Max Clicks: {game.max_clicks}</p>
              <p>Target Risks: {game.target_risks}</p>
              <p>Images: {game.images.length}</p>
            </div>
            <button
              onClick={() => startGame(game.id)}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded w-full"
            >
              Start Game
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  const renderPlayGame = () => (
    <div className="play-game-container">
      {gameSession && (
        <div className="game-header mb-4">
          <h2 className="text-2xl font-bold">Playing Game - {gameSession.player_name}</h2>
          <div className="game-stats flex gap-4 mt-2">
            <span className="bg-blue-100 px-3 py-1 rounded">Score: {gameSession.score}</span>
            <span className="bg-yellow-100 px-3 py-1 rounded">Clicks: {gameSession.clicks_used}</span>
            <span className="bg-red-100 px-3 py-1 rounded">Time: {gameSession.time_remaining}s</span>
          </div>
        </div>
      )}
      
      {selectedImage && (
        <div className="relative">
          {selectedImage.image_data.startsWith('http') ? (
            <img
              ref={imageRef}
              src={selectedImage.image_data}
              alt={selectedImage.name}
              className="max-w-full h-auto"
              onLoad={() => {
                if (canvasRef.current && imageRef.current) {
                  canvasRef.current.width = imageRef.current.width;
                  canvasRef.current.height = imageRef.current.height;
                }
              }}
            />
          ) : (
            <img
              ref={imageRef}
              src={`data:image/jpeg;base64,${selectedImage.image_data}`}
              alt={selectedImage.name}
              className="max-w-full h-auto"
              onLoad={() => {
                if (canvasRef.current && imageRef.current) {
                  canvasRef.current.width = imageRef.current.width;
                  canvasRef.current.height = imageRef.current.height;
                }
              }}
            />
          )}
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 cursor-crosshair"
            onClick={handleGameClick}
          />
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center mr-3">
                <span className="text-white font-bold text-sm">R</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-800">Risk Hunt Builder</h1>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveTab('builder')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  activeTab === 'builder'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Builder
              </button>
              <button
                onClick={() => setActiveTab('games')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  activeTab === 'games'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Games
              </button>
              <button
                onClick={() => setActiveTab('play')}
                className={`px-4 py-2 rounded-lg font-medium ${
                  activeTab === 'play'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Play
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'builder' && renderBuilder()}
        {activeTab === 'games' && renderGames()}
        {activeTab === 'play' && renderPlayGame()}
      </div>
    </div>
  );
};

export default RiskHuntBuilder;