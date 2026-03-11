/**
 * 🦝 Raccoon Browser - Main Process (Simplified)
 * Just handles the window - all logic is in Flask backend
 */

const { app, BrowserWindow, session } = require('electron');
const path = require('path');

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 800,
    minHeight: 600,
    title: 'Raccoon Browser',
    icon: path.join(__dirname, '../../assets/icons/raccoon.png'),
    backgroundColor: '#0a0a0a',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    show: false,
  });

  mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    console.log('🦝 Raccoon Browser initialized');
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Block trackers at network level
  setupTrackerBlocking();
}

function setupTrackerBlocking() {
  const trackerDomains = [
    'google-analytics.com',
    'googletagmanager.com',
    'doubleclick.net',
    'facebook.net',
    'facebook.com/tr',
    'adservice.google.com',
  ];

  session.defaultSession.webRequest.onBeforeRequest(
    { urls: ['*://*/*'] },
    (details, callback) => {
      const url = new URL(details.url);
      const isTracker = trackerDomains.some(d => url.hostname.includes(d));
      callback({ cancel: isTracker });
    }
  );
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});