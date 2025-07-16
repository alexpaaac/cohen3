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
  const [results, setResults] = useState([]);
  const [riskZones, setRiskZones] = useState([]);
  const [selectedRiskZone, setSelectedRiskZone] = useState(null);
  const [hoveredRiskZone, setHoveredRiskZone] = useState(null);
  const [currentTool, setCurrentTool] = useState('circle');
  const [isDrawing, setIsDrawing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [gameTimer, setGameTimer] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [gameEnded, setGameEnded] = useState(false);
  const [gameConfig, setGameConfig] = useState({
    name: '',
    description: '',
    time_limit: 300,
    max_clicks: 17,
    target_risks: 15,
    is_public: false
  });
  const [editingItem, setEditingItem] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [analytics, setAnalytics] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [languages, setLanguages] = useState('en');
  const [branding, setBranding] = useState({
    logo: '',
    primaryColor: '#3b82f6',
    secondaryColor: '#ef4444',
    companyName: 'Acapella'
  });
  const [undoStack, setUndoStack] = useState([]);
  const [redoStack, setRedoStack] = useState([]);
  const [unsavedChanges, setUnsavedChanges] = useState(false);
  const [showCorrectionScreen, setShowCorrectionScreen] = useState(false);
  const [gameStatistics, setGameStatistics] = useState(null);
  const [autoSaveInterval, setAutoSaveInterval] = useState(null);
  
  const canvasRef = useRef(null);
  const imageRef = useRef(null);

  // Auto-save functionality
  useEffect(() => {
    if (unsavedChanges && selectedImage && riskZones.length > 0) {
      const interval = setInterval(() => {
        saveRiskZones(true); // Silent save
      }, 30000); // Auto-save every 30 seconds
      setAutoSaveInterval(interval);
      return () => clearInterval(interval);
    }
  }, [unsavedChanges, selectedImage, riskZones]);

  // Load data on component mount
  useEffect(() => {
    loadImages();
    loadGames();
    loadResults();
  }, []);

  // Game timer effect
  useEffect(() => {
    let interval;
    if (gameSession && gameSession.status === 'active' && timeRemaining > 0) {
      interval = setInterval(() => {
        setTimeRemaining(prev => {
          if (prev <= 1) {
            handleGameTimeout();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [gameSession, timeRemaining]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (unsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [unsavedChanges]);

  const loadImages = async () => {
    try {
      const response = await axios.get(`${API}/images`);
      setImages(response.data);
    } catch (error) {
      console.error('Error loading images:', error);
      showNotification('Error loading images', 'error');
    }
  };

  const loadGames = async () => {
    try {
      const response = await axios.get(`${API}/games`);
      setGames(response.data);
    } catch (error) {
      console.error('Error loading games:', error);
      showNotification('Error loading games', 'error');
    }
  };

  const loadResults = async () => {
    try {
      const response = await axios.get(`${API}/results`);
      setResults(response.data);
    } catch (error) {
      console.error('Error loading results:', error);
    }
  };

  const loadAnalytics = async (gameId) => {
    try {
      const response = await axios.get(`${API}/results/analytics/${gameId}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const showNotification = (message, type = 'info') => {
    const notification = {
      id: Date.now(),
      message,
      type
    };
    setNotifications(prev => [...prev, notification]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const saveToUndoStack = () => {
    setUndoStack(prev => [...prev, JSON.parse(JSON.stringify(riskZones))]);
    setRedoStack([]); // Clear redo stack when new action is performed
    if (undoStack.length > 20) {
      setUndoStack(prev => prev.slice(1)); // Keep only last 20 states
    }
  };

  const undo = () => {
    if (undoStack.length > 0) {
      const previousState = undoStack[undoStack.length - 1];
      setRedoStack(prev => [...prev, JSON.parse(JSON.stringify(riskZones))]);
      setRiskZones(previousState);
      setUndoStack(prev => prev.slice(0, -1));
      setUnsavedChanges(true);
    }
  };

  const redo = () => {
    if (redoStack.length > 0) {
      const nextState = redoStack[redoStack.length - 1];
      setUndoStack(prev => [...prev, JSON.parse(JSON.stringify(riskZones))]);
      setRiskZones(nextState);
      setRedoStack(prev => prev.slice(0, -1));
      setUnsavedChanges(true);
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
      showNotification('Image uploaded successfully', 'success');
    } catch (error) {
      console.error('Error uploading image:', error);
      showNotification('Error uploading image', 'error');
    } finally {
      setLoading(false);
    }
  };

  const selectImage = async (imageId) => {
    if (unsavedChanges) {
      const shouldContinue = window.confirm('You have unsaved changes. Do you want to continue without saving?');
      if (!shouldContinue) return;
    }

    try {
      const response = await axios.get(`${API}/images/${imageId}`);
      setSelectedImage(response.data);
      setRiskZones(response.data.risk_zones || []);
      setUnsavedChanges(false);
      setUndoStack([]);
      setRedoStack([]);
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

    // Check if clicking on existing risk zone for editing
    const clickedZone = riskZones.find(zone => {
      if (zone.type === 'circle') {
        const [cx, cy, radius] = zone.coordinates;
        const distance = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
        return distance <= radius;
      } else if (zone.type === 'rectangle') {
        const [rx, ry, width, height] = zone.coordinates;
        return x >= rx && x <= rx + width && y >= ry && y <= ry + height;
      }
      return false;
    });

    if (clickedZone) {
      setSelectedRiskZone(clickedZone);
      return;
    }

    // Save to undo stack before creating new zone
    saveToUndoStack();

    // Create new risk zone
    if (currentTool === 'circle') {
      const newRiskZone = {
        id: Date.now().toString(),
        type: 'circle',
        coordinates: [x, y, 30],
        description: 'Safety Risk',
        difficulty: 'medium',
        points: 1,
        explanation: 'Describe the safety risk here',
        color: '#ff0000'
      };
      setRiskZones([...riskZones, newRiskZone]);
      setUnsavedChanges(true);
    } else if (currentTool === 'rectangle') {
      const newRiskZone = {
        id: Date.now().toString(),
        type: 'rectangle',
        coordinates: [x - 25, y - 25, 50, 50],
        description: 'Safety Risk',
        difficulty: 'medium',
        points: 1,
        explanation: 'Describe the safety risk here',
        color: '#ff0000'
      };
      setRiskZones([...riskZones, newRiskZone]);
      setUnsavedChanges(true);
    }
  };

  const handleCanvasMouseMove = (event) => {
    if (!selectedImage || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find hovered risk zone
    const hoveredZone = riskZones.find(zone => {
      if (zone.type === 'circle') {
        const [cx, cy, radius] = zone.coordinates;
        const distance = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
        return distance <= radius;
      } else if (zone.type === 'rectangle') {
        const [rx, ry, width, height] = zone.coordinates;
        return x >= rx && x <= rx + width && y >= ry && y <= ry + height;
      }
      return false;
    });

    setHoveredRiskZone(hoveredZone);
  };

  const updateRiskZone = (zoneId, updates) => {
    saveToUndoStack();
    setRiskZones(zones => zones.map(zone => 
      zone.id === zoneId ? { ...zone, ...updates } : zone
    ));
    setUnsavedChanges(true);
  };

  const deleteRiskZone = (zoneId) => {
    saveToUndoStack();
    setRiskZones(zones => zones.filter(zone => zone.id !== zoneId));
    setSelectedRiskZone(null);
    setUnsavedChanges(true);
  };

  const saveRiskZones = async (silent = false) => {
    if (!selectedImage) return;

    try {
      await axios.put(`${API}/images/${selectedImage.id}/risk-zones`, riskZones);
      setUnsavedChanges(false);
      if (!silent) {
        showNotification('Risk zones saved successfully', 'success');
      }
    } catch (error) {
      console.error('Error saving risk zones:', error);
      if (!silent) {
        showNotification('Error saving risk zones', 'error');
      }
    }
  };

  const createGame = async () => {
    if (!gameConfig.name.trim()) {
      showNotification('Please enter a game name', 'warning');
      return;
    }

    const gameData = {
      ...gameConfig,
      images: selectedImage ? [selectedImage.id] : [],
      branding
    };

    try {
      await axios.post(`${API}/games`, gameData);
      loadGames();
      showNotification('Game created successfully', 'success');
      setGameConfig({
        name: '',
        description: '',
        time_limit: 300,
        max_clicks: 17,
        target_risks: 15,
        is_public: false
      });
    } catch (error) {
      console.error('Error creating game:', error);
      showNotification('Error creating game', 'error');
    }
  };

  const updateGame = async (gameId, updates) => {
    try {
      await axios.put(`${API}/games/${gameId}`, updates);
      loadGames();
      showNotification('Game updated successfully', 'success');
    } catch (error) {
      console.error('Error updating game:', error);
      showNotification('Error updating game', 'error');
    }
  };

  const deleteGame = async (gameId) => {
    // Optimistic update - remove from UI immediately
    setGames(prev => prev.filter(game => game.id !== gameId));
    showNotification('Deleting game...', 'info');
    
    try {
      await axios.delete(`${API}/games/${gameId}`);
      showNotification('Game deleted successfully', 'success');
    } catch (error) {
      console.error('Error deleting game:', error);
      showNotification('Error deleting game', 'error');
      // Revert optimistic update on error
      loadGames();
    }
  };

  const deleteImage = async (imageId) => {
    // Optimistic update - remove from UI immediately
    setImages(prev => prev.filter(image => image.id !== imageId));
    
    // Clear selection if this image was selected
    if (selectedImage?.id === imageId) {
      setSelectedImage(null);
      setRiskZones([]);
    }
    
    showNotification('Deleting image...', 'info');
    
    try {
      await axios.delete(`${API}/images/${imageId}`);
      showNotification('Image deleted successfully', 'success');
    } catch (error) {
      console.error('Error deleting image:', error);
      showNotification('Error deleting image', 'error');
      // Revert optimistic update on error
      loadImages();
      if (selectedImage?.id === imageId) {
        selectImage(imageId); // Try to restore selection
      }
    }
  };

  const duplicateGame = async (gameId) => {
    showNotification('Duplicating game...', 'info');
    
    try {
      const response = await axios.post(`${API}/games/${gameId}/duplicate`);
      
      // Get the original game to copy its images
      const originalGame = games.find(g => g.id === gameId);
      if (originalGame && originalGame.images && originalGame.images.length > 0) {
        // Duplicate all images associated with the game
        const duplicatedImages = [];
        for (const imageId of originalGame.images) {
          try {
            const imageResponse = await axios.post(`${API}/images/${imageId}/duplicate`);
            duplicatedImages.push(imageResponse.data.id);
          } catch (imageError) {
            console.error('Error duplicating image:', imageError);
          }
        }
        
        // Update the duplicated game with the new image IDs
        if (duplicatedImages.length > 0) {
          await axios.put(`${API}/games/${response.data.id}`, {
            images: duplicatedImages
          });
        }
      }
      
      loadGames();
      showNotification('Game duplicated successfully with all images and risk zones', 'success');
    } catch (error) {
      console.error('Error duplicating game:', error);
      showNotification('Error duplicating game', 'error');
    }
  };

  const duplicateImage = async (imageId) => {
    try {
      await axios.post(`${API}/images/${imageId}/duplicate`);
      loadImages();
      showNotification('Image duplicated successfully', 'success');
    } catch (error) {
      console.error('Error duplicating image:', error);
      showNotification('Error duplicating image', 'error');
    }
  };

  const startGame = async (gameId) => {
    const playerName = prompt('Enter your name:');
    if (!playerName) return;

    const teamName = prompt('Enter your team name (optional):') || 'Default Team';

    const session = {
      game_id: gameId,
      player_name: playerName,
      team_name: teamName
    };

    try {
      const response = await axios.post(`${API}/sessions`, session);
      const game = games.find(g => g.id === gameId);
      
      setGameSession(response.data);
      setTimeRemaining(game.time_limit);
      setGameEnded(false);
      setActiveTab('play');
      setShowCorrectionScreen(false);
      
      // Load first image
      if (game.images.length > 0) {
        selectImage(game.images[0]);
      }
    } catch (error) {
      console.error('Error starting game:', error);
      showNotification('Error starting game', 'error');
    }
  };

  const handleGameClick = async (event) => {
    if (!gameSession || gameSession.status !== 'active' || !selectedImage) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Provide immediate visual feedback
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.beginPath();
    ctx.arc(x, y, 15, 0, 2 * Math.PI);
    ctx.fill();
    
    // Clear the visual feedback after a short delay
    setTimeout(() => {
      drawRiskZones(showCorrectionScreen);
    }, 200);

    try {
      const response = await axios.post(`${API}/sessions/${gameSession.id}/click`, { x, y });
      
      if (response.data.hit) {
        // Show hit animation
        showNotification(`🎯 Risk Found: ${response.data.risk_zone.description}`, 'success');
        
        // Visual feedback for hit
        ctx.strokeStyle = '#10b981';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, y, 20, 0, 2 * Math.PI);
        ctx.stroke();
        
        // Show the found risk zone temporarily
        const foundZone = response.data.risk_zone;
        if (foundZone) {
          ctx.fillStyle = 'rgba(16, 185, 129, 0.3)';
          ctx.strokeStyle = '#10b981';
          ctx.lineWidth = 2;
          
          if (foundZone.type === 'circle') {
            const [cx, cy, radius] = foundZone.coordinates;
            ctx.beginPath();
            ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
            ctx.fill();
            ctx.stroke();
          } else if (foundZone.type === 'rectangle') {
            const [rx, ry, width, height] = foundZone.coordinates;
            ctx.fillRect(rx, ry, width, height);
            ctx.strokeRect(rx, ry, width, height);
          }
        }
        
      } else {
        showNotification('No risk found here', 'info');
        
        // Visual feedback for miss
        ctx.strokeStyle = '#ef4444';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, 15, 0, 2 * Math.PI);
        ctx.stroke();
      }
      
      // Update game session with new data
      setGameSession(prev => ({
        ...prev,
        clicks_used: response.data.clicks_used,
        score: response.data.score,
        found_risks: response.data.found_risks || prev.found_risks
      }));

      // Check if game should end
      if (response.data.game_status === 'completed' || response.data.clicks_remaining <= 0) {
        handleGameEnd();
      }
    } catch (error) {
      console.error('Error handling click:', error);
      showNotification('Error processing click', 'error');
    }
  };

  const handleGameTimeout = async () => {
    if (!gameSession) return;

    try {
      await axios.post(`${API}/sessions/${gameSession.id}/timeout`);
      handleGameEnd();
    } catch (error) {
      console.error('Error handling timeout:', error);
    }
  };

  const handleGameEnd = () => {
    setGameEnded(true);
    setGameSession(prev => ({ ...prev, status: 'completed' }));
    loadResults();
    setShowCorrectionScreen(true);
  };

  const exportResults = async (gameId, format) => {
    if (!gameId) {
      showNotification('Please select a game first', 'warning');
      return;
    }

    try {
      const response = await axios.get(`${API}/results/export/${gameId}?format=${format}`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `game_results_${gameId}.${format === 'excel' ? 'xlsx' : format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      showNotification(`Results exported as ${format.toUpperCase()}`, 'success');
    } catch (error) {
      console.error('Error exporting results:', error);
      showNotification('Error exporting results', 'error');
    }
  };

  const drawRiskZones = (showAll = false) => {
    if (!canvasRef.current || !selectedImage) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw risk zones
    riskZones.forEach(zone => {
      const isHovered = hoveredRiskZone && hoveredRiskZone.id === zone.id;
      const isSelected = selectedRiskZone && selectedRiskZone.id === zone.id;
      
      if (showAll || isHovered || isSelected || activeTab === 'builder') {
        ctx.strokeStyle = isSelected ? '#00ff00' : (isHovered ? '#ffff00' : zone.color);
        ctx.lineWidth = isSelected ? 3 : (isHovered ? 2 : 1);
        ctx.fillStyle = isSelected ? 'rgba(0, 255, 0, 0.2)' : (isHovered ? 'rgba(255, 255, 0, 0.2)' : `${zone.color}33`);
        
        if (zone.type === 'circle') {
          const [x, y, radius] = zone.coordinates;
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, 2 * Math.PI);
          ctx.stroke();
          if (isHovered || isSelected || showAll) ctx.fill();
        } else if (zone.type === 'rectangle') {
          const [x, y, width, height] = zone.coordinates;
          ctx.strokeRect(x, y, width, height);
          if (isHovered || isSelected || showAll) ctx.fillRect(x, y, width, height);
        }
      }
    });
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    drawRiskZones(showCorrectionScreen);
  }, [riskZones, selectedImage, hoveredRiskZone, selectedRiskZone, showCorrectionScreen]);

  const renderNotifications = () => (
    <div className="notifications">
      {notifications.map(notification => (
        <div key={notification.id} className={`notification ${notification.type}`}>
          {notification.message}
        </div>
      ))}
    </div>
  );

  const renderBuilder = () => (
    <div className="builder-container">
      <div className="builder-header">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Risk Hunt Game Builder</h2>
          {unsavedChanges && (
            <span className="text-orange-600 font-semibold">⚠️ Unsaved Changes</span>
          )}
        </div>
        
        {/* Game Configuration */}
        <div className="game-config-section mb-6">
          <h3 className="text-lg font-semibold mb-4">Game Configuration</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Game Name</label>
              <input
                type="text"
                value={gameConfig.name}
                onChange={(e) => setGameConfig({...gameConfig, name: e.target.value})}
                className="w-full p-2 border rounded"
                placeholder="Enter game name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Description</label>
              <input
                type="text"
                value={gameConfig.description}
                onChange={(e) => setGameConfig({...gameConfig, description: e.target.value})}
                className="w-full p-2 border rounded"
                placeholder="Enter description"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Time Limit (seconds)</label>
              <input
                type="number"
                value={gameConfig.time_limit}
                onChange={(e) => setGameConfig({...gameConfig, time_limit: parseInt(e.target.value)})}
                className="w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Max Clicks</label>
              <input
                type="number"
                value={gameConfig.max_clicks}
                onChange={(e) => setGameConfig({...gameConfig, max_clicks: parseInt(e.target.value)})}
                className="w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Target Risks</label>
              <input
                type="number"
                value={gameConfig.target_risks}
                onChange={(e) => setGameConfig({...gameConfig, target_risks: parseInt(e.target.value)})}
                className="w-full p-2 border rounded"
              />
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={gameConfig.is_public}
                  onChange={(e) => setGameConfig({...gameConfig, is_public: e.target.checked})}
                  className="mr-2"
                />
                Make game public
              </label>
            </div>
          </div>
        </div>

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
          <h3 className="text-lg font-semibold mb-4">Select Image ({images.length} images)</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {images.map(image => (
              <div
                key={image.id}
                className={`cursor-pointer border-2 rounded-lg overflow-hidden hover:shadow-lg transition-all duration-200 ${
                  selectedImage?.id === image.id ? 'border-blue-500 shadow-md' : 'border-gray-300'
                }`}
                onClick={() => selectImage(image.id)}
              >
                <div className="aspect-square bg-gray-100 flex items-center justify-center">
                  {image.image_data.startsWith('http') ? (
                    <img 
                      src={image.image_data} 
                      alt={image.name} 
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOWNhM2FmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkltYWdlIEVycm9yPC90ZXh0Pjwvc3ZnPg==';
                      }}
                    />
                  ) : (
                    <img 
                      src={`data:image/jpeg;base64,${image.image_data}`} 
                      alt={image.name} 
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2YzZjRmNiIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOWNhM2FmIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iMC4zZW0iPkltYWdlIEVycm9yPC90ZXh0Pjwvc3ZnPg==';
                      }}
                    />
                  )}
                </div>
                <div className="p-3">
                  <p className="text-sm font-medium text-gray-800 truncate" title={image.name}>
                    {image.name}
                  </p>
                  <div className="flex gap-1 mt-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingItem({type: 'image', id: image.id, name: image.name});
                      }}
                      className="flex-1 text-blue-500 hover:text-blue-700 text-xs py-1 px-2 rounded hover:bg-blue-50 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        duplicateImage(image.id);
                      }}
                      className="flex-1 text-green-500 hover:text-green-700 text-xs py-1 px-2 rounded hover:bg-green-50 transition-colors"
                    >
                      Clone
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowDeleteModal({type: 'image', id: image.id, name: image.name});
                      }}
                      className="flex-1 text-red-500 hover:text-red-700 text-xs py-1 px-2 rounded hover:bg-red-50 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
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
              onClick={() => undo()}
              disabled={undoStack.length === 0}
              className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-300 text-white px-4 py-2 rounded mr-2"
            >
              Undo
            </button>
            <button
              onClick={() => redo()}
              disabled={redoStack.length === 0}
              className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-300 text-white px-4 py-2 rounded mr-2"
            >
              Redo
            </button>
            <button
              onClick={() => saveRiskZones()}
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
              onMouseMove={handleCanvasMouseMove}
            />
          </div>

          {hoveredRiskZone && (
            <div className="hovered-zone-info">
              <p><strong>Risk:</strong> {hoveredRiskZone.description}</p>
            </div>
          )}

          <div className="risk-zones-management mt-6">
            <h3 className="text-lg font-semibold mb-4">Risk Zones ({riskZones.length})</h3>
            
            {selectedRiskZone && (
              <div className="selected-zone-editor mb-4 p-4 bg-gray-100 rounded">
                <h4 className="font-semibold mb-2">Edit Risk Zone</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Description</label>
                    <input
                      type="text"
                      value={selectedRiskZone.description}
                      onChange={(e) => updateRiskZone(selectedRiskZone.id, {description: e.target.value})}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Difficulty</label>
                    <select
                      value={selectedRiskZone.difficulty}
                      onChange={(e) => updateRiskZone(selectedRiskZone.id, {difficulty: e.target.value})}
                      className="w-full p-2 border rounded"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Points</label>
                    <input
                      type="number"
                      value={selectedRiskZone.points}
                      onChange={(e) => updateRiskZone(selectedRiskZone.id, {points: parseInt(e.target.value)})}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Color</label>
                    <input
                      type="color"
                      value={selectedRiskZone.color}
                      onChange={(e) => updateRiskZone(selectedRiskZone.id, {color: e.target.value})}
                      className="w-full p-2 border rounded"
                    />
                  </div>
                </div>
                <div className="mt-4">
                  <label className="block text-sm font-medium mb-1">Explanation</label>
                  <textarea
                    value={selectedRiskZone.explanation}
                    onChange={(e) => updateRiskZone(selectedRiskZone.id, {explanation: e.target.value})}
                    className="w-full p-2 border rounded"
                    rows="3"
                  />
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => deleteRiskZone(selectedRiskZone.id)}
                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded mr-2"
                  >
                    Delete Zone
                  </button>
                  <button
                    onClick={() => setSelectedRiskZone(null)}
                    className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-2">
              {riskZones.map(zone => (
                <div
                  key={zone.id}
                  className={`p-3 rounded cursor-pointer ${
                    selectedRiskZone?.id === zone.id ? 'bg-blue-100' : 'bg-gray-100'
                  }`}
                  onClick={() => setSelectedRiskZone(zone)}
                >
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
          <div key={game.id} className="game-card bg-white rounded-lg shadow-md p-6 border">
            <h3 className="text-xl font-semibold mb-2">{game.name}</h3>
            <p className="text-gray-600 mb-4">{game.description}</p>
            <div className="text-sm text-gray-500 mb-4">
              <p>Time Limit: {formatTime(game.time_limit)}</p>
              <p>Max Clicks: {game.max_clicks}</p>
              <p>Target Risks: {game.target_risks}</p>
              <p>Images: {game.images.length}</p>
              {game.is_public && <p className="text-green-600">Public Game</p>}
            </div>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={() => startGame(game.id)}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
              >
                Start Game
              </button>
              <button
                onClick={() => duplicateGame(game.id)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
              >
                Duplicate
              </button>
              <button
                onClick={() => setEditingItem({type: 'game', id: game.id, name: game.name})}
                className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded"
              >
                Edit
              </button>
              <button
                onClick={() => setShowDeleteModal({type: 'game', id: game.id})}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded"
              >
                Delete
              </button>
              <button
                onClick={() => {
                  loadAnalytics(game.id);
                  setShowResults(true);
                  setActiveTab('results');
                }}
                className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded"
              >
                Analytics
              </button>
            </div>
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
            <span className={`px-3 py-1 rounded ${timeRemaining <= 30 ? 'bg-red-100 text-red-800' : 'bg-green-100'}`}>
              Time: {formatTime(timeRemaining)}
            </span>
          </div>
          {gameSession.status === 'completed' && (
            <div className="game-completed mt-4 p-4 bg-green-100 rounded">
              <h3 className="font-bold text-green-800">Game Completed!</h3>
              <p>Final Score: {gameSession.score}</p>
              <p>Clicks Used: {gameSession.clicks_used}</p>
              <button
                onClick={() => setShowCorrectionScreen(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded mt-2 mr-2"
              >
                Show Correction Screen
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded mt-2"
              >
                View Results
              </button>
            </div>
          )}
        </div>
      )}
      
      {showCorrectionScreen && selectedImage && (
        <div className="correction-screen mb-6">
          <h3 className="text-lg font-semibold mb-4">Correction Screen - All Risks Revealed</h3>
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
                    drawRiskZones(true);
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
                    drawRiskZones(true);
                  }
                }}
              />
            )}
            <canvas
              ref={canvasRef}
              className="absolute top-0 left-0"
            />
          </div>
          <div className="risk-explanations mt-4">
            <h4 className="font-semibold mb-2">Risk Explanations:</h4>
            {riskZones.map(zone => (
              <div key={zone.id} className="mb-2 p-2 bg-gray-100 rounded">
                <strong>{zone.description}:</strong> {zone.explanation}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {selectedImage && gameSession && gameSession.status === 'active' && !showCorrectionScreen && (
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

  const renderResults = () => (
    <div className="results-container">
      <h2 className="text-2xl font-bold mb-6">Results Dashboard</h2>
      
      {analytics && (
        <div className="analytics-section mb-6">
          <h3 className="text-lg font-semibold mb-4">Game Analytics</h3>
          <div className="grid grid-cols-4 gap-4">
            <div className="stat-card bg-blue-100 p-4 rounded">
              <h4 className="font-semibold text-blue-800">Total Players</h4>
              <p className="text-2xl text-blue-600">{analytics.total_players}</p>
            </div>
            <div className="stat-card bg-green-100 p-4 rounded">
              <h4 className="font-semibold text-green-800">Average Score</h4>
              <p className="text-2xl text-green-600">{analytics.average_score}</p>
            </div>
            <div className="stat-card bg-yellow-100 p-4 rounded">
              <h4 className="font-semibold text-yellow-800">Average Time</h4>
              <p className="text-2xl text-yellow-600">{formatTime(analytics.average_time)}</p>
            </div>
            <div className="stat-card bg-purple-100 p-4 rounded">
              <h4 className="font-semibold text-purple-800">Total Risks Found</h4>
              <p className="text-2xl text-purple-600">{analytics.total_risks_found}</p>
            </div>
          </div>
        </div>
      )}

      <div className="results-table-section">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Game Results</h3>
          <div className="flex gap-2">
            <button
              onClick={() => exportResults(analytics?.results?.[0]?.game_id || selectedGame?.id, 'csv')}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
            >
              Export CSV
            </button>
            <button
              onClick={() => exportResults(analytics?.results?.[0]?.game_id || selectedGame?.id, 'excel')}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
            >
              Export Excel
            </button>
          </div>
        </div>

        <div className="table-container">
          <table className="w-full border-collapse border border-gray-300">
            <thead>
              <tr className="bg-gray-100">
                <th className="border border-gray-300 p-2">Player Name</th>
                <th className="border border-gray-300 p-2">Team</th>
                <th className="border border-gray-300 p-2">Score</th>
                <th className="border border-gray-300 p-2">Risks Found</th>
                <th className="border border-gray-300 p-2">Time Spent</th>
                <th className="border border-gray-300 p-2">Clicks Used</th>
                <th className="border border-gray-300 p-2">Date</th>
              </tr>
            </thead>
            <tbody>
              {(analytics?.results || results).map(result => (
                <tr key={result.id}>
                  <td className="border border-gray-300 p-2">{result.player_name}</td>
                  <td className="border border-gray-300 p-2">{result.team_name}</td>
                  <td className="border border-gray-300 p-2">{result.total_score}</td>
                  <td className="border border-gray-300 p-2">{result.total_risks_found}</td>
                  <td className="border border-gray-300 p-2">{formatTime(result.total_time_spent)}</td>
                  <td className="border border-gray-300 p-2">{result.total_clicks_used}</td>
                  <td className="border border-gray-300 p-2">
                    {new Date(result.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {renderNotifications()}
      
      {/* Header */}
      <div className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                <span className="text-white font-bold text-sm">A</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-800">Acapella Risk Hunt Builder</h1>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => setActiveTab('builder')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'builder'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Builder
              </button>
              <button
                onClick={() => setActiveTab('games')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'games'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Games
              </button>
              <button
                onClick={() => setActiveTab('play')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'play'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Play
              </button>
              <button
                onClick={() => setActiveTab('results')}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  activeTab === 'results'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                Results
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
        {activeTab === 'results' && renderResults()}
      </div>

      {/* Modals */}
      {editingItem && (
        <div className="modal-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="modal bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Edit {editingItem.type}</h3>
            <input
              type="text"
              defaultValue={editingItem.name}
              className="w-full p-2 border rounded mb-4"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  // Handle update
                  setEditingItem(null);
                }
              }}
            />
            <div className="flex gap-2">
              <button
                onClick={() => setEditingItem(null)}
                className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded"
              >
                Cancel
              </button>
              <button
                onClick={() => setEditingItem(null)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {showDeleteModal && (
        <div className="modal-overlay fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="modal bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mr-3">
                <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 18.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Confirm Delete</h3>
                <p className="text-sm text-gray-500">This action cannot be undone</p>
              </div>
            </div>
            
            <div className="mb-6">
              <p className="text-gray-700 mb-2">Are you sure you want to delete this {showDeleteModal.type}?</p>
              {showDeleteModal.name && (
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm font-medium text-gray-800">
                    <span className="text-gray-600">Name:</span> {showDeleteModal.name}
                  </p>
                </div>
              )}
            </div>
            
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(null)}
                className="flex-1 bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Show loading state immediately
                  const deleteBtn = document.querySelector('.delete-confirm-btn');
                  if (deleteBtn) {
                    deleteBtn.innerHTML = '<span class="flex items-center justify-center"><svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Deleting...</span>';
                    deleteBtn.disabled = true;
                  }
                  
                  if (showDeleteModal.type === 'game') {
                    deleteGame(showDeleteModal.id);
                  } else if (showDeleteModal.type === 'image') {
                    deleteImage(showDeleteModal.id);
                  }
                  setShowDeleteModal(null);
                }}
                className="delete-confirm-btn flex-1 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg transition-colors"
              >
                Delete {showDeleteModal.type}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskHuntBuilder;