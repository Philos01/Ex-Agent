---
name: amap-weather
description: |
  Query real-time weather and 4-day forecasts via Amap (高德) Weather API for Chinese cities.
  
  Use when: user asks about current weather, temperature, or forecast in any Chinese city. User asks if it will rain/snow tomorrow or in the coming days. User mentions weather-related keywords like 天气, 气温, 下雨, 刮风, 雾霾, 湿度. User asks about outdoor activity feasibility related to weather conditions. User asks about weather in a specific Chinese location by name.
  
  Do NOT use when: user asks about weather outside China (Amap only covers Chinese locations). User asks about climate or long-term weather trends (not real-time/forecast data). User asks about non-weather information.
input_parameters:
  city:
    type: string
    required: true
    description: Chinese city name extracted from the user's question (e.g., 北京, 上海, 宁波)
---

# Amap Weather (高德天气)

## Prerequisites

- `AMAP_API_KEY`: Set via environment variable (see `.env.example`). Never hardcode API keys in source files.
- Apply at https://lbs.amap.com → 控制台 → 应用管理 → 创建应用 → 添加 Key (Web服务类型)

## Quick Usage

Run the bundled script:

```bash
# Real-time weather (实况)
python3 scripts/amap_weather.py 北京

# 4-day forecast (预报)
python3 scripts/amap_weather.py 杭州 --forecast

# By adcode (区县级精度)
python3 scripts/amap_weather.py 110108 --forecast   # 海淀区

# Raw JSON output
python3 scripts/amap_weather.py 上海 --json
```

The script accepts city names (中文) or 6-digit adcodes. It has a built-in lookup table for 40+ major cities. For districts or less common cities, use adcodes directly.

## Direct API Call (without script)

```bash
# Real-time
curl -s "https://restapi.amap.com/v3/weather/weatherInfo?key=${AMAP_API_KEY}&city=110000&extensions=base"

# Forecast
curl -s "https://restapi.amap.com/v3/weather/weatherInfo?key=${AMAP_API_KEY}&city=110000&extensions=all"
```

Parse the JSON: `lives[0]` for real-time, `forecasts[0].casts[]` for forecast (4 days).

## Key Details

- **extensions=base** → real-time → `lives[]` (temperature, weather, humidity, wind)
- **extensions=all** → forecast → `forecasts[].casts[]` (4 days, day/night split)
- adcode 6-digit code required (not city name in API). Script handles name→adcode mapping.
- Updates: real-time hourly, forecast at ~8:00/11:00/18:00 CST
- Free quota: 300k calls/day

## Formatting Output

When presenting weather to users:
- Use weather emoji (☀️晴 ⛅多云 🌧雨 ❄️雪 🌫雾 😷霾)
- Temperature in °C
- Include wind and humidity for real-time
- For forecast, show day/night separately with high/low temps

## API Reference

For complete field definitions, error codes, and adcode list: see [references/api-docs.md](references/api-docs.md).
