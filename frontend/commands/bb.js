const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const axios = require('axios');

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:7860/process';

const PLATFORM_CHOICES = [
  { name: '🎵 YouTube', value: 'youtube' },
  { name: '🎶 TikTok', value: 'tiktok' },
  { name: '☁️  SoundCloud', value: 'soundcloud' },
  { name: '💚 Spotify', value: 'spotify' },
];

const PLATFORM_COLORS = {
  youtube: 0xFF0000,
  tiktok: 0x010101,
  soundcloud: 0xFF5500,
  spotify: 0x1DB954,
};

const PLATFORM_ICONS = {
  youtube: '🎥',
  tiktok: '🎵',
  soundcloud: '☁️',
  spotify: '💚',
};

function buildSuccessEmbed(title, platform, directLink, username) {
  const icon = PLATFORM_ICONS[platform] ?? '🎵';
  const color = PLATFORM_COLORS[platform] ?? 0x5865F2;
  const extractedHost = new URL(directLink).hostname;

  return new EmbedBuilder()
    .setColor(color)
    .setTitle(`${icon} ${title.slice(0, 250)}`)
    .setDescription(`\`${directLink}\``)
    .addFields(
      { name: '📦 Platform', value: platform.charAt(0).toUpperCase() + platform.slice(1), inline: true },
      { name: '🗂️ Format', value: 'MP3 (audio)', inline: true },
      { name: '☁️ Host', value: extractedHost, inline: true },
    )
    .setFooter({ text: `Diminta oleh ${username} • Powered by The Kims 1975` })
    .setTimestamp();
}

function buildErrorEmbed(message, username) {
  return new EmbedBuilder()
    .setColor(0xED4245)
    .setTitle('❌ Konversi Gagal')
    .setDescription(`**Error:**\n\`\`\`${message}\`\`\``)
    .setFooter({ text: `Diminta oleh ${username}` })
    .setTimestamp();
}

module.exports = {
  data: new SlashCommandBuilder()
    .setName('bb')
    .setDescription('🎵 Ubah link audio/video menjadi direct link MP3')
    .addStringOption(option =>
      option
        .setName('type')
        .setDescription('Platform sumber audio/video')
        .setRequired(true)
        .addChoices(...PLATFORM_CHOICES),
    )
    .addStringOption(option =>
      option
        .setName('url')
        .setDescription('URL audio/video yang ingin dikonversi')
        .setRequired(true),
    ),
  async execute(interaction, stats) {
    await interaction.deferReply();
    const platform = interaction.options.getString('type');
    const url = interaction.options.getString('url');
    const username = interaction.user.tag;
    
    console.log(`[CMD] /bb | channel=${interaction.channelId} | platform=${platform} | url=${url} | user=${username}`);

    try {
      const response = await axios.post(
        BACKEND_URL,
        { type: platform, url },
        {
          timeout: 120_000,
          headers: { 'Content-Type': 'application/json' },
        },
      );
      
      const data = response.data;
      if (data.status === 'success' && data.direct_link) {
        const title = data.title || 'Unknown Title';
        const httpLink = data.direct_link.replace(/^https:\/\//i, 'http://');
        await interaction.editReply({
          embeds: [buildSuccessEmbed(title, platform, httpLink, username)],
        });
        console.log(`[SUCCESS] direct_link=${httpLink}`);
        if (stats) stats.success++;
      } else {
        const msg = data.message || 'Unknown error dari backend.';
        await interaction.editReply({
          embeds: [buildErrorEmbed(msg, username)],
        });
        console.warn(`[WARN] Backend error: ${msg}`);
        if (stats) stats.fail++;
      }
    } catch (err) {
      if (stats) stats.fail++;
      console.error(`[ERROR] bb command:`, err);
      await interaction.editReply({ content: '❌ Terjadi kesalahan pada server.' }).catch(() => { });
    }
  }
};
