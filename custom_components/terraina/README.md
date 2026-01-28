# TERRAINA Integration Guide

Version: 1.0.0

## Overview

- Control TERRAINA robot mowers from Home Assistant, with a focus on the "Back to dock" command.
- Supports multiple countries with dedicated OAuth/token endpoints.
- Uses Home Assistant Config Flow with OAuth2 authentication.

## Installation

### Method 1: HACS (Recommended)
  - Make sure HACS is installed.
  - Go to HACS → Integrations → Three dots menu (⋮) → Custom repositories
  - Add https://github.com/DCK-China/home-assistant-terraina as repository URL with category "Integration"
  - Go to HACS → Integrations → + → Search for "TERRAINA"
  - Install and restart Home Assistant
### Method 2: Manual Installation
  - Copy the `custom_components/terraina` folder into the `/config/custom_components` directory.

  - **If Home Assistant is running in a container, copy the `terraina` directory to the corresponding `custom_components` directory in the data volume.**
  - Restart Home Assistant.

## Configuration Steps

1. After installation, navigate to Home Assistant UI: **Settings → Devices & Services → Add Integration** → search for **TERRAINA**.

2. Select your country and complete the OAuth login process.

3. Upon successful authentication, entities and services will be created automatically.

   All devices already bound in your TERRAINA app will be registered as entities and displayed on the home page.

## Features

### Sync Devices with Your TERRAINA App
- The TERRAINA Integration automatically syncs devices with your TERRAINA app. When new devices are bound in the app, they will be registered in the TERRAINA integration. The same applies when unbinding devices.

### Back to Dock Service

- A dedicated service is registered for each mower: `terraina.back_<serial_slug>`.
- Can be called via **Developer Tools → Services**, automations, or scripts.

**Example automation / 自动化示例：**

```yaml
automation:
  - alias: "Mower back to dock at 18:00"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: terraina.back_abc123456
```

### Entities

- Each mower has a sensor showing its binding state: `sensor.<name>_(<serial>)_binding`.

## Troubleshooting

- The TERRAINA Integration depends on My Home Assistant. Please verify that the address linked at `https://my.home-assistant.io` is reachable from your Home Assistant instance.
- Service not found: confirm integration loaded and serial slug matches service name.
- No response to back command: ensure mower online and network reachable; check HA logs.
- Some trouble not listed: please contact us.

## Logging

Enable debug logs when needed:

```yaml
logger:
  default: info
  logs:
    homeassistant.components.terraina: debug
```

## Maintainer

- Codeowner: @DCK-China

---
