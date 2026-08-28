/**
 * ============================================================
 *  Discord Bot – Dynamic Command Handler
 *  Stack : Node.js + discord.js v14 + axios
 *  Comm. : HTTP POST  →  Python FastAPI  (http://127.0.0.1:8000)
 * ============================================================
 */

'use strict';

const fs = require('fs');
const path = require('path');
const {
  Client,
  Collection,
  GatewayIntentBits,
  REST,
  Routes,
  ActivityType,
} = require('discord.js');
const os = require('os');
const { execSync } = require('child_process');
require('dotenv').config();

const botVersion = "1.0.0";
let stats = { success: 0, fail: 0 };

// ─── Custom Logger (To preserve logs in Dashboard) ──────────────────────────
const recentLogs = [];
function addLog(type, msg) {
  const time = new Date().toLocaleTimeString();
  recentLogs.push(`[${time}] ${type} ${msg}`);
  if (recentLogs.length > 10) recentLogs.shift();
}
const origLog = console.log;
const origWarn = console.warn;
const origError = console.error;
console.log = (...args) => { origLog(...args); addLog('INFO', args.join(' ')); };
console.warn = (...args) => { origWarn(...args); addLog('WARN', args.join(' ')); };
console.error = (...args) => { origError(...args); addLog('ERR ', args.join(' ')); };

// ─── Env Validation ────────────────────────────────────────────────────────────
const { BOT_TOKEN } = process.env;
if (!BOT_TOKEN) {
  console.error('[FATAL] Missing BOT_TOKEN in .env file.');
  process.exit(1);
}

// ─── Constants ─────────────────────────────────────────────────────────────────
const RATE_LIMIT_MAX = 5;          // max executions per window
const RATE_LIMIT_WINDOW = 35_000;    // 35 seconds in ms

// ─── Rate Limiter (per Channel ID) ─────────────────────────────────────────────
const channelRateMap = new Map();

function checkRateLimit(channelId) {
  const now = Date.now();
  let entry = channelRateMap.get(channelId);

  if (!entry || now >= entry.resetAt) {
    entry = { count: 0, resetAt: now + RATE_LIMIT_WINDOW };
    channelRateMap.set(channelId, entry);
  }

  if (entry.count >= RATE_LIMIT_MAX) {
    const retryAfterSec = Math.ceil((entry.resetAt - now) / 1000);
    return { allowed: false, retryAfterSec };
  }

  entry.count += 1;
  return { allowed: true };
}

// ─── Discord Client ─────────────────────────────────────────────────────────────
const client = new Client({
  intents: [GatewayIntentBits.Guilds],
});

client.commands = new Collection();
const localCommands = [];

// ─── Command Loading ────────────────────────────────────────────────────────────
const commandsPath = path.join(__dirname, 'commands');
const commandFiles = fs.readdirSync(commandsPath).filter(file => file.endsWith('.js'));

for (const file of commandFiles) {
  const filePath = path.join(commandsPath, file);
  const command = require(filePath);
  if ('data' in command && 'execute' in command) {
    client.commands.set(command.data.name, command);
    localCommands.push(command.data.toJSON());
  } else {
    console.warn(`[WARNING] Command at ${filePath} is missing 'data' or 'execute' property.`);
  }
}

// ─── Interaction Handler ────────────────────────────────────────────────────────
client.on('interactionCreate', async interaction => {
  if (!interaction.isChatInputCommand()) return;

  const command = client.commands.get(interaction.commandName);
  if (!command) return;

  // Rate Limiting is only for specific expensive commands like bb and search
  if (['bb', 'search'].includes(interaction.commandName)) {
    const { allowed, retryAfterSec } = checkRateLimit(interaction.channelId);
    if (!allowed) {
      const { EmbedBuilder } = require('discord.js');
      const limitEmbed = new EmbedBuilder()
        .setColor(0xFEE75C)
        .setTitle('⏱️ Rate Limit Channel')
        .setDescription(`Channel ini telah mencapai batas **${RATE_LIMIT_MAX} eksekusi / 35 detik**.\nSilakan coba lagi dalam **${retryAfterSec} detik**.`)
        .setFooter({ text: 'Cooldown dihitung per channel, bukan per user.' })
        .setTimestamp();
      return interaction.reply({ embeds: [limitEmbed], ephemeral: true });
    }
  }

  try {
    await command.execute(interaction, stats);
  } catch (error) {
    console.error(`[ERROR] Executing command ${interaction.commandName}:`, error);
    if (interaction.replied || interaction.deferred) {
      await interaction.followUp({ content: '❌ Terjadi kesalahan saat mengeksekusi command ini!', ephemeral: true }).catch(()=>{});
    } else {
      await interaction.reply({ content: '❌ Terjadi kesalahan saat mengeksekusi command ini!', ephemeral: true }).catch(()=>{});
    }
  }
});

// ─── Ready Event ────────────────────────────────────────────────────────────────
client.once('ready', async () => {
  console.log(`\n[BOT] Logged in as ${client.user.tag}`);
  console.log(`[BOT] Serving ${client.guilds.cache.size} guild(s).`);
  client.user.setActivity('/bb | /search', { type: ActivityType.Listening });

  try {
    const fetchedCommands = await client.application.commands.fetch();
    let needsUpdate = false;
    
    if (fetchedCommands.size !== localCommands.length) {
      needsUpdate = true;
    } else {
      const fetchedNames = Array.from(fetchedCommands.values()).map(cmd => cmd.name);
      for (const localCmd of localCommands) {
        if (!fetchedNames.includes(localCmd.name)) {
          needsUpdate = true;
          break;
        }
      }
    }

    if (needsUpdate) {
      const rest = new REST({ version: '10' }).setToken(process.env.DISCORD_TOKEN || BOT_TOKEN);
      await rest.put(Routes.applicationCommands(client.user.id), { body: localCommands });
      console.log('[Auto-Register] Mendeteksi command baru. Registrasi berhasil!');
    } else {
      console.log('[Auto-Register] Command up-to-date. Melewati registrasi.');
    }
  } catch (err) {
    console.error('[ERROR] Gagal melakukan auto-register slash commands:', err.message);
  }

  // ─── Live Dashboard Terminal ────────────────────────────────────────────────────
  setInterval(() => {
    let pyVer = "Unknown";
    try { pyVer = execSync('python --version', { stdio: 'pipe' }).toString().trim(); } catch (e) { }
    const totalMem = (os.totalmem() / 1024 / 1024 / 1024).toFixed(2);
    const freeMem = (os.freemem() / 1024 / 1024 / 1024).toFixed(2);
    const usedMem = (totalMem - freeMem).toFixed(2);
    const cpu = os.loadavg()[0].toFixed(2);

    console.clear();
    origLog(`╔════════════════════════════════════════════════════════════╗`);
    origLog(`║                  BOTJS LIVE DASHBOARD                      ║`);
    origLog(`╠════════════════════════════════════════════════════════════╣`);
    origLog(`║ 🤖 Bot Version : v${botVersion.padEnd(41)}║`);
    origLog(`║ 🟢 Node.js     : ${process.version.padEnd(41)}║`);
    origLog(`║ 🐍 Python      : ${pyVer.padEnd(41)}║`);
    origLog(`╠════════════════════════════════════════════════════════════╣`);
    origLog(`║ 💻 CPU Load    : ${cpu.toString().padEnd(41)}║`);
    origLog(`║ 🧠 RAM Usage   : ${(usedMem + ' / ' + totalMem + ' GB').padEnd(41)}║`);
    origLog(`║ 🌐 WS Ping     : ${(client.ws.ping + ' ms').padEnd(41)}║`);
    origLog(`╠════════════════════════════════════════════════════════════╣`);
    origLog(`║ 📈 Traffic     : ✅ Sukses: ${stats.success} | ❌ Gagal: ${stats.fail}`.padEnd(61) + '║');
    origLog(`╚════════════════════════════════════════════════════════════╝`);
    origLog(`\n[Recent Logs]`);
    recentLogs.forEach(l => origLog(l));
  }, 3000);
});

// ─── Graceful Shutdown ──────────────────────────────────────────────────────────
process.on('SIGINT', () => {
  console.log('\n[BOT] Shutting down gracefully...');
  client.destroy();
  process.exit(0);
});

// ─── Bootstrap ─────────────────────────────────────────────────────────────────
(async () => {
  await client.login(BOT_TOKEN);
})();

// ─── Global Error Handler ──────────────────────────────────────────────────────
process.on('unhandledRejection', error => {
  console.error('[Anti-Crash] Unhandled promise rejection:', error);
});
