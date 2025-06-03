require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const ytDlp = require('yt-dlp-exec');
const path = require('path');
const fs = require('fs').promises;

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(express.json());
app.use(cors({
  origin: process.env.ALLOWED_ORIGIN || '*'
}));

// Create temp directory if it doesn't exist
const tempDir = path.join(__dirname, '..', 'temp');
fs.mkdir(tempDir, { recursive: true }).catch(console.error);

// Utility function to generate a random filename
const generateFileName = () => {
  return `${Date.now()}-${Math.random().toString(36).substring(7)}`;
};

// Utility function to clean up temporary files
const cleanup = async (filePath) => {
  try {
    await fs.unlink(filePath);
  } catch (error) {
    console.error('Error cleaning up file:', error);
  }
};

// YouTube download endpoint
app.post('/api/download/youtube', async (req, res) => {
  const { url } = req.body;
  
  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  const outputFile = path.join(tempDir, `${generateFileName()}.mp3`);

  try {
    await ytDlp(url, {
      extractAudio: true,
      audioFormat: 'mp3',
      output: outputFile,
      noCheckCertificates: true,
      noWarnings: true,
      preferFreeFormats: true
    });

    res.download(outputFile, async (err) => {
      if (err) {
        console.error('Error sending file:', err);
      }
      await cleanup(outputFile);
    });
  } catch (error) {
    console.error('YouTube download error:', error);
    res.status(500).json({ error: 'Failed to download YouTube audio' });
  }
});

// Spotify download endpoint
app.post('/api/download/spotify', async (req, res) => {
  const { url } = req.body;
  
  if (!url) {
    return res.status(400).json({ error: 'URL is required' });
  }

  const outputFile = path.join(tempDir, `${generateFileName()}.mp3`);

  try {
    const spotdl = spawn('spotdl', [url, '--output', outputFile]);
    
    spotdl.stderr.on('data', (data) => {
      console.error(`spotdl error: ${data}`);
    });

    spotdl.on('close', (code) => {
      if (code === 0) {
        res.download(outputFile, async (err) => {
          if (err) {
            console.error('Error sending file:', err);
          }
          await cleanup(outputFile);
        });
      } else {
        res.status(500).json({ error: 'Failed to download Spotify track' });
      }
    });
  } catch (error) {
    console.error('Spotify download error:', error);
    res.status(500).json({ error: 'Failed to download Spotify track' });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
}); 