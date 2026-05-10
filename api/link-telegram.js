/**
 * Stateless Telegram Linking Endpoint
 * Handles verification code generation and stateless warm-memory connection checking.
 */

// Global cache to bridge verification across warm serverless invocations
global.telegramLinkCache = global.telegramLinkCache || {};

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const { action, code } = req.query;
  const botUsername = process.env.TELEGRAM_BOT_USERNAME || '';

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  try {
    // Action 1: Generate a unique connection payload
    if (action === 'generate') {
      const newCode = 'VEMAIL-' + Math.floor(100000 + Math.random() * 900000);
      return res.status(200).json({
        success: true,
        code: newCode,
        bot_username: botUsername,
        bot_url: `https://t.me/${botUsername}?start=${newCode}`
      });
    }

    // Action 2: Check in-memory cache for incoming webhook triggers
    if (action === 'check') {
      if (!code) {
        return res.status(400).json({ error: 'Verification code required' });
      }

      const chatId = global.telegramLinkCache[code];
      
      if (chatId) {
        // Cleanup cache once successfully consumed
        delete global.telegramLinkCache[code];
        return res.status(200).json({
          linked: true,
          chat_id: chatId
        });
      }

      return res.status(200).json({ linked: false });
    }

    return res.status(400).json({ error: 'Invalid action specified' });
  } catch (error) {
    console.error('Link Telegram Error:', error);
    return res.status(500).json({ error: 'Internal Serverless Error' });
  }
}
