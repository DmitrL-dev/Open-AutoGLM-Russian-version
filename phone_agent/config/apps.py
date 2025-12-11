"""App name to package name mapping for supported applications."""

APP_PACKAGES: dict[str, str] = {
    # System
    "Settings": "com.android.settings",
    "Clock": "com.android.deskclock",
    "Contacts": "com.android.contacts",
    "Files": "com.android.fileexplorer",
    "File Manager": "com.android.fileexplorer",
    "AudioRecorder": "com.android.soundrecorder",
    # Browser
    "Chrome": "com.android.chrome",
    "Google Chrome": "com.android.chrome",
    # Google Apps
    "Gmail": "com.google.android.gm",
    "Google Mail": "com.google.android.gm",
    "Google Files": "com.google.android.apps.nbu.files",
    "Google Calendar": "com.google.android.calendar",
    "Google Chat": "com.google.android.apps.dynamite",
    "Google Clock": "com.google.android.deskclock",
    "Google Contacts": "com.google.android.contacts",
    "Google Docs": "com.google.android.apps.docs.editors.docs",
    "Google Drive": "com.google.android.apps.docs",
    "Google Fit": "com.google.android.apps.fitness",
    "Google Keep": "com.google.android.keep",
    "Google Maps": "com.google.android.apps.maps",
    "Google Play Books": "com.google.android.apps.books",
    "Google Play Store": "com.android.vending",
    "Google Slides": "com.google.android.apps.docs.editors.slides",
    "Google Tasks": "com.google.android.apps.tasks",
    # Social & Messaging
    "Telegram": "org.telegram.messenger",
    "WhatsApp": "com.whatsapp",
    "WeChat": "com.tencent.mm",
    "Twitter": "com.twitter.android",
    "X": "com.twitter.android",
    "Reddit": "com.reddit.frontpage",
    "Quora": "com.quora.android",
    # Video & Entertainment
    "TikTok": "com.zhiliaoapp.musically",
    "VLC": "org.videolan.vlc",
    # Travel & Booking
    "Booking": "com.booking",
    "Booking.com": "com.booking",
    "Expedia": "com.expedia.bookings",
    # Shopping
    "Temu": "com.einnovation.temu",
    # Learning
    "Duolingo": "com.duolingo",
    # Maps & Navigation
    "OsmAnd": "net.osmand",
    # Productivity
    "Joplin": "net.cozic.joplin",
    # Music
    "RetroMusic": "code.name.monkey.retromusic",
    "PiMusicPlayer": "com.Project100Pi.themusicplayer",
    # Food
    "McDonald's": "com.mcdonalds.app",
    # Finance
    "Bluecoins": "com.rammigsoftware.bluecoins",
    # Health
    "Broccoli": "com.flauschcode.broccoli",
}


def get_package_name(app_name: str) -> str | None:
    """
    Get the package name for an app.

    Args:
        app_name: The display name of the app.

    Returns:
        The Android package name, or None if not found.
    """
    return APP_PACKAGES.get(app_name)


def get_app_name(package_name: str) -> str | None:
    """
    Get the app name from a package name.

    Args:
        package_name: The Android package name.

    Returns:
        The display name of the app, or None if not found.
    """
    for name, package in APP_PACKAGES.items():
        if package == package_name:
            return name
    return None


def list_supported_apps() -> list[str]:
    """
    Get a list of all supported app names.

    Returns:
        List of app names.
    """
    return list(APP_PACKAGES.keys())
