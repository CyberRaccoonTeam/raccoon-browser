/**
 * 🦝 Raccoon Browser - Preload Script
 * Minimal - backend handles everything via HTTP
 */

const { contextBridge } = require('electron');

// Expose platform info only - all logic via Flask backend
contextBridge.exposeInMainWorld('raccoon', {
  platform: process.platform,
  version: '0.1.0',
});

console.log('🦝 Preload script loaded');