## Tenda AC6 Router Device Tracker

Adds device tracking support for [Tenda AC6](https://www.tendacn.com/product/AC6.html) to [Home Assistant](https://www.home-assistant.io/).
Based on:  sakowicz/home-assistant-tenda-tracker
(Currently archived so unable to add it to hacs)
## Setup Process

1. Install using [HACS](https://github.com/hacs/integration) or manually copy the files
2. Restart Home Assistant
3. Add and configure integration

## Step 1: Installation

### Installation with Home Assistant Community Store (HACS)

For easy updates whenever a new version is released, use the [Home Assistant Community Store (HACS)](https://github.com/hacs/integration) and add the following Integration in the Settings tab:

```
Cygansky/home-assistant-tenda-tracker
```
## Step 2: Restart and Test

You should see new devices in your entities. Their names will appear as you configured them before in Tenda admin panel or as their hostname or mac address. You can manipulate them in `known_devices.yaml`.

## Step 3: Add and configure integration

From UI

### Disclamer

I am not a python developer so code can be not as clean as I would want to. Feel free to contribute and do refactor!

