const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const axios = require('axios');

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:7860/process';

function buildSuccessEmbed(title, directLink, username) {
  const extractedHost = new URL(directLink).hostname;
  return new EmbedBuilder()
    .setColor(0x5865F2)
    .setTitle(`🔍 ${title.slice(0, 250)}`)
    .setDescription(`\`${directLink}\``)
    .addFields(
      { name: '📦 Platform', value: 'Search', inline: true },
      { name: '🗂️ Format', value: 'MP3 (audio)', inline: true },
      { name: '☁️ Host', value: extractedHost, inline: true },
    )
    .setFooter({ text: `Diminta oleh ${username} • Powered by The Kims 1975` })
    .setTimestamp();
}

function buildErrorEmbed(message, username) {
  return new EmbedBuilder()
    .setColor(0xED4245)
    .setTitle('❌ Pencarian Gagal')
    .setDescription(`**Error:**\n\`\`\`${message}\`\`\``)
    .setFooter({ text: `Diminta oleh ${username}` })
    .setTimestamp();
}

module.exports = {
  data: new SlashCommandBuilder()
    .setName('search')
    .setDescription('Cari dan download lagu berdasarkan judul')
    .addStringOption(option =>
      option
        .setName('query')
        .setDescription('Judul lagu yang ingin dicari')
        .setRequired(true),
    ),
  async execute(interaction, stats) {
    await interaction.deferReply();
    const query = interaction.options.getString('query');
    const username = interaction.user.tag;
    
    console.log(`[CMD] /search | channel=${interaction.channelId} | query=${query} | user=${username}`);

    try {
      const response = await axios.post(
        BACKEND_URL,
        { type: 'search', url: query },
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
          embeds: [buildSuccessEmbed(title, httpLink, username)],
        });
        console.log(`[SUCCESS] search direct_link=${httpLink}`);
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
      console.error(`[ERROR] search command:`, err);
      await interaction.editReply({ content: '❌ Terjadi kesalahan pada server.' }).catch(() => { });
    }
  }
};
