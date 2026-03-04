/**
 * Server-Sent Events (SSE) client for real-time data change notifications
 */
let eventSource: EventSource | null = null;
let onDataChangeCallback: (() => void) | null = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;
const MIN_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 30000;

/**
 * Connect to the SSE endpoint
 */
export const connectSSE = (callback: () => void) => {
  if (eventSource && eventSource.readyState === EventSource.OPEN) {
    console.log('SSE connection already active');
    return;
  }

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || `http://${window.location.hostname}:8000`;
  const apiKey: string = import.meta.env.VITE_API_KEY || '';
  const sseUrl = `${API_BASE_URL}/admin/events${apiKey ? `?api_key=${encodeURIComponent(apiKey)}` : ''}`;

  try {
    eventSource = new EventSource(sseUrl);
    onDataChangeCallback = callback;
    reconnectAttempts = 0;

    eventSource.onopen = () => {
      console.log('SSE connection established');
      reconnectAttempts = 0;
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('SSE message received:', data);

        if (data.event === 'data_changed') {
          console.log('Data changed event received, triggering refetch');
          if (onDataChangeCallback) {
            onDataChangeCallback();
          }
        }
      } catch (e) {
        console.error('Error parsing SSE message:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      // Check if connection is closed or error occurred
      if (eventSource?.readyState === EventSource.CLOSED || eventSource?.readyState === EventSource.CONNECTING) {
        console.log('SSE connection error, attempting to reconnect...');
        reconnect();
      }
    };

  } catch (error) {
    console.error('Failed to connect to SSE:', error);
    disconnectSSE();
    setTimeout(reconnect, MIN_RECONNECT_DELAY_MS);
  }
};

/**
 * Reconnect to the SSE endpoint with exponential backoff
 */
const reconnect = () => {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.log('Max reconnect attempts reached');
    return;
  }

  reconnectAttempts++;
  const delay = Math.min(
    MIN_RECONNECT_DELAY_MS * Math.pow(2, reconnectAttempts - 1),
    MAX_RECONNECT_DELAY_MS
  );

  console.log(`Attempting to reconnect (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}) in ${delay}ms...`);
  const savedCallback = onDataChangeCallback;
  disconnectSSE();

  setTimeout(() => {
    if (savedCallback) {
      connectSSE(savedCallback);
    }
  }, delay);
};

/**
 * Disconnect from the SSE endpoint
 */
export const disconnectSSE = () => {
  if (eventSource) {
    eventSource.close();
    eventSource = null;
    onDataChangeCallback = null;
    console.log('SSE connection closed');
  }
};

/**
 * Check if SSE is connected
 */
export const isSSEConnected = (): boolean => {
  return eventSource?.readyState === EventSource.OPEN;
};
