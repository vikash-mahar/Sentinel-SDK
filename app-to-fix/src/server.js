const express = require('express');
const fs = require('fs');
const path = require('path');

// Models and Middleware
const User = require('./models/user.js'); 
const performanceLogger = require('./performance_logger');

const app = express();

// Performance Monitoring Middleware
app.use(performanceLogger);

// Logs Path (Absolute path is safer for Sentinel)
const LOG_FILE = path.join(__dirname, 'logs', 'error.log');

// Ensure logs directory exists at startup
if (!fs.existsSync(path.dirname(LOG_FILE))) {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
}

// --- 1. CRASH ROUTE (The Bug Hunter) ---
app.get('/crash', (req, res) => {
    try {
        /**
         * PLANNED BUG:
         * models/user.js mein 'fullName' hai, lekin hum 'name' access kar rahe hain.
         * User.fullName undefined hoga, aur undefined.toUpperCase() crash kar dega.
         */
        console.log("Attempting to access UserFullName...");
        const userExists = User.findOne({}, { name: 1 }); // Safe way to query with projection
        const welcomeMessage = (userExists && userExists.name)? userExists.name.toUpperCase(): ""; // Safe way to uppercase name
        
        res.send(welcomeMessage); 
    } catch (error) {
        // Sentinel specific format (Don't change this)
        const errorData = `\n---\nFILE: ${__filename}\nERROR: ${error.message}\nSTACK: ${error.stack}\n---\n`;
        
        fs.appendFileSync(LOG_FILE, errorData);
        console.log("❌ App Crashed! Error logged for Sentinel.");
        
        res.status(500).send("Sentinel is on the case. Check your terminal!");
    }
});