const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');
const os = require('os');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('server')
    .setDescription('Cek status server'),
  async execute(interaction) {
    const totalMem = (os.totalmem() / 1024 / 1024 / 1024).toFixed(2);
    const freeMem = (os.freemem() / 1024 / 1024 / 1024).toFixed(2);
    const usedMem = (totalMem - freeMem).toFixed(2);
    const cpu = os.loadavg()[0].toFixed(2);

    const serverEmbed = new EmbedBuilder()
      .setColor(0x5865F2)
      .setTitle('🖥️ Status Server')
      .addFields(
        { name: 'Ping', value: `${interaction.client.ws.ping} ms`, inline: true },
        { name: 'CPU Load', value: `${cpu}`, inline: true },
        { name: 'RAM Usage', value: `${usedMem} GB / ${totalMem} GB`, inline: true },
        { name: 'Owner', value: 'The Kims 1975', inline: true },
        { name: 'Waktu Server', value: new Date().toLocaleString('id-ID'), inline: true }
      )
      .setTimestamp();
    return interaction.reply({ embeds: [serverEmbed] });
  }
};
