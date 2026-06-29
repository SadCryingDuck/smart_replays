<div align="center">
<h1 style="text-align: center; font-size: 50px">Smart Replays</h1>
</div>

Smart Replays is an OBS script whose main purpose is to save clips with different names and to separate folders depending on the application being recorded (imitating NVIDIA Shadow Play functionality).
This script also has additional functionality, such as sound and pop-up notifications, auto-restart of the replay buffer, etc.

> [!NOTE]
> This is a modified fork of [qvvonk/smart_replays](https://github.com/qvvonk/smart_replays), maintained by SadCryingDuck.
> See the commit history and [releases](https://github.com/SadCryingDuck/smart_replays/releases) for the changes and their dates.

![overview](https://github.com/user-attachments/assets/82c8e163-ae2a-4ace-90ca-f4c052aa67e3)

<div align="center">
<p style="text-align: center; font-size: 30px"><b>⭐ Like this script? ⭐</b></p>
<p style="text-align: center; font-size: 20px"><b>😎Consider giving the repository a star 😎</b></p>
</div>


> [!WARNING]  
> This script is designed for Windows OS only


# Table of content
* [⭐ Features](#features)
* [⚙️ Requirements](#requirements)
* [🔷 More about this script](#more-about-script)


# Features

* [Automatic clip name changing and saving in to separate folder depending on](#clip-naming-and-saving)
    - the name of an active app (.exe file name) at the moment of clip saving
    - the name of an app (.exe file name) that was active most of the time during the clip recording
    - the name of the current scene
* [Ability to set hotkeys for each of the modes above](#hotkeys)
* [Ability to set clip file name template](#clip-filename-template)
* [Ability to set custom clip names for individual applications/folders](#custom-names)
* [Sound notifications with the ability to set your own sound](#sound-notifications)
* [Pop-up NVIDIA-like notifications](#pop-up-notifications)
* [Cyclic restart of replay buffer](#cyclic-buffer-restarting)
* [Automatic restarting the replay buffer after clip saving](#restarting-the-replay-buffer-after-saving-a-clip)


# Requirements
OS: Windows 10 or higher
Python 3.10 or higher
The script does not require any third-party libraries, however, Python must be installed together with `Tkinter`.

![python_installing](https://github.com/user-attachments/assets/1d798ed9-2284-4759-9180-e7486012e1e7)

<hr />

# More about script
## Clip naming and saving
The main purpose of the script is to automatically change clip names depending on the recorded window, as well as to sort clips into folders.

![different_folders](https://github.com/user-attachments/assets/b5db2e73-d717-4379-87d5-c1ca0ee83587)
![names](https://github.com/user-attachments/assets/355a0772-bdd0-42ac-975f-95d252dafa0c)

There are 3 modes of clip title naming:
* by the name of an active app (.exe file name) at the moment of clip saving
* by the name of an app (.exe file name) that was active most of the time during the clip recording
* by the name of the current OBS scene

![different_modes](https://github.com/user-attachments/assets/b0755804-ccdf-424b-99b7-991d82364b3f)

## Hotkeys
You can register any hotkeys for any of the modes.
Pressing the hotkeys will save the clip in the corresponding mode without changing the mode globally.

![hotkeys](https://github.com/user-attachments/assets/0eee6b68-f1c3-4fd8-8acd-19ec5b5b7c48)


## Clip filename template
You can set a template for the clip file name by using variables with the clip name and save time.
You can read more about variables and their values in the template input field hint or at the [link](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes).


## Custom names
Sometimes the names of the executable files may not match the names of the applications (for example, a clip that recorded the desktop will be saved with the name `explorer` because the desktop executable is called `explorer.exe`)

Or you may not be happy with the current name of the executable and want to replace it with your own.

In this case, you can set up custom names for the applications or folders where the applications are located.

To do this, add an entry of the following format to the list
```
C:\path\to\executable\or\folder > CustomName
```

For example:
```
C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe > Browser
C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe > Browser
C:\Program Files (x86)\Steam\steamapps > SteamGames
C:\Program Files (x86)\Steam\steamapps\common\Deadlock > DeadLock
```
Following on from the example above, if you record _Microsoft Edge_ or _Brave Browser_, the clip name and save folder will be `Browser`.

If you record any games that are in the _Steam_ folder, the clip will be saved in the `SteamGames` folder
However, if you record _Deadlock_ game (more precisely, the application located in the `C:\Program Files (x86)\Steam\steamapps\common\Deadlock folder`), the clip will be saved in the `SteamGames` folder. 

The script provides the ability to import and export a list of custom names.

![custom_names_list](https://github.com/user-attachments/assets/03879677-4e50-4d44-a680-0c7448c05c12)


## Sound notifications
You can set custom `.wav` sounds on successful and unsuccessful clip saves.

![sound_notifications](https://github.com/user-attachments/assets/d6fdb925-58ab-4453-9c80-9b30957d7e79)


## Pop-up notifications
You can enable pop-up notifications, which are the same as Nvidia Shadow Play (or not ._.)

![popup_success](https://github.com/user-attachments/assets/0a4cc1bb-4780-4c86-918a-efeaf2b023f5)

![popup_failure](https://github.com/user-attachments/assets/7a774432-ac16-4ee8-bfd9-9f402675168a)


## Cyclic buffer restarting
Long running of the replay buffer in OBS may cause unpleasant consequences, such as long clip saving, OBS interface freezing, etc.

If you face similar problems, you can enable cyclic restart of the replay buffer. 

Note that this mode “looks” at the time of the last mouse or keyboard input. If no input is made within the time specified in the OBS Replay Buffer settings (`Settings` -> `Output` -> `Maximum Replay Time`), the script will automatically restart the replay buffer. In the opposite case the restart will be delayed for the maximum replay time.


## Restarting the replay buffer after saving a clip
OBS doesn't know the time the clip was saved. This means that after saving OBS continues recording without clearing the buffer, which may be inconvenient for some people.

For example, the clip length you have set is 60 seconds. You recorded for 60 seconds and saved the clip: the first clip will be 60 seconds long.
After 20 seconds, you save the clip again. Logically, the second clip should be 20 seconds long, but no, it will also be 60 seconds long, capturing the last 40 seconds of the first clip.
This script function helps to solve this problem.


<div align="center">
<p style="text-align: center; font-size: 30px"><b>⭐ Like this script? ⭐</b></p>
<p style="text-align: center; font-size: 20px"><b>😎Consider giving the repository a star 😎</b></p>
</div>