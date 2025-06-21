tell application "Spotify"
    activate
    try
        set trackList to search "Yellow Coldplay"
        if trackList is not {} then
            play track (item 1 of trackList)
        else
            display dialog "No matching track found."
        end if
    on error errMsg
        display dialog "AppleScript error: " & errMsg
    end try
end tell

