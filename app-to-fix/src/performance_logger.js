const fs = require('fs');
const path = require('path');

module.exports = (req, res, next) => {
    const start = Date.now();

    res.on('finish', () => {
        const duration = Date.now() - start;
        console.log(`⏱️ Request to ${req.url} took ${duration}ms`); // Terminal pe check karne ke liye

        if (duration > 200) {
            const logEntry = `[PERF] ${new Date().toISOString()} | ${req.method} ${req.url} took ${duration}ms\n`;
            
            // Absolute path use karo taaki koi confusion na rahe
            const logDir = path.join(__dirname, 'logs');
            const logPath = path.join(logDir, 'performance.log');

            // Folder nahi hai toh banao
            if (!fs.existsSync(logDir)) {
                fs.mkdirSync(logDir, { recursive: true });
            }

            try {
                fs.appendFileSync(logPath, logEntry);
                console.log(`✅ Performance log updated!`);
            } catch (err) {
                console.error(`❌ Failed to write to log: ${err.message}`);
            }
        }
    });

    next();
};