/**
 * Centralized API Client
 * 
 * Single source for all backend communication with:
 * - Consistent error handling
 * - Automatic JSON parsing
 * - Environment-based URL configuration
 */

// Get backend URL from environment (never hardcode!)
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

/**
 * Create error response for network/parsing errors
 */
function createErrorResponse(error) {
  const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
  
  return {
    success: false,
    data: null,
    error: {
      type: 'network_error',
      message: errorMessage,
      details: {}
    }
  };
}

/**
 * Parse response and ensure it matches ApiResponse format
 */
async function parseResponse(response) {
  try {
    const json = await response.json();
    
    // Check if response already has the normalized format
    if ('success' in json && 'data' in json && 'error' in json) {
      return json;
    }
    
    // Legacy responses without envelope - wrap them
    if (response.ok) {
      return {
        success: true,
        data: json,
        error: null
      };
    } else {
      return {
        success: false,
        data: null,
        error: {
          type: 'http_error',
          message: json.detail || json.message || 'Request failed',
          details: { status_code: response.status }
        }
      };
    }
  } catch (parseError) {
    // JSON parsing failed
    return {
      success: false,
      data: null,
      error: {
        type: 'parse_error',
        message: 'Failed to parse response',
        details: { status_code: response.status }
      }
    };
  }
}

/**
 * GET request
 */
export async function get(path, options = {}) {
  try {
    let url = `${BACKEND_URL}${path}`;
    
    // CRITICAL FIX: Append query parameters if provided
    if (options.params) {
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          searchParams.append(key, value);
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      signal: options.signal
    });
    
    return parseResponse(response);
  } catch (error) {
    return createErrorResponse(error);
  }
}

/**
 * POST request
 */
export async function post(path, body, options = {}) {
  try {
    const url = `${BACKEND_URL}${path}`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(body),
      signal: options.signal
    });
    
    return parseResponse(response);
  } catch (error) {
    return createErrorResponse(error);
  }
}

/**
 * PUT request
 */
export async function put(path, body, options = {}) {
  try {
    const url = `${BACKEND_URL}${path}`;
    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: JSON.stringify(body),
      signal: options.signal
    });
    
    return parseResponse(response);
  } catch (error) {
    return createErrorResponse(error);
  }
}

/**
 * PATCH request
 */
export async function patch(path, body, options = {}) {
  try {
    let url = `${BACKEND_URL}${path}`;
    
    // Append query parameters if provided
    if (options.params) {
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          searchParams.append(key, value);
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += `?${queryString}`;
      }
    }
    
    const response = await fetch(url, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: options.signal
    });
    
    return parseResponse(response);
  } catch (error) {
    return createErrorResponse(error);
  }
}

/**
 * DELETE request
 */
export async function del(path, options = {}) {
  try {
    const url = `${BACKEND_URL}${path}`;
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      signal: options.signal
    });
    
    return parseResponse(response);
  } catch (error) {
    return createErrorResponse(error);
  }
}

/**
 * Helper to check if response is successful
 */
export function isSuccess(response) {
  return response.success && response.data !== null;
}

/**
 * Helper to extract error message
 */
export function getErrorMessage(error) {
  if (!error) return 'Unknown error';
  return error.message;
}

// Export default object with all methods
const apiClient = {
  get,
  post,
  put,
  patch,
  delete: del,
  isSuccess,
  getErrorMessage
};

export default apiClient;
