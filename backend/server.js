import express from 'express';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import dotenv from 'dotenv';
import fetch from 'node-fetch';
import TelegramBot from 'node-telegram-bot-api';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import { v4 as uuidv4 } from 'uuid';

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.use(cors({
  origin: process.env.FRONTEND_URL,
  credentials: true
}));

app.use(cookieParser());

const db = await open({
  filename: './database.sqlite',
  driver: sqlite3.Database
});

await db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT UNIQUE,
  email TEXT,
  password TEXT,
  token TEXT,
  telegram_chat_id TEXT,
  telegram_code TEXT,
  last_message_id TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
`);

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, {
  polling: true
});

const clients = new Map();

function generateRandomName() {
  return 'vmail_' + Math.random().toString(36).substring(2, 10);
}

async function createTempEmail() {

  const domainsRes = await fetch('https://api.mail.tm/domains');
  const domainsData = await domainsRes.json();

  const domain = domainsData['hydra:member'][0].domain;

  const username = generateRandomName();
  const password = 'TempPass123';

  const address = `${username}@${domain}`;

  await fetch('https://api.mail.tm/accounts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      address,
      password
    })
  });

  const tokenRes = await fetch('https://api.mail.tm/token', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      address,
      password
    })
  });

  const tokenData = await tokenRes.json();

  return {
    address,
    password,
    token: tokenData.token
  };
}

app.get('/', (req, res) => {
  res.send('Vmail Backend Running 🚀');
});

app.post('/api/create-email', async (req, res) => {

  try {

    const emailData = await createTempEmail();

    const sessionId = uuidv4();

    await db.run(`
      INSERT INTO users
      (session_id, email, password, token)
      VALUES (?, ?, ?, ?)
    `,
      sessionId,
      emailData.address,
      emailData.password,
      emailData.token
    );

    res.cookie('vmail_session', sessionId, {
      httpOnly: true,
      secure: true,
      sameSite: 'none',
      maxAge: 1000 * 60 * 60 * 24 * 7
    });

    res.json({
      success: true,
      email: emailData.address
    });

  } catch (error) {

    console.log(error);

    res.status(500).json({
      error: 'Failed to create email'
    });
  }
});

app.get('/api/me', async (req, res) => {

  const sessionId = req.cookies.vmail_session;

  if (!sessionId) {
    return res.json({
      logged: false
    });
  }

  const user = await db.get(
    'SELECT * FROM users WHERE session_id = ?',
    sessionId
  );

  if (!user) {
    return res.json({
      logged: false
    });
  }

  res.json({
    logged: true,
    email: user.email,
    telegramLinked: !!user.telegram_chat_id
  });
});

app.post('/api/telegram/link', async (req, res) => {

  const sessionId = req.cookies.vmail_session;

  if (!sessionId) {
    return res.status(401).json({
      error: 'No session'
    });
  }

  const user = await db.get(
    'SELECT * FROM users WHERE session_id = ?',
    sessionId
  );

  if (!user) {
    return res.status(401).json({
      error: 'User not found'
    });
  }

  const code = Math.floor(100000 + Math.random() * 900000).toString();

  await db.run(
    'UPDATE users SET telegram_code = ? WHERE session_id = ?',
    code,
    sessionId
  );

  res.json({
    success: true,
    code,
    botUrl: `https://t.me/${process.env.TELEGRAM_BOT_USERNAME}`
  });
});

app.get('/api/stream', async (req, res) => {

  const sessionId = req.cookies.vmail_session;

  if (!sessionId) {
    return res.status(401).end();
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  clients.set(sessionId, res);

  req.on('close', () => {
    clients.delete(sessionId);
  });
});

bot.onText(/\/start (.+)/, async (msg, match) => {

  const code = match[1];

  const user = await db.get(
    'SELECT * FROM users WHERE telegram_code = ?',
    code
  );

  if (!user) {
    await bot.sendMessage(msg.chat.id, '❌ Invalid verification code');
    return;
  }

  await db.run(
    'UPDATE users SET telegram_chat_id = ? WHERE id = ?',
    msg.chat.id,
    user.id
  );

  await bot.sendMessage(
    msg.chat.id,
`✅ Telegram linked successfully

📧 Email:
${user.email}

🔔 You will now receive all incoming emails instantly.`
  );
});

async function checkMessages() {

  const users = await db.all('SELECT * FROM users');

  for (const user of users) {

    try {

      const res = await fetch('https://api.mail.tm/messages', {
        headers: {
          Authorization: `Bearer ${user.token}`
        }
      });

      if (!res.ok) {
        continue;
      }

      const data = await res.json();

      const messages = data['hydra:member'] || [];

      if (messages.length === 0) {
        continue;
      }

      const latest = messages[0];

      if (latest.id === user.last_message_id) {
        continue;
      }

      await db.run(
        'UPDATE users SET last_message_id = ? WHERE id = ?',
        latest.id,
        user.id
      );

      const fullMessageRes = await fetch(
        `https://api.mail.tm/messages/${latest.id}`,
        {
          headers: {
            Authorization: `Bearer ${user.token}`
          }
        }
      );

      const fullMessage = await fullMessageRes.json();

      if (user.telegram_chat_id) {

        await bot.sendMessage(
          user.telegram_chat_id,
`📩 رسالة جديدة

👤 من:
${latest.from.address}

📝 العنوان:
${latest.subject || 'No subject'}

📧 إلى:
${user.email}

━━━━━━━━━━

${fullMessage.text || ''}`
        );
      }

      const client = clients.get(user.session_id);

      if (client) {
        client.write(`data: ${JSON.stringify(fullMessage)}\n\n`);
      }

    } catch (error) {
      console.log(error);
    }
  }
}

setInterval(checkMessages, 2000);

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});