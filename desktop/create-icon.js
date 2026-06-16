const sharp = require('sharp');
const pngToIco = require('png-to-ico');
const fs = require('fs');
const path = require('path');

// Create a simple notification bell icon
async function createIcon() {
  console.log('Creating icon...');

  // Create a 256x256 PNG with a notification bell
  const svgIcon = `
  <svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
    <!-- Background circle -->
    <circle cx="128" cy="128" r="120" fill="#0a0e27" stroke="#00ffa3" stroke-width="4"/>

    <!-- Bell icon -->
    <g transform="translate(128, 128)">
      <!-- Bell body -->
      <ellipse cx="0" cy="-20" rx="35" ry="45" fill="#00ffa3"/>

      <!-- Bell top -->
      <circle cx="0" cy="-65" r="10" fill="#00ffa3"/>

      <!-- Bell bottom (ring) -->
      <ellipse cx="0" cy="25" rx="40" ry="8" fill="#00ffa3"/>

      <!-- Bell clapper -->
      <circle cx="0" cy="40" r="8" fill="#00ffa3"/>

      <!-- Notification dot -->
      <circle cx="20" cy="-80" r="15" fill="#00c8ff"/>
    </g>

    <!-- "A" letter for Agent -->
    <text x="128" y="200" font-family="Arial, sans-serif" font-size="40" font-weight="bold"
          fill="#00c8ff" text-anchor="middle">A</text>
  </svg>
  `;

  // Convert SVG to PNG
  const pngBuffer = await sharp(Buffer.from(svgIcon))
    .resize(256, 256)
    .png()
    .toBuffer();

  // Save PNG
  fs.writeFileSync(path.join(__dirname, 'icon.png'), pngBuffer);
  console.log('✅ PNG created: icon.png');

  // Convert PNG to ICO
  const icoBuffer = await pngToIco.default(pngBuffer);
  fs.writeFileSync(path.join(__dirname, 'icon.ico'), icoBuffer);
  console.log('✅ ICO created: icon.ico');
}

createIcon().catch(console.error);