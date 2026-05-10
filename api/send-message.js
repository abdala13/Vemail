/**
 * Protected Telegram Dispatcher
 * Securely formats incoming Mail.tm details into premium HTML blocks without exposing API secrets.
 */

export default async function handler(req, res) {
  // Enforce explicit CORS preflight responses
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!botToken) {
    return res.status(500).json({ error: 'Server integration secret unconfigured' });
  }

  try {
    const { chat_id, subject, from_name, from_address, text_preview, message_id } = req.body;

    if (!chat_id) {
      return res.status(400).json({ error: 'Target destination chat_id missing' });
    }

    // Sanitize tags to prevent Telegram HTML parse errors
    const safeSubject = (subject || 'No Subject').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const safeFromName = (from_name || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const safeFromAddr = (from_address || 'unknown@domain').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const safePreview = (text_preview || 'Empty message body').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Truncate overly long content to guarantee Telegram delivery limits
    const truncatedPreview = safePreview.length > 3000 ? safePreview.substring(0, 3000) + '... [Truncated]' : safePreview;

    const telegramPayload = `
📬 <b>New Message Received!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<b>From:</b> ${safeFromName} &lt;<code>${safeFromAddr}</code>&gt;
<b>Subject:</b> <b>${safeSubject}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

${truncatedPreview}

🛡️ <i>VeMail Instant Forwarding Engine</i>
`;

    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chat_id.toString().trim(),
        text: telegramPayload.trim(),
        parse_mode: 'HTML',
        disable_web_page_preview: true
      })
    });

    const result = await response.json();

    if (!result.ok) {
      console.error('Telegram Delivery Reject:', result);
      return res.status(400).json({ error: result.description || 'Failed to dispatch payload' });
    }

    return res.status(200).json({ success: true, message_id: result.result.message_id });
  } catch (error) {
    console.error('Forwarding Execution Failure:', error);
    return res.status(500).json({ error: 'Internal Forwarding Error' });
  }
}
