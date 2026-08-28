const { SlashCommandBuilder, EmbedBuilder } = require('discord.js');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('help')
    .setDescription('Menampilkan panduan bot'),
  async execute(interaction) {
    const helpEmbed = new EmbedBuilder()
      .setColor(0x5865F2)
      .setTitle('📖 Panduan Penggunaan Bot')
      .setDescription('Berikut adalah daftar command yang tersedia:')
      .addFields(
        { name: '/bb', value: 'Ubah link audio/video menjadi direct link MP3' },
        { name: '/search', value: 'Cari dan download lagu berdasarkan judul' },
        { name: '/help', value: 'Menampilkan panduan bot' },
        { name: '/server', value: 'Cek status server' }
      )
      .setTimestamp();
    return interaction.reply({ embeds: [helpEmbed] });
  }
};
