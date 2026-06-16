#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2026 KizCo (https://github.com/KizCo)
# Licensed under the 3-Clause BSD License.

import re
import json
import urllib.request
import urllib.error
from mumo_module import MumoModule


class weather(MumoModule):
    default_config = {'weather': ()}

    def __init__(self, name, manager, configuration=None):
        MumoModule.__init__(self, name, manager, configuration)
        self.murmur = manager.getMurmurModule()
        self.keyword = "!weather"
        
        # Weather.gov strictly requires an explicit administrative contact string.
        self.headers = {
            'User-Agent': 'MumbleWeatherBot/1.1 (admin@yourdomain.com)',
            'Accept': 'application/geo+json'
        }

    def connected(self):
        manager = self.manager()
        self.log().debug("Registering Weather.gov forecast module")
        manager.subscribeServerCallbacks(self, manager.SERVERS_ALL)

    def disconnected(self):
        pass

    def sendMessage(self, server, user, message, msg):
        if message.channels:
            server.sendMessageChannel(user.channel, False, msg)
        else:
            server.sendMessage(user.session, msg)

    def _get_weather_emoji(self, description):
        """Matches weather descriptions to the most accurate emoji helper."""
        desc = description.lower() if description else ""
        if "thunder" in desc or "storm" in desc:
            return "⛈️"
        elif "snow" in desc or "blizzard" in desc or "ice" in desc or "freezing" in desc:
            return "❄️"
        elif "rain" in desc or "shower" in desc or "drizzle" in desc:
            return "🌧️"
        elif "fog" in desc or "mist" in desc or "haze" in desc:
            return "🌫️"
        elif "wind" in desc or "breezy" in desc or "gale" in desc:
            return "💨"
        elif "partly" in desc or "scattered" in desc or "mostly cloudy" in desc:
            return "⛅"
        elif "cloud" in desc or "overcast" in desc:
            return "☁️"
        elif "sunny" in desc or "clear" in desc:
            return "☀️"
        return "🌤️"

    def _geocode_zip(self, zipcode):
        """Converts a 5-digit US ZIP code into latitude and longitude."""
        url = f"https://api.zippopotam.us/us/{zipcode}"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not data.get('places'):
                    return None
                place = data['places'][0]
                return {
                    'lat': place['latitude'],
                    'lon': place['longitude'],
                    'city': place['place name'],
                    'state': place['state abbreviation']
                }
        except Exception:
            return None

    def userTextMessage(self, server, user, message, current=None):
        clean_text = re.sub(r'<[^>]*>', ' ', message.text).strip()

        if not clean_text.lower().startswith(self.keyword):
            return

        args = clean_text.split()
        if len(args) < 2 or not re.match(r'^\d{5}$', args[1]):
            self.sendMessage(server, user, message, "⚠️ <b>Usage:</b> <code>!weather [5-digit-zipcode]</code>")
            return

        zipcode = args[1]
        
        # 1. Translate zip to coordinates
        geo = self._geocode_zip(zipcode)
        if not geo:
            self.sendMessage(server, user, message, f"❌ <b>Error:</b> Could not find coordinates for ZIP code {zipcode}.")
            return

        # 2. Look up the Weather.gov metadata points to find the grid and nearest station
        points_url = f"https://api.weather.gov/points/{geo['lat']},{geo['lon']}"
        req_points = urllib.request.Request(points_url, headers=self.headers)
        
        try:
            with urllib.request.urlopen(req_points, timeout=5) as response:
                metadata = json.loads(response.read().decode('utf-8'))
                # Access variables inside the standard properties nesting layer
                props = metadata.get('properties', {})
                forecast_url = props.get('forecast')
                observation_stations_url = props.get('observationStations')
                
            if not forecast_url or not observation_stations_url:
                self.sendMessage(server, user, message, "❌ <b>Error:</b> Unable to route NWS endpoints.")
                return

            # 3. Hardened real-time observation parser
            current_condition = ""
            req_stations = urllib.request.Request(observation_stations_url, headers=self.headers)
            try:
                with urllib.request.urlopen(req_stations, timeout=5) as response:
                    stations_data = json.loads(response.read().decode('utf-8'))
                    stations = stations_data.get('features', [])
                    
                    if stations:
                        # Grab the first functional reporting observation station identifier loop
                        station_id = stations[0]['properties']['stationIdentifier']
                        latest_obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
                        
                        req_obs = urllib.request.Request(latest_obs_url, headers=self.headers)
                        with urllib.request.urlopen(req_obs, timeout=5) as response_obs:
                            obs_data = json.loads(response_obs.read().decode('utf-8'))
                            obs_props = obs_data.get('properties', {})
                            
                            text_desc = obs_props.get('textDescription', '')
                            celsius = obs_props.get('temperature', {}).get('value')
                            
                            # Fallback value parsing if text descriptions loop back empty
                            if not text_desc:
                                text_desc = "Clear"
                                
                            if celsius is not None:
                                fahrenheit = round((celsius * 9/5) + 32)
                                short_desc = text_desc.split(' and ')[0].split(' then ')[0].strip()
                                current_emoji = self._get_weather_emoji(short_desc)
                                current_condition = f" — Currently: {fahrenheit}°F, {short_desc} {current_emoji}"
            except Exception as obs_err:
                # Log tracing block to catch local hardware tracking variations without killing output lines
                self.log().warning(f"Observation fallback caught: {str(obs_err)}")

            # 4. Fetch the 12-hour forecast timeline array
            req_forecast = urllib.request.Request(forecast_url, headers=self.headers)
            with urllib.request.urlopen(req_forecast, timeout=5) as response:
                forecast_data = json.loads(response.read().decode('utf-8'))
                forecast_props = forecast_data.get('properties', {})

            periods = forecast_props.get('periods', [])
            if not periods:
                self.sendMessage(server, user, message, "❌ <b>Error:</b> Missing complete atmospheric metrics.")
                return

            # Build exact output block string array layout matching specification request bounds
            html = [f"🌤️ <b>Weather Forecast for {geo['city']}, {geo['state']} ({zipcode}){current_condition}</b><br/>"]

            for period in periods[:2]:
                name = period.get('name', 'Forecast')
                temp = period.get('temperature', '--')
                unit = period.get('temperatureUnit', 'F')
                wind = period.get('windSpeed', '--')
                direction = period.get('windDirection', '')
                short_forecast = period.get('shortForecast', '')
                detailed = period.get('detailedForecast', '')

                period_emoji = self._get_weather_emoji(short_forecast)

                html.append(f"<br/><b>{name}</b>: {temp}°{unit} | Wind: {wind} {direction} {period_emoji}")
                html.append(f"<br/>{detailed}")

            self.sendMessage(server, user, message, "".join(html))
                
        except Exception as e:
            self.log().error(f"Weather module structural processing fault: {str(e)}")
            self.sendMessage(server, user, message, "❌ <b>Error:</b> Could not process active weather matrix data.")

    def userConnected(self, server, state, context=None): pass
    def userDisconnected(self, server, state, context=None): pass
    def userStateChanged(self, server, state, context=None): pass
    def channelCreated(self, server, state, context=None): pass
    def channelRemoved(self, server, state, context=None): pass
    def channelStateChanged(self, server, state, context=None): pass
