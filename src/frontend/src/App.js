import React, { useState, useEffect } from 'react';
import Chat from './components/Chat';
import ScheduledJobs from './components/ScheduledJobs';
import { WebSocketService } from './services/websocket';
import { apiService } from './services/api';

function App() {
  const [messages, setMessages] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  
  useEffect(() => {
    // Initialize WebSocket connection using singleton
    const wsService = WebSocketService.getInstance();
    
    // Add event handlers and store cleanup functions
    const cleanupMessage = wsService.addMessageHandler((data) => {
      if (data.type === 'chat_message') {
        setMessages(prev => [...prev, data.message]);
      } else if (data.type === 'job_created') {
        setJobs(prev => [...prev, data.job]);
      } else if (data.type === 'monitoring_update') {
        // Handle monitoring updates
        console.log('Monitoring update:', data.result);
      }
    });
    
    const cleanupConnect = wsService.addConnectHandler(() => {
      setIsConnected(true);
    });
    
    const cleanupDisconnect = wsService.addDisconnectHandler(() => {
      setIsConnected(false);
    });
    
    wsService.connect();
    
    // Load initial data
    loadInitialData();
    
    return () => {
      // Clean up event handlers
      cleanupMessage();
      cleanupConnect();
      cleanupDisconnect();
    };
  }, []);
  
  const loadInitialData = async () => {
    try {
      const [messagesData, jobsData] = await Promise.all([
        apiService.getChatMessages(),
        apiService.getJobs()
      ]);
      
      setMessages(messagesData);
      setJobs(jobsData);
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  };
  
  const sendMessage = (content) => {
    if (isConnected) {
      WebSocketService.getInstance().sendMessage({
        type: 'user_message',
        content: content
      });
    }
  };
  
  const toggleJob = async (jobId) => {
    try {
      const updatedJob = await apiService.toggleJob(jobId);
      setJobs(prev => prev.map(job => 
        job.id === jobId ? { ...job, is_active: updatedJob.is_active } : job
      ));
    } catch (error) {
      console.error('Error toggling job:', error);
    }
  };
  
  const deleteJob = async (jobId) => {
    try {
      await apiService.deleteJob(jobId);
      setJobs(prev => prev.filter(job => job.id !== jobId));
    } catch (error) {
      console.error('Error deleting job:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar for scheduled jobs */}
      <div className="w-1/3 bg-white border-r border-gray-200">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-800">Scheduled Jobs</h2>
          <div className="flex items-center mt-2">
            <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
        <ScheduledJobs 
          jobs={jobs} 
          onToggleJob={toggleJob}
          onDeleteJob={deleteJob}
        />
      </div>
      
      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 p-4">
          <h1 className="text-xl font-bold text-gray-800">SiteWatch Chat</h1>
          <p className="text-sm text-gray-600">Ask me to monitor websites for changes</p>
        </div>
        
        <Chat 
          messages={messages}
          onSendMessage={sendMessage}
          isConnected={isConnected}
        />
      </div>
    </div>
  );
}

export default App; 