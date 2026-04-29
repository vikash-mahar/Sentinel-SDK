const express = require('express');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const app = express();

/**
 * Manual CORS Middleware
 */
app.use((req, res, next) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
    res.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

app.use(express.json());

const performanceLogger = require('./performance_logger');
app.use(performanceLogger);

const LOG_FILE = path.join(__dirname, 'logs', 'error.log');
if (!fs.existsSync(path.dirname(LOG_FILE))) {
    try {
        fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });
    } catch (e) {
        console.error("❌ Log Directory Error:", e.message);
    }
}

// --- Routes ---
/**
 * Route to simulate a crash
 */
app.get('/crash', (req, res) => {
    try {
        const modelFilePath = './models/user.js';
        let User;
        try {
            User = require(modelFilePath);
        } catch (e) {
            return res.status(500).send({ message: "Error loading user model" });
        }

        console.log("Attempting to access User.name...");
        if (User && User.name !== undefined) {
            const welcomeMessage = `Welcome, ${User.name.toUpperCase()}`; 
            res.send(welcomeMessage); 
        } else {
            res.status(404).send('User not found!');
        }
    } catch (error) {
        // Handle the error safely
        const errorData = `\n---\nFILE: ${__filename}\nERROR: ${error.message}\nSTACK: ${error.stack}\n---\n`;
        fs.appendFileSync(LOG_FILE, errorData);
        console.log("❌ App Crashed! Error logged for Sentinel.");
        return res.status(500).send({ message: "Sentinel is on the case. Check your terminal!" });
    }
});

/**
 * Route to initiate a predictive scan
 */
app.post('/api/sentinel/scan', async (req, res) => {
    console.log("🔍 [Sentinel] Initiating Predictive Scan via LangGraph...");

    // Sentinel Agent folder path
    const agentDir = path.join(__dirname, '../../sentinel_agent'); 

    // Target file path
    const targetFile = path.resolve(__dirname, '../src/server.js');

    /**
     * Use a more direct execution method to avoid 'spawn /bin/sh ENOENT' on Mac
     */
    const pythonCmd = `python3 -c "from graph import run_predictive_scan; run_predictive_scan('${targetFile}')"`;

    console.log(`🚀 Executing command in: ${agentDir}`);

    // Set up execution options to ensure the execution is done in a safe manner
    const execOptions = {
        cwd: agentDir,
        env: { ...process.env, PATH: process.env.PATH },
    };

    try {
        const output = await new Promise((resolve, reject) => {
            execSync(pythonCmd, execOptions, (error, stdout, stderr) => {
                if (error) {
                    reject(error);
                } else {
                    resolve(stdout.toString());
                }
            });
        });
        console.log(`✅ Scan Output: ${output}`);
        return res.json({ message: "Scan completed", output });
    } catch (error) {
        console.error(`❌ Scan Error: ${error.message}`);
        if (error.message.includes('not found') || error.message.includes('ENOENT')) {
            console.log("🔄 python3 not found, attempting with 'python' command...");
            const fallbackCmd = `python -c "from graph import run_predictive_scan; run_predictive_scan('${targetFile}')"`;
            return res.status(500).json({ error: "Python not found. Please check your PATH." });
        }
        return res.status(500).json({ error: "Scan failed", details: error.message });
    }
});

/**
 * Route to trigger a slow API
 */
app.get('/slow-api', async (req, res) => {
    const time = 100;
    await new Promise(resolve => setTimeout(resolve, time));
    res.send("Bhai, main bohot slow hoon, Sentinel ko bulao!");
});

// --- Start Server ---
const PORT = 3000;
const server = app.listen(PORT, () => {
    console.log(`🚀 Sentinel Backend running on http://localhost:${PORT}`);
    console.log(`📂 Monitoring Log: ${LOG_FILE}`);
}).on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.error(`❌ Error: Port ${PORT} is already in use!`);
    } else {
        console.error("❌ Server Error:", err);
    }
    process.exit(1);
});