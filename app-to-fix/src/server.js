const express = require('express');
const fs = require('fs');
const path = require('path');
// Import the model (Taki indexer aur RAG ko connection mil sake)
const User = require('./models/user.js'); 

const app = express();
const LOG_FILE = path.join(__dirname, './logs/error.log'); // Check path according to your structure

// Ensure logs directory exists
if (!fs.existsSync(path.dirname(LOG_FILE))) {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
}

app.get('/crash', (req, res) => {
    try {
        // BUG: Hum 'User' object use kar rahe hain jo models/User.js se aa raha hai
        // Lekin hum 'name' call kar rahe hain jabki file mein 'fullName' hai.
        res.send(`Welcome, ${User.name.toUpperCase()}`); 
    } catch (error) {
        const errorData = `\n---\nFILE: ${__filename}\nERROR: ${error.message}\nSTACK: ${error.stack}\n---\n`;
        fs.appendFileSync(LOG_FILE, errorData);
        console.log("❌ App Crashed! Error logged for Sentinel.");
        res.status(500).send("Sentinel is on the case. Check your terminal!");
    }
});

app.listen(3000, () => console.log("🚀 Patient App on port 3000"));