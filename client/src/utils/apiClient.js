import { supabase } from '../supabaseClient';

const BACKEND_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Function to check if token is expired or about to expire (within 5 minutes)
const isTokenExpired = (session) => {
  if (!session || !session.expires_at) return true;
  
  const now = Date.now() / 1000; // Current time in seconds
  const expiresAt = session.expires_at;
  const fiveMinutes = 5 * 60; // 5 minutes in seconds
  
  return now >= (expiresAt - fiveMinutes);
};

// Function to refresh token if needed
const refreshTokenIfNeeded = async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      throw new Error('No active session');
    }
    
    // Check if token is expired or about to expire
    if (isTokenExpired(session)) {
      console.log('Token expired or about to expire, refreshing...');
      const { data, error } = await supabase.auth.refreshSession();
      
      if (error) {
        console.error('Error refreshing token:', error);
        throw error;
      }
      
      if (!data.session) {
        throw new Error('Failed to refresh session');
      }
      
      console.log('Token refreshed successfully');
      return data.session;
    }
    
    return session;
  } catch (error) {
    console.error('Error in refreshTokenIfNeeded:', error);
    throw error;
  }
};

// Generic API call function with automatic token refresh
export const apiCall = async (endpoint, options = {}) => {
  try {
    // Refresh token if needed
    const session = await refreshTokenIfNeeded();
    
    // Prepare headers
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`,
      ...options.headers,
    };
    
    // Make the API call
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      headers,
    });
    
    // Handle 401 errors (token expired despite refresh attempt)
    if (response.status === 401) {
      console.log('Received 401, attempting to refresh token and retry...');
      
      // Try to refresh token one more time
      const { data, error } = await supabase.auth.refreshSession();
      
      if (error || !data.session) {
        throw new Error('Authentication failed. Please log in again.');
      }
      
      // Retry the request with new token
      const retryResponse = await fetch(`${BACKEND_URL}${endpoint}`, {
        ...options,
        headers: {
          ...headers,
          'Authorization': `Bearer ${data.session.access_token}`,
        },
      });
      
      if (!retryResponse.ok) {
        const errorText = await retryResponse.text();
        throw new Error(`HTTP ${retryResponse.status}: ${errorText}`);
      }
      
      return retryResponse;
    }
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    return response;
  } catch (error) {
    console.error('API call error:', error);
    throw error;
  }
};

// Convenience functions for common HTTP methods
export const apiGet = (endpoint) => apiCall(endpoint, { method: 'GET' });
export const apiPost = (endpoint, body) => apiCall(endpoint, { 
  method: 'POST', 
  body: JSON.stringify(body) 
});
export const apiPut = (endpoint, body) => apiCall(endpoint, { 
  method: 'PUT', 
  body: JSON.stringify(body) 
});
export const apiDelete = (endpoint) => apiCall(endpoint, { method: 'DELETE' });

// Debug function to check token status
export const debugTokenStatus = async () => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      console.log('❌ No active session');
      return;
    }
    
    const now = Date.now() / 1000;
    const expiresAt = session.expires_at;
    const timeLeft = expiresAt - now;
    
    console.log('🔍 Token Status:');
    console.log('- User ID:', session.user.id);
    console.log('- Email:', session.user.email);
    console.log('- Token expires at:', new Date(expiresAt * 1000).toLocaleString());
    console.log('- Time left:', Math.floor(timeLeft / 60), 'minutes');
    console.log('- Is expired:', isTokenExpired(session));
    
    // Test the token
    try {
      const response = await apiGet('/api/auth-test');
      const data = await response.json();
      console.log('✅ Token is valid:', data);
    } catch (error) {
      console.log('❌ Token validation failed:', error.message);
    }
  } catch (error) {
    console.error('Debug error:', error);
  }
}; 