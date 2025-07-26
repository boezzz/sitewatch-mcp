class ApiService {
  constructor() {
    this.baseUrl = '/api';
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }
  
  async getChatMessages(limit = 50) {
    return this.request(`/chat/messages?limit=${limit}`);
  }
  
  async getJobs() {
    return this.request('/jobs');
  }
  
  async getJobResults(jobId, limit = 10) {
    return this.request(`/jobs/${jobId}/results?limit=${limit}`);
  }
  
  async toggleJob(jobId) {
    return this.request(`/jobs/${jobId}/toggle`, {
      method: 'POST',
    });
  }
  
  async deleteJob(jobId) {
    return this.request(`/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }
  
  async getStats() {
    return this.request('/stats');
  }
}

const apiService = new ApiService();
export { apiService }; 