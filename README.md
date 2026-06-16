# Mumo Weather Forecast Module

A lightweight, dependency-free weather lookup module for the **Mumo** ([Mumble Monitor](https://github.com/mumble-voip/mumo)) framework. It provides real-time ambient conditions alongside a contextual 2-period localized weather forecast directly within Mumble server text channels via the `!weather` command.

## Features

*   **Dual API Integration**: Leverages `zippopotam.us` for lightning-fast ZIP-to-GPS translations, and pulls verified meteorological arrays directly from the official United States National Weather Service (`weather.gov`).
*   **Real-Time Ambient Data**: Resolves closest local hardware automated weather stations dynamically to inject real-time observation temperatures and descriptions into the header stream.
*   **Smart Emoji Mapping**: Automatically parses forecasting string matrices to correspond contextual emojis (`☀️`, `⛅`, `🌧️`, `⛈️`, `❄️`, `💨`) matching localized atmospheric criteria.
*   **HTML Structure Layout**: Formats responses automatically to print clean, high-visibility, scannable summaries inside the Mumble side-chat window console.

---

## Output Display Example

When a user triggers the script console interface inside a text window channel:

```text
To Channel: !weather 90210
Server: 🌤️ Weather Forecast for Beverly Hills, CA (90210) — Currently: 74°F, Partly Cloudy ⛅

Tonight: 59°F | Wind: 0 to 5 mph SSE ⛅
Mostly cloudy, with a low around 59. South southeast wind 0 to 5 mph.

Tuesday: 76°F | Wind: 0 to 10 mph S ☀️
Mostly sunny, with a high near 76. South wind 0 to 10 mph.
```

🛠️ Installation
1. Save the Module

Copy weather.py into your primary Mumo modules/ directory.
2. Enable the Module

Depending on how your Mumo environment is configured, choose one of the methods below:
Method A: If your setup uses a single mumo.ini file

Open your mumo.ini file and add weather to your active modules list, then append the configuration at the bottom:

[modules]
weather =

[weather]
enabled = true

Method B: If your setup uses a modules-enabled/ directory

Create a new file called weather.ini inside your modules-enabled/ folder:

[weather]
enabled = true

3. Restart Mumo

Restart your Mumo bot framework instance to load the new extension.
⚙️ Compatibility

    Works natively with Mumble 1.4.x / 1.5.x+ server deployments.
    Written using the standardized mumo_module namespace layer. Mumo Required:
    https://github.com/mumble-voip/mumo

📄 License

This project is open-source and available under the terms of the MIT License.
