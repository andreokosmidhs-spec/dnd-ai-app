/**
 * Centralized LocalStorage Keys
 * 
 * CRITICAL: All localStorage keys must be defined here.
 * No component should use hardcoded localStorage keys.
 * 
 * This prevents:
 * - Duplicate key collisions
 * - Typos causing data loss
 * - Accidental overwrites
 */

// Session Management
export const KEYS = {
  // Session & Campaign
  SESSION_ID: 'game-state-session-id',
  CAMPAIGN_ID: 'game-state-campaign-id',
  
  // Intro State
  INTRO_PLAYED: 'dm-intro-played',
  INTRO_PLAYED_SESSION: (sessionId) => `dm-intro-played-${sessionId}`,
  
  // Game State (Legacy - to be migrated)
  CAMPAIGN_GAMESTATE: 'rpg-campaign-gamestate',
  CAMPAIGN_CHARACTER: 'rpg-campaign-character',
  
  // DM Log Messages
  DM_LOG_MESSAGES: (sessionId) => `dm-log-messages-${sessionId}`,
  DM_LOG_OPTIONS: (sessionId) => `dm-log-options-${sessionId}`,
  DM_INTENT_MODE: 'dm-intent-mode',
  
  // GameStateContext Keys
  GAME_STATE_CHARACTER: (sessionId) => `game-state-character-${sessionId}`,
  GAME_STATE_WORLD: (sessionId) => `game-state-world-${sessionId}`,
  GAME_STATE_NOTES: (sessionId) => `game-state-notes-${sessionId}`,
  GAME_STATE_THREAT: (sessionId) => `game-state-threat-${sessionId}`,
  GAME_STATE_DMENGINE: (sessionId) => `game-state-dmengine-${sessionId}`,
  
  // DM Chat (Legacy)
  DM_CHAT_SESSION_ID: 'dm-chat-session-id',
  DM_CHAT_MESSAGES: (sessionId) => `dm-chat-messages-${sessionId}`,
  DM_CHAT_OPTIONS: (sessionId) => `dm-chat-options-${sessionId}`,
  
  // UI Preferences
  TTS_ENABLED: 'rpg-tts-enabled',
  INFO_DRAWER_TAB: 'rpg-info-drawer-tab',
  
  // Testing/Dev
  CHECK_ATTEMPTS: 'check_attempts'
};

/**
 * Safe localStorage wrapper with error handling
 */
export const storage = {
  /**
   * Get item from localStorage
   * @param {string} key - localStorage key
   * @param {*} defaultValue - Default value if key doesn't exist
   * @returns {*} Parsed value or defaultValue
   */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      if (item === null) return defaultValue;
      
      // Try to parse as JSON
      try {
        return JSON.parse(item);
      } catch {
        // Return as string if not JSON
        return item;
      }
    } catch (error) {
      console.error(`[Storage] Error reading key "${key}":`, error);
      return defaultValue;
    }
  },
  
  /**
   * Set item in localStorage
   * @param {string} key - localStorage key
   * @param {*} value - Value to store (will be JSON stringified if object)
   */
  set(key, value) {
    try {
      const stringValue = typeof value === 'string' ? value : JSON.stringify(value);
      localStorage.setItem(key, stringValue);
      console.debug(`[Storage] Set "${key}"`);
    } catch (error) {
      console.error(`[Storage] Error writing key "${key}":`, error);
    }
  },
  
  /**
   * Remove item from localStorage
   * @param {string} key - localStorage key
   */
  remove(key) {
    try {
      localStorage.removeItem(key);
      console.debug(`[Storage] Removed "${key}"`);
    } catch (error) {
      console.error(`[Storage] Error removing key "${key}":`, error);
    }
  },
  
  /**
   * Clear all localStorage
   */
  clear() {
    try {
      localStorage.clear();
      console.debug('[Storage] Cleared all');
    } catch (error) {
      console.error('[Storage] Error clearing:', error);
    }
  },
  
  /**
   * Check if key exists
   * @param {string} key - localStorage key
   * @returns {boolean}
   */
  has(key) {
    return localStorage.getItem(key) !== null;
  }
};

/**
 * Key validation - ensures only known keys are used
 * @param {string} key
 * @returns {boolean}
 */
export function isValidKey(key) {
  const allKeys = Object.values(KEYS);
  const allStaticKeys = allKeys.filter(k => typeof k === 'string');
  const allDynamicKeyPrefixes = [
    'dm-intro-played-',
    'dm-log-messages-',
    'dm-log-options-',
    'game-state-character-',
    'game-state-world-',
    'game-state-notes-',
    'game-state-threat-',
    'game-state-dmengine-',
    'dm-chat-messages-',
    'dm-chat-options-'
  ];
  
  // Check static keys
  if (allStaticKeys.includes(key)) return true;
  
  // Check dynamic keys
  return allDynamicKeyPrefixes.some(prefix => key.startsWith(prefix));
}

export default {
  KEYS,
  storage,
  isValidKey
};
