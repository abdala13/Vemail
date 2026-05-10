global.telegramLinkCache = global.telegramLinkCache || {};

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' });
  }

  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  if (!botToken) {
    return res.status(500).json({ error: 'Server misconfiguration' });
  }

  try {
    const update = req.body;

    if (update && update.message && update.message.text) {
      const chatId = update.message.chat.id;
      const text = update.message.text.trim();

      let replyMessage = '';

      // التحقق مما إذا كان المستخدم قادماً عبر رابط التحويل المباشر
      if (text.startsWith('/start VEMAIL')) {
        const code = text.replace('/start ', '').trim();
        global.telegramLinkCache[code] = chatId;

        replyMessage = `
✅ <b>تم الاتصال بنجاح!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
تم ربط هذا الحساب ببريدك المؤقت على موقع VeMail.
ستصلك جميع رسائل التفعيل الجديدة هنا فورياً.

🔑 <b>معرف المحادثة الخاص بك (Chat ID):</b>
<code>${chatId}</code>

<i>(إذا لم يتحدث الموقع تلقائياً، قم بنسخ المعرف أعلاه ولصقه في خانة الربط اليدوي بالموقع).</i>
`;
      } else {
        // في حال ضغط المستخدم /start بدون كود (تحدث في بعض الهواتف)
        replyMessage = `
مرحباً بك في بوت <b>VeMail</b> 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
لاستقبال رسائل البريد المؤقت هنا، قم بنسخ <b>معرف المحادثة</b> الخاص بك وأدخله في الموقع:

👇 اضغط على الرقم للنسخ:
<code>${chatId}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
<i>قم بلصق هذا الرقم في خانة "الربط اليدوي" داخل الموقع ليتم التفعيل فوراً.</i>
`;
      }

      // إرسال الرد الفوري للمستخدم
      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: chatId,
          text: replyMessage.trim(),
          parse_mode: 'HTML'
        })
      });
    }

    return res.status(200).json({ received: true });
  } catch (error) {
    console.error('Webhook Error:', error);
    return res.status(500).json({ error: 'Fatal Webhook Exception' });
  }
}
