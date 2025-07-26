class WebSocketService {
  constructor() {
    this.ws = null;
    this.messageHandlers = new Set();
    this.connectHandlers = new Set();
    this.disconnectHandlers = new Set();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 1000;
  }
  
  static getInstance() {
    if (!WebSocketService.instance) {
      WebSocketService.instance = new WebSocketService();
    }
    return WebSocketService.instance;
  }

  addMessageHandler(handler) {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  addConnectHandler(handler) {
    this.connectHandlers.add(handler);
    return () => this.connectHandlers.delete(handler);
  }

  addDisconnectHandler(handler) {
    this.disconnectHandlers.add(handler);
    return () => this.disconnectHandlers.delete(handler);
  }
  
  connect() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8081/ws`;
      
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.connectHandlers.forEach(handler => {
          try {
            handler();
          } catch (error) {
            console.error('Error in connect handler:', error);
          }
        });
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.messageHandlers.forEach(handler => {
            try {
              handler(data);
            } catch (error) {
              console.error('Error in message handler:', error);
            }
          });
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.disconnectHandlers.forEach(handler => {
          try {
            handler();
          } catch (error) {
            console.error('Error in disconnect handler:', error);
          }
        });
        this.reconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
    }
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('WebSocket is not connected');
    }
  }
  
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval * this.reconnectAttempts);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
}

export { WebSocketService }; 