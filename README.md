# VEP MIDI AutoMate
Windows GUI to auto-populate MIDI Controller mappings in _Vienna Ensemble Pro 7_ from a CSV file. Windows-only (for now); macOS contributions welcome.

## Download the latest release
[VEP MIDI Automate 1.0.0](https://link.com/)

## Walkthrough video
to come

## Quick start
- Download _VEP MIDI AutoMate_ [here](https://link.com/).
- Open _Vienna Ensemble Pro 7_ (**on a screen with scaling set to 100%**) and load/start your project.
- Take the sample CSV, populate it with your desired MIDI controller mappings, and save.
- Run _VEP MIDI AutoMate_.
- Click "Browse..." and locate your CSV file.
- Click "Let’s AutoMate ▶" and watch your MIDI controller mapping populate.

## What _VEP MIDI AutoMate_ does
- Loads and reads a CSV of your desired MIDI controller mappings (see below for instructions on how this CSV should appear).
- Drives the UI of _Vienna Ensemble Pro 7_ via the mouse and keyboard to input these MIDI controller mappings reliably and quickly.

## How _VEP MIDI AutoMate_ works
- After loading your CSV file and checking for errors, _VEP MIDI AutoMate_ will locate your _Vienna Ensemble Pro 7_ window (either _Standalone_ or _Server_ works), maximise it, bring it to the front, verify the presence of an active instance, and set up the layout so that the _MIDI Controllers_ section is maximised. This ensures that all important buttons and rows are in calculable locations.
- Then, all current MIDI automation rows will be deleted.
- Next, _VEP MIDI AutoMate_ will investigate the left-side menu layout of _Vienna Ensemble Pro 7_ as it appears on your screen; counting and noting the on-screen positions of MIDI ports, devices and internal cables, and determining the relative positions of all sub-menu items. This will normally take about 5 seconds.
- Finally, for each row in your CSV, the following actions will take place.
  - A new row will be created, scrolling down if required.
  - The _DEVICE_ | _CHANNEL_ | _CONTROLLER_ | _CC_ menus will be progressed through with the mouse according to the numbers in your CSV for the columns _device_, _channel_ and _cc_. Note that only the device _number_ should be entered into the CSV, not the device name; the number will be used to inform the mouse as to where it should move by calculating the position of the device item in the first main menu. See the video walkthrough above for more details about this.
  - After the right-side column has been clicked on, the _DESTINATION_ will be populated by sequentially typing the contents stored in the _layer 1_, _layer 2_, _layer 3_, _layer 4_ columns of the CSV as required. More specifically:
    - The contents of _layer 1_ (the mixer channel name) will be entered into the search bar. This must appear in your CSV exactly as it will be written in the final destination, including the preceding mixer channel number, such as "1 Violin". Note, choosing a mixer channel name that is likely to collide with a plugin name or parameter may cause issues, as other items may appear in the filtered list. You can check this by ensuring that manually typing the contents of _layer 1_ into the destination searchbar filters out all entries apart from the mixer channel you are aiming for. If a problem is likely, consider temporarily renaming your mixer channel names while using _VEP MIDI AutoMate_. Please see the video walkthrough above for more information. Then, the keyboard will be pressed down once to select the mixer channel, and the destination input text will be deleted. This still preserves the selection of the mixer channel.
    - The above process is then repeated for _layer 2_, which will select the next layer of the destination, which will either be a mixer channel parameter (such as "Mute"), a VST (such as "Vienna Synchron Player") or the "FX" or "Send x" grouping.
    - If required, the above process is repeated for _layer 3_ and _layer 4_.
    - In cases where the final layer describes a parameter which appears more the once in the filtered, a number in the _repeat_ column of your CSV will indicate how many additional keyboard down presses are to occur. Please see the video walkthrough to understand why this might be needed.
- To halt _VEP MIDI AutoMate_, you can press Ctrl+F12 at any time. If you run into any serious problems, quickly move your mouse to the top-left of the screen to cause an error, and _VEP MIDI AutoMate_ will be forced to stop.
- _VEP MIDI AutoMate_ will display an update of progress and estimated time to finish.
- Checking "Slow mode" will inject a pause between all UI events. Use this if you want to watch more carefully how _VEP MIDI AutoMate_ works.
- "Light mode" and "Dark mode" is available, but make no difference to functionality.
- Upon close, your settings (CSV location, slow mode, light/dark mode) will be saved in C:\Users\your_name\AppData\Roaming\VEP MIDI AutoMate.

## Requirements
- Windows 10/11 (64-bit). I have tested _VEP MIDI AutoMate_ on three of my own Windows devices with no issues, but have not yet had it tested on devices and setups belonging to others. If you use _VEP MIDI AutoMate_ on your device, either successfully or unsuccessfully, please let me know so that I can note this or make any adjustments.
- _Vienna Ensemble Pro 7_ (standalone) or _Vienna Ensemble Pro 7 Server_ already open with your instance active. _VEP MIDI AutoMate_ serves no purpose for the non-pro _Vienna Ensemble 7_, which does not include the ability to set up MIDI controller mappings.
- _Vienna Ensemble Pro 7_ **must be on a screen with scaling set to 100%**, otherwise the pixel detection algorithms can get confused. On Windows 10/11, the screen scaling can be changed via Settings/System/Display/Scale.
- A CSV with column headings in row 1; "device", "channel", "cc", "layer 1", "layer 2", "layer 3", "layer 4", "repeat". The requirements for the values in the CSV are as follows:
  - Values in "device" must be from {1, 2, 3, …}.
  - Values in "channel" must be from {1, 2, 3, …, 16}.
  - Values in "cc" must be from {0, 1, 2, …, 127}.
  - Values in "layer 1" must be the destination mixer channel name, including the preceding mixer channel number, such as "1 Violin", "2 Flute", "3 Final Mix", etc.
  - Values in "layer 2", "layer 3" and "layer 4" must be the exact text of the parameters/plugins/groups at their respective layer of the destination, with "layer 3" and/or "layer 4" to be left blank if not required.
  - Values in "repeat" must be left blank if not required, or from {1, 2, 3, …} if required.
  - Note that a sample CSV has been provided that you may edit for your needs.

## Troubleshooting
- If something goes wrong and _VEP MIDI AutoMate_ times out while inputting your MIDI controller mappings (usually after 10 seconds), the most likely issue is that the destination items in your CSV (_layer 1_, _layer 2_, _layer 3_, _layer 4_) are not spelt the same as they appear in _Vienna Ensemble Pro 7_. Misspelling will mean that _VEP MIDI AutoMate_ cannot find the destination for the MIDI controller mapping, and so will get confused.
- If you still run into a problem, please contact me. I have only tested  _VEP MIDI AutoMate_ on my own devices.

## Known limitations
- Windows only (PyAutoGUI/PyWin specifics); macOS ports welcome.
- Requires 100% screen scaling.
- UI changes in future releases of _Vienna Ensemble Pro 7_ may require updates.

## Roadmap
- macOS support.

## Contributing
- Issues and pull requests welcome.
- If you are attempting a macOS port, please open an issue to coordinate the approach.

## Privacy and safety
- _VEP MIDI AutoMate_ does not use the network or upload files.
- _VEP MIDI AutoMate_ programmatically controls your mouse and keyboard; don't use your device while it runs.

## License
Copyright © Robert Russell.
Licensed under Apache-2.0. See [LICENSE](https://link.com/).
