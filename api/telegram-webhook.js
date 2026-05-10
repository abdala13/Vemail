/**
 * Telegram Webhook Processor
 * Receives /start CODE commands directly from Telegram without databases.
 * Pairs session via memory bridge and securely replies with fallback connection credentials.
 */

global.telegramLinkCache = global.telegramLinkCache || {};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!botToken) {
    console.error('CRITICAL: TELEGRAM_BOT_TOKEN is missing.');
    return res.status(500).json({ error: 'Server misconfiguration' });
  }

  try {
    const update = req.body;

    // Verify incoming message structure safely
    if (update && update.message && update.message.text) {
      const chatId = update.message.chat.id;
      const text = update.message.text.trim();

      // Check for deep-linked startup command: /start VEMAIL-XXXXXX
      if (text.startsWith('/start VEMAIL-')) {
        const code = text.replace('/start ', '').trim();
        
        // Store mapping securely in isolated instance execution memory
        global.telegramLinkCache[code] = chatId;

        // Dispatch stunning welcome message back to Telegram Client
        const replyMessage = `
✅ <b>Successfully Connected to VeMail!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your secure temporary inbox is now linked to this chat.
All incoming emails will be forwarded here instantly.

🔑 <b>Manual Override ID:</b> <code>${chatId}</code>

<i>If your browser does not link automatically within 3 seconds, simply paste the ID above into the website settings.</i>
`;

        await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: chatId,
            text: replyMessage.trim(),
            parse_mode: 'HTML'
          })
        });

        return res.status(200).json({ success: true });
      }

      // Default Help Handler for generic commands
      if (text === '/start' || text === '/help') {
        const helpMsg = `🛡️ <b>VeMail Forwarding Bot</b>\n\nTo connect your temporary inbox, please initiate the connection directly from the VeMail application interface.`;
        await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ chat_id: chatId, text: helpMsg, parse_mode: 'HTML' })
        });
      }
    }

    // Acknowledge Telegram instantly to prevent retries
    return res.status(200).json({ received: true });
  } catch (error) {
    console.error('Webhook Processing Exception:', error);
    return res.status(500).json({ error: 'Webhook processing failed' });
  }
}
