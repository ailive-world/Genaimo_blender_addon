# Genaimo Addon for Blender
A Blender addon that converts text descriptions to 3D character animations using the Genaimo AI API.
## Features
- **Text to Motion**: Generate character animations from text descriptions
- **Motion Stylization**: Apply various styles to existing animations (Kawai, Elegant, Robot-like, etc.)
- **Batch Generation**: Generate multiple motion variations at once
- **Motion Management**: Organize, preview, and manage generated animations
## Requirements
- Blender 4.2+
- Internet connection
-Genaimo account
- Genaimo API key and secret
## Installation
1. Download the latest release from [Releases](https://github.com/ailive-world/Genaimo_blender_addon/releases/)
2. In Blender, go to Edit → Preferences → Add-ons
3. Click "Install..." and select the downloaded zip file
4. Enable the "Genaimo Blender tools" addon
## Quick Start
1. **Get API Access**: Visit [Genaimo](https://genaimo.ailive.world/) to get your API key and secret
2. **Configure API**: In Blender, go to the 3D Viewport sidebar → Genaimo tab
3. **Enter Credentials**: Input your API key and secret, then click "Save API Key"
4. **Generate Motion**:
   - Enter a text description (e.g., "a person walks forward")
   - Click "Generate" to create 4 motion variations
   - Select and apply motions from the Motion List panel
## Usage
### Text to Motion
- Enter descriptive text in the Text to Motion panel
- Adjust frame count and start frame as needed
- Click Generate to create motion variations
### Motion Stylization
- Select an existing motion from the Motion List
- Choose a style from the Stylize panel
- Click "Generate Stylized" to apply the style
### Motion Management
- View all generated motions in the Motion List panel
- Click motion numbers to select and apply
- Delete individual motions or entire batches
- Use pagination to navigate through large motion libraries
## API Configuration
The addon requires a Genaimo API key and secret key:
1. Visit the [Genaimo](https://genaimo.ailive.world/)
2. Sign up for an account
3. Go to [Account management](https://genaimo.ailive.world/mypage)
3. Generate API key and secret key
4. Enter them in the Blender addon settings
## License
This project is licensed under the GNU General Public License v3.0 or later - see the [LICENSE](LICENSE) file for details.
## Support
- Documentation: [Genaimo Docs](https://docs.ailive.world/docs/intro)
- Issues: Please send an email to team@ailive.world
- Website: [Genaimo](https://genaimo.ailive.world)
- Discord: [Discord](https://discord.com/invite/8Yj4pMYsJN)
## Environments
Tested in Blender 4.2.1 LTS
