# Android APK

This project is packaged as an Android WebView client for the deployed FastAPI dashboard.

Alpaca API credentials remain on the backend and must never be placed in the Android application.

## Build

Open:

**GitHub → Actions → Build Android APK → Run workflow**

Optionally enter the deployed dashboard URL, such as:

```text
https://your-render-service.onrender.com
```

After the workflow finishes, download the artifact:

```text
alpaca-dashboard-debug-apk
```

The APK file is:

```text
app-debug.apk
```

## Local build

Install:

- JDK 17
- Android SDK 35
- Gradle 8.7

Then run:

```bash
gradle assembleDebug \
  -PDASHBOARD_URL=https://your-dashboard.example.com
```

The APK will be generated at:

```text
app/build/outputs/apk/debug/app-debug.apk
```

This is an unsigned debug APK. A production release requires Android signing configuration.

Keep the backend safety settings enabled until the trading application has been independently reviewed:

```env
ENABLE_LIVE_ORDERS=false
DRY_RUN=true
EMERGENCY_STOP=true
```