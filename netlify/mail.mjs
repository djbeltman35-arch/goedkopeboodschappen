// Mail versturen via SMTP met TLS (bijvoorbeeld Gmail met een app-wachtwoord), zonder extra pakketten.
// Gebruik: const v = await verbind({ host, port, user, pass }); await v.stuur(bericht({...})); await v.sluit();
import tls from 'node:tls';
import crypto from 'node:crypto';

export async function verbind({ host = process.env.SMTP_HOST || 'smtp.gmail.com', port = +(process.env.SMTP_PORT || 465), user, pass, naam = 'boodschappenvergelijk.nl', tlsOpties = {} }) {
  const sock = tls.connect({ host, port, servername: host, ...tlsOpties });
  sock.setEncoding('utf8');
  let buf = '', wachter = null;
  const regels = [];
  const verwerk = () => {
    // Een antwoord is compleet bij een regel "250 ..." (spatie na de code); "250-..." betekent dat er meer komt.
    let i;
    while ((i = buf.indexOf('\r\n')) >= 0) {
      const r = buf.slice(0, i); buf = buf.slice(i + 2); regels.push(r);
      if (/^\d{3} /.test(r) || /^\d{3}$/.test(r)) {
        const all = regels.splice(0), code = +r.slice(0, 3);
        if (wachter) { const w = wachter; wachter = null; w.ok({ code, tekst: all.join('\n') }); }
      }
    }
  };
  sock.on('data', d => { buf += d; verwerk(); });
  sock.on('error', e => { if (wachter) { const w = wachter; wachter = null; w.fout(e); } });
  const antwoord = (ms = 20000) => new Promise((ok, fout) => {
    const t = setTimeout(() => { wachter = null; fout(new Error('SMTP: geen antwoord')); }, ms);
    wachter = { ok: v => { clearTimeout(t); ok(v); }, fout: e => { clearTimeout(t); fout(e); } };
    verwerk();
  });
  const opdracht = async (regel, verwacht) => {
    const p = antwoord(); sock.write(regel + '\r\n'); const a = await p;
    if (!verwacht.includes(a.code)) throw new Error(`SMTP ${a.code} na ${regel.startsWith('AUTH') || /^[A-Za-z0-9+/=]+$/.test(regel) ? '(inloggen)' : regel.split(' ')[0]}: ${a.tekst.slice(0, 200)}`);
    return a;
  };
  try {
    await new Promise((ok, fout) => { sock.once('secureConnect', ok); sock.once('error', fout); setTimeout(() => fout(new Error('SMTP: verbinden duurt te lang')), 15000); });
    const begin = await antwoord(); if (begin.code !== 220) throw new Error('SMTP begin: ' + begin.tekst);
    await opdracht(`EHLO ${naam}`, [250]);
    await opdracht('AUTH LOGIN', [334]);
    await opdracht(Buffer.from(user).toString('base64'), [334]);
    await opdracht(Buffer.from(pass.replace(/\s+/g, '')).toString('base64'), [235]);
  } catch (e) { sock.destroy(); throw e; }
  return {
    async stuur({ aan, data }) {
      await opdracht(`MAIL FROM:<${user}>`, [250]);
      await opdracht(`RCPT TO:<${aan}>`, [250, 251]);
      await opdracht('DATA', [354]);
      // Regels die met een punt beginnen krijgen een extra punt (SMTP-regel).
      await opdracht(data.replace(/\r?\n/g, '\r\n').replace(/^\./gm, '..') + '\r\n.', [250]);
    },
    async reset() { await opdracht('RSET', [250]); },
    async sluit() { try { await opdracht('QUIT', [221]); } catch {} sock.end(); },
  };
}

const b64regels = s => Buffer.from(s, 'utf8').toString('base64').replace(/.{76}/g, '$&\r\n');
const kop = s => /^[\x20-\x7e]*$/.test(s) ? s : `=?UTF-8?B?${Buffer.from(s, 'utf8').toString('base64')}?=`;

// Een complete mail (tekst + HTML) met afmeldkop, zodat Gmail en Outlook een afmeldknop tonen.
export function bericht({ van, vanNaam, antwoordAan, aan, onderwerp, tekst, html, afmelden }) {
  const grens = 'gb-' + crypto.randomBytes(8).toString('hex');
  const domein = van.split('@')[1] || 'localhost';
  const koppen = [
    `From: ${kop(vanNaam)} <${van}>`, `To: <${aan}>`, ...(antwoordAan ? [`Reply-To: <${antwoordAan}>`] : []),
    `Subject: ${kop(onderwerp)}`, `Date: ${new Date().toUTCString().replace('GMT', '+0000')}`,
    `Message-ID: <${crypto.randomUUID()}@${domein}>`, 'MIME-Version: 1.0',
    ...(afmelden ? [`List-Unsubscribe: <${afmelden}>`, 'List-Unsubscribe-Post: List-Unsubscribe=One-Click'] : []),
    `Content-Type: multipart/alternative; boundary="${grens}"`,
  ];
  const data = koppen.join('\r\n') + '\r\n\r\n' +
    `--${grens}\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n${b64regels(tekst)}\r\n` +
    `--${grens}\r\nContent-Type: text/html; charset=utf-8\r\nContent-Transfer-Encoding: base64\r\n\r\n${b64regels(html)}\r\n` +
    `--${grens}--`;
  return { aan, data };
}

// Opmaak van de mails, in de huisstijl van de site.
export const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
export function opmaak({ titel, inhoud, knop, knopUrl, voet }) {
  return `<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;background:#f4f7f1;font-family:Arial,Helvetica,sans-serif;color:#1e2a22">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f7f1"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:14px;border:1px solid #e1e7dc">
<tr><td style="background:#0e7c4a;color:#ffffff;padding:16px 20px;border-radius:14px 14px 0 0;font-size:18px;font-weight:bold">🛒 Goedkope Boodschappen</td></tr>
<tr><td style="padding:20px"><h1 style="margin:0 0 12px;font-size:22px;line-height:1.25">${esc(titel)}</h1>${inhoud}
${knop ? `<p style="margin:20px 0 4px"><a href="${esc(knopUrl)}" style="display:inline-block;background:#0e7c4a;color:#ffffff;text-decoration:none;font-weight:bold;padding:12px 18px;border-radius:10px">${esc(knop)}</a></p>` : ''}
</td></tr>
<tr><td style="padding:14px 20px;border-top:1px solid #e1e7dc;font-size:13px;color:#5d6a61;line-height:1.5">${voet}</td></tr>
</table></td></tr></table></body></html>`;
}
