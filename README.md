# Xbox 360 Controller GUI TCP Sender

A visual GUI application for reading Xbox 360 controller input and transmitting it via TCP to remote devices. Based on the original `upper.py` script with enhanced functionality and user interface. Written by Claude Sonnet 4.

## Features

- **Visual Controller Input Display**: Real-time visualization of all controller inputs including:
  - Analog sticks (left/right with deadzone)
  - Triggers (LT/RT with pressure visualization)
  - All buttons (A, B, X, Y, LB, RB, etc.)
  - D-pad input
  
- **TCP Connection Management**: 
  - Configurable target IP and port
  - Connect/disconnect buttons
  - Connection status monitoring
  - Error handling and reporting

- **Configuration System**:
  - Default configuration file (`controller_config.json`)
  - Save/load configuration
  - Adjustable update rate and deadzone
  - Persistent settings

- **Status Monitoring**:
  - Real-time connection status
  - Packet transmission counter
  - Error logging with timestamps
  - Controller detection and information

## Requirements

- Python 3.7+
- pygame 2.5.2
- tkinter (usually included with Python)
- Xbox 360 or compatible controller

## Installation

### Option 1: Run from Source
1. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python joystick_gui.py
   ```

### Option 2: Build Executable

**For Conda Users (Recommended):**
1. Run the manual build script (handles pathlib conflicts):
   ```bash
   build_manual.bat
   ```

**For Standard Python Installations:**
1. Run the standard build script:
   ```bash
   build.bat
   ```
   
2. The executable will be created in the `dist` folder as `Xbox_Controller_GUI.exe`

**If you encounter pathlib conflicts:**
```bash
conda remove pathlib
pip install pyinstaller
pyinstaller --onefile --windowed joystick_gui.py
```

### Manual Build Process
If you prefer to build manually:
```bash
pip install -r requirements.txt
pip install pyinstaller
python setup.py
pyinstaller joystick_gui.spec
```

## Usage

### Starting the Application
1. Connect your Xbox 360 controller to your computer
2. Launch the application (either run the Python script or the executable)
3. The controller should be automatically detected

### Connecting to TCP Server
1. Enter the target IP address (default: 127.0.0.1)
2. Enter the target port (default: 5555)
3. Click "Connect" to establish connection
4. Controller data will automatically start transmitting

### Configuration
- **Update Rate**: How many times per second to send data (default: 20 Hz)
- **Deadzone**: Minimum analog stick movement to register (default: 0.1)
- **Save Config**: Save current settings to file
- **Load Config**: Load settings from file

### Visualization Tab
Switch to the "Visualization" tab to see real-time controller input:
- Red dot: Left analog stick position
- Blue dot: Right analog stick position
- Green bars: Trigger pressure (LT/RT)
- Yellow dot: D-pad position
- Button highlights: Show when buttons are pressed

## Configuration File

The application uses `controller_config.json` for default settings:

```json
{
  "tcp_ip": "127.0.0.1",
  "tcp_port": 5555,
  "update_rate": 20,
  "deadzone": 0.1
}
```

## Data Format

Controller data is sent as JSON over TCP with the following structure:

```json
{
  "left_stick_x": 0.0,
  "left_stick_y": 0.0,
  "right_stick_x": 0.0,
  "right_stick_y": 0.0,
  "left_trigger": -1.0,
  "right_trigger": -1.0,
  "dpad_x": 0,
  "dpad_y": 0,
  "a_button": 0,
  "b_button": 0,
  "x_button": 0,
  "y_button": 0,
  "lb_button": 0,
  "rb_button": 0,
  "back_button": 0,
  "start_button": 0,
  "xbox_button": 0,
  "left_stick_button": 0,
  "right_stick_button": 0,
  "buttons": {
    "button_0": 0,
    "button_1": 0,
    ...
  },
  "timestamp": 1623456789.123
}
```

### Value Ranges
- **Analog sticks**: -1.0 to 1.0 (with deadzone applied)
- **Triggers**: -1.0 (not pressed) to 1.0 (fully pressed)
- **D-pad**: -1, 0, or 1 for each axis
- **Buttons**: 0 (not pressed) or 1 (pressed)

## Troubleshooting

### Controller Not Detected
- Ensure controller is properly connected
- Try different USB ports
- Check Windows Game Controllers settings
- Click "Refresh" button in the application

### Connection Issues
- Verify target IP and port are correct
- Check if target server is running and listening
- Ensure firewall isn't blocking the connection
- Check the error log in the Status section

### Build Issues
- Ensure Python and pip are properly installed
- Run command prompt as administrator if needed
- Check that all dependencies are installed

## Files Structure

```
joystick_exec/
├── joystick_gui.py          # Main GUI application
├── upper.py                 # Original command-line version
├── controller_config.json   # Default configuration
├── requirements.txt         # Python dependencies
├── setup.py                 # Build setup script
├── build.bat               # Windows build script
├── README.md               # This file
└── dist/                   # Built executable (after build)
    └── Xbox_Controller_GUI.exe
```

## Compatibility

- **Operating System**: Windows (tested on Windows 11)
- **Controllers**: Xbox 360 wired/wireless, Xbox One controllers
- **Python**: 3.7+ (for source version)

## Based On

This project is based on and extends the functionality of `upper.py`, adding:
- Complete GUI interface
- Real-time visualization
- Enhanced configuration management
- Better error handling
- Executable packaging

## License

This project is provided as-is for educational and personal use.
